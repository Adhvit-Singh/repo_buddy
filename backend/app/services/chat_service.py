"""
repo_buddy — AI Sidekick chat

Answers a user's question about a repo using the scan report as context.
"""
import json

from app.services.llm_router import active_provider, llm_text

MAX_CONTEXT_CHARS = 30_000


def chat_with_codebase(question: str, report: dict) -> str:
    if not question or not question.strip():
        return "Please ask a question about your app — for example, 'Is my login secure?' or 'What database am I using?'"

    if active_provider() == "none":
        return "AI chat is unavailable: no GEMINI_API_KEY is configured on the server."

    if not report:
        return "I don't have any analysis data yet. Run a scan first, then ask me about the results."

    context = json.dumps(report, indent=2)
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n... [truncated]"

    prompt = f"""You are repo_buddy's AI Sidekick — a friendly, concise assistant that helps
non-technical builders understand their codebase.

Here is the analysis report for their repository:
{context}

The user asks: {question}

Answer in 2-3 sentences maximum, in simple non-technical language. Be direct.
Only use facts from the report; if the report doesn't cover it, say so."""

    answer = llm_text(prompt, pass_type="tick", max_tokens=512)
    return answer or "The AI service is busy or rate-limited right now. Please try again in a minute."
