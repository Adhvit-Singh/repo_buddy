import pytest

from app.services import llm_router
from app.services.llm_router import _extract_json, _is_retryable


@pytest.mark.parametrize(
    "text, expected",
    [
        ('{"a": 1}', {"a": 1}),
        ('```json\n{"a": 1}\n```', {"a": 1}),
        ('Sure! Here you go:\n{"a": {"b": [1, 2]}}\nHope that helps.', {"a": {"b": [1, 2]}}),
        ('[{"title": "x"}]', [{"title": "x"}]),
        ("not json at all", None),
        ("", None),
        (None, None),
    ],
)
def test_extract_json(text, expected):
    assert _extract_json(text) == expected


@pytest.mark.parametrize(
    "message, retry",
    [
        ("429 RESOURCE_EXHAUSTED quota exceeded", True),
        ("503 UNAVAILABLE. This model is currently experiencing high demand", True),
        ("504 DEADLINE_EXCEEDED", True),
        ("Read timed out", True),
        ("404 NOT_FOUND model retired", False),
        ("400 INVALID_ARGUMENT", False),
    ],
)
def test_retryable_errors(message, retry):
    assert _is_retryable(Exception(message)) is retry


def test_no_keys_means_no_provider_and_no_answer():
    assert llm_router.active_provider() == "none"
    assert llm_router.llm_json("{}") is None
    assert llm_router.llm_text("hi") is None


def test_gemini_falls_through_models_until_one_answers(monkeypatch):
    calls = []

    class FakeModels:
        def generate_content(self, model, contents, config=None):
            calls.append(model)
            if model == "retired-model":
                raise Exception("404 NOT_FOUND")
            return type("R", (), {"text": '{"ok": true}'})()

    class FakeClient:
        def __init__(self, **kw):
            self.models = FakeModels()

    import google.genai as genai

    monkeypatch.setattr(genai, "Client", FakeClient)
    monkeypatch.setattr(llm_router, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(llm_router, "GEMINI_MODELS", ["retired-model", "good-model"])

    assert llm_router.llm_json("prompt") == {"ok": True}
    assert calls == ["retired-model", "good-model"]  # 404 is not retried, just skipped


def test_gemini_retries_busy_model(monkeypatch):
    attempts = {"n": 0}

    class FakeModels:
        def generate_content(self, model, contents, config=None):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise Exception("503 UNAVAILABLE high demand")
            return type("R", (), {"text": "hello"})()

    class FakeClient:
        def __init__(self, **kw):
            self.models = FakeModels()

    import google.genai as genai

    monkeypatch.setattr(genai, "Client", FakeClient)
    monkeypatch.setattr(llm_router, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(llm_router, "GEMINI_MODELS", ["only-model"])
    monkeypatch.setattr(llm_router, "_RETRY_DELAYS", (0, 0))

    assert llm_router.llm_text("prompt") == "hello"
    assert attempts["n"] == 2
