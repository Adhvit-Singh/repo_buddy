"""
repo_buddy — LLM Router

Single entry point for every LLM call in the backend. Each service asks for
JSON (`llm_json`) or plain text (`llm_text`) and the router decides which
provider/model answers:

  1. Anthropic Claude, if ANTHROPIC_API_KEY is set (optional).
  2. Google Gemini, trying each model in GEMINI_MODELS in order.

Model names live in config (env-overridable), so when a provider retires a
model the fix is an env change, not a code change. Callers that get `None`
back must surface an error — never substitute fake data.
"""
import json
import re
import time
from typing import Any, Literal, Optional

from app.config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL_DEEP,
    ANTHROPIC_MODEL_FAST,
    GEMINI_API_KEY,
    GEMINI_MODELS,
    LLM_TIMEOUT_SECONDS,
)

PassType = Literal["deep", "headline", "tick"]

_ANTHROPIC_MODELS: dict[PassType, str] = {
    "deep": ANTHROPIC_MODEL_DEEP,
    "headline": ANTHROPIC_MODEL_DEEP,
    "tick": ANTHROPIC_MODEL_FAST,
}

# Anthropic has no JSON response mode, so the format is enforced by
# instruction and parsed defensively.
_JSON_SYSTEM = (
    "Respond with a single valid JSON value and nothing else. "
    "No markdown fences. No prose before or after."
)


def _extract_json(text: Optional[str]) -> Optional[Any]:
    """Parse strict JSON, or pull the first {...} / [...] block out of prose."""
    if not text:
        return None
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None


_RETRY_DELAYS = (3, 8)  # seconds to wait before 2nd and 3rd attempt on one model


def _is_retryable(err: Exception) -> bool:
    """Rate limits, overload and timeouts are transient — worth a retry."""
    s = str(err).lower()
    return any(k in s for k in ("429", "503", "504", "resource_exhausted", "unavailable",
                                "deadline", "timed out", "timeout", "high demand"))


def _try_anthropic(pass_type: PassType, prompt: str, max_tokens: int, want_json: bool) -> Optional[str]:
    if not ANTHROPIC_API_KEY:
        return None
    try:
        from anthropic import Anthropic
    except ImportError:
        return None

    model = _ANTHROPIC_MODELS[pass_type]
    try:
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        kwargs = {"system": _JSON_SYSTEM} if want_json else {}
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        text = response.content[0].text if response.content else ""
        print(f"INFO: LLM pass={pass_type} answered by {model}")
        return text
    except Exception as e:
        print(f"WARN: Anthropic {model} call failed: {e}")
        return None


def _try_gemini(prompt: str, want_json: bool) -> Optional[str]:
    if not GEMINI_API_KEY:
        return None
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=LLM_TIMEOUT_SECONDS * 1000),
    )
    config = types.GenerateContentConfig(response_mime_type="application/json") if want_json else None
    last_err: Optional[Exception] = None
    for model_name in GEMINI_MODELS:
        for attempt in range(len(_RETRY_DELAYS) + 1):
            try:
                response = client.models.generate_content(
                    model=model_name, contents=prompt, config=config
                )
                if response.text:
                    print(f"INFO: LLM answered by {model_name}")
                    return response.text
                break
            except Exception as e:
                last_err = e
                if _is_retryable(e) and attempt < len(_RETRY_DELAYS):
                    delay = _RETRY_DELAYS[attempt]
                    print(f"WARN: {model_name} busy ({str(e)[:60]}), retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                print(f"WARN: Gemini {model_name} failed: {str(e)[:200]}")
                break
    print(f"WARN: All Gemini models failed (last error: {last_err}).")
    return None


def llm_json(prompt: str, pass_type: PassType = "deep", max_tokens: int = 8192) -> Optional[Any]:
    """Return parsed JSON (dict or list) from the first provider that answers, else None."""
    text = _try_anthropic(pass_type, prompt, max_tokens, want_json=True)
    parsed = _extract_json(text)
    if parsed is not None:
        return parsed
    return _extract_json(_try_gemini(prompt, want_json=True))


def llm_text(prompt: str, pass_type: PassType = "tick", max_tokens: int = 1024) -> Optional[str]:
    """Return plain text from the first provider that answers, else None."""
    text = _try_anthropic(pass_type, prompt, max_tokens, want_json=False)
    if text:
        return text.strip()
    text = _try_gemini(prompt, want_json=False)
    return text.strip() if text else None


def active_provider() -> str:
    """Which provider would handle a request right now ("none" = no key set)."""
    if ANTHROPIC_API_KEY:
        return "anthropic"
    if GEMINI_API_KEY:
        return "gemini"
    return "none"
