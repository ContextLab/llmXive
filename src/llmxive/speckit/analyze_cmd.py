"""/speckit.analyze driver — used inside the Tasker's resolve loop (T052).

There is no dedicated mechanical script for /speckit.analyze in
upstream Spec Kit; it is purely an LLM cross-artifact consistency
check. This module supplies the analyze invocation as a function (not
a SlashCommandAgent) so the Tasker can call it inline within its
resolve loop.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage
from llmxive.backends.router import chat_with_fallback
from llmxive.types import BackendName


ANALYZE_SYSTEM_PROMPT_PATH = "agents/prompts/tasker.md"  # Tasker prompt covers analyze in Mode B


def run_analyze(
    *,
    spec_text: str,
    plan_text: str,
    tasks_text: str,
    default_backend: BackendName,
    fallback_backends: list[BackendName],
    default_model: str,
    repo_root: Path | None = None,
) -> str:
    """Issue an analyze pass over the three artifacts; return raw report text.

    The Tasker's prompt (Mode B) accepts the analyze report and the
    artifacts together to produce patches; here we synthesize the
    report by asking the model to act as analyze.
    """
    repo = repo_root or Path(__file__).resolve().parent.parent.parent.parent
    system = (
        "You are the Spec Kit /speckit.analyze step. "
        "Examine the three artifacts (spec.md, plan.md, tasks.md) and produce "
        "a bulleted list of cross-artifact issues. Each bullet must include: "
        "(severity: CRITICAL|HIGH|MEDIUM|LOW), (file:section), and a one-sentence summary. "
        "If no issues are found, return the literal string 'CLEAN' on its own line."
    )
    user = (
        f"# spec.md\n\n{spec_text}\n\n"
        f"# plan.md\n\n{plan_text}\n\n"
        f"# tasks.md\n\n{tasks_text}\n\n"
        "Now produce the analyze report."
    )
    response = chat_with_fallback(
        [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)],
        default_backend=default_backend.value,
        fallback_backends=[b.value for b in fallback_backends],
        model=default_model,
    )
    return response.text.strip()


def is_clean(report: str) -> bool:
    return report.strip().upper().startswith("CLEAN")


__all__ = ["run_analyze", "is_clean"]
