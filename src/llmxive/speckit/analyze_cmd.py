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

# Spec 015 T031 (discrepancy #4) + FR-030: the analyze prompts are now real prompt
# files that ARE used (the constant is no longer dead) and paper analyze uses a
# paper-appropriate prompt rather than reusing the research tasker.md.
ANALYZE_SYSTEM_PROMPT_PATHS: dict[str, str] = {
    "research": "agents/prompts/analyze.md",
    "paper": "agents/prompts/paper_analyze.md",
}
# Back-compat: legacy callers may reference the bare name. Points at the research
# variant — paper callers pass kind="paper".
ANALYZE_SYSTEM_PROMPT_PATH: str = ANALYZE_SYSTEM_PROMPT_PATHS["research"]


def run_analyze(
    *,
    spec_text: str,
    plan_text: str,
    tasks_text: str,
    default_backend: BackendName,
    fallback_backends: list[BackendName],
    default_model: str,
    repo_root: Path | None = None,
    project_dir: Path | None = None,
    kind: str = "research",
    constitution_text: str | None = None,
) -> str:
    """Issue an analyze pass over the three artifacts; return raw report text.

    ``kind`` selects the analyze prompt (``"research"`` or ``"paper"``).
    ``constitution_text``, when provided, is included as a panel input so the
    analyzer can flag constitution violations (FR-030).
    """
    repo = repo_root or Path(__file__).resolve().parent.parent.parent.parent
    if kind not in ANALYZE_SYSTEM_PROMPT_PATHS:
        raise ValueError(
            f"run_analyze: unknown kind {kind!r}; "
            f"expected one of {sorted(ANALYZE_SYSTEM_PROMPT_PATHS)}"
        )
    system = render_prompt(ANALYZE_SYSTEM_PROMPT_PATHS[kind], {}, repo_root=repo)

    # Spec 011 / FR-013: inject recent personality + reviewer comments
    # so the analyzer's flagged issues reflect existing feedback. The
    # caller passes project_dir (optional, kept None for legacy callsites).
    comments_block = ""
    if project_dir is not None:
        from llmxive.speckit._comments_context import render_recent_comments_block
        comments_block = render_recent_comments_block(project_dir)

    parts: list[str] = []
    if constitution_text:
        parts.append(f"# constitution.md\n\n{constitution_text}")
    parts.extend([
        f"# spec.md\n\n{spec_text}",
        f"# plan.md\n\n{plan_text}",
        f"# tasks.md\n\n{tasks_text}",
    ])
    if comments_block:
        parts.append(comments_block)
    parts.append("Now produce the analyze report.")
    user = "\n\n".join(parts)
    response = chat_with_fallback(
        [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)],
        default_backend=default_backend.value,
        fallback_backends=[b.value for b in fallback_backends],
        model=default_model,
    )
    return response.text.strip()


def is_clean(report: str) -> bool:
    return report.strip().upper().startswith("CLEAN")


__all__ = [
    "ANALYZE_SYSTEM_PROMPT_PATH",
    "ANALYZE_SYSTEM_PROMPT_PATHS",
    "is_clean",
    "run_analyze",
]
