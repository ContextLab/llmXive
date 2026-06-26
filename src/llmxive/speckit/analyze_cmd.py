"""/speckit.analyze driver — used inside the Tasker's resolve loop (T052).

There is no dedicated mechanical script for /speckit.analyze in
upstream Spec Kit; it is purely an LLM cross-artifact consistency
check. This module supplies the analyze invocation as a function (not
a SlashCommandAgent) so the Tasker can call it inline within its
resolve loop.
"""

from __future__ import annotations

import re
from pathlib import Path

from llmxive.agents.prompts import render_prompt
from llmxive.backends.base import ChatMessage
from llmxive.backends.router import chat_with_fallback
from llmxive.config import repo_root as _repo_root
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
    repo = repo_root or _repo_root()
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


# Findings are emitted as `(severity: CRITICAL|HIGH|MEDIUM|LOW) ...` bullets
# (agents/prompts/analyze.md). CRITICAL/HIGH = a real cross-artifact defect
# (missing coverage, contradiction, scope creep, constitution violation);
# MEDIUM/LOW = doc-level polish.
_BLOCKING_SEVERITY_RE = re.compile(r"severity\s*[:=]\s*(?:CRITICAL|HIGH)\b", re.IGNORECASE)
_ANY_SEVERITY_RE = re.compile(
    r"severity\s*[:=]\s*(?:CRITICAL|HIGH|MEDIUM|LOW)\b", re.IGNORECASE
)


def analyze_advance_ok(report: str) -> bool:
    """Two-tier convergence for the doc-authoring **tasks** stage (Constitution
    1.2.0).

    The analyze step is an LLM critic that almost never emits a literal
    ``CLEAN`` — it reliably finds *some* minor nit — so gating convergence on
    ``is_clean`` alone stalls EVERY project at the tasks gate forever, even with
    a genuinely good tasks.md. A doc-authoring stage may ADVANCE on writing-level
    residue: converge when the report is ``CLEAN`` **or** carries only MEDIUM/LOW
    findings. A CRITICAL/HIGH cross-artifact issue (a real coverage gap,
    contradiction, scope creep, or constitution violation) ALWAYS kicks back —
    the science bar is never relaxed. Mirrors ``engine.py``'s two-tier bar (doc
    stages advance when ``worst_rank <= WRITING``); the strict zero-concern gate
    remains ``research_review``.

    A non-CLEAN report with NO parseable ``severity:`` bullet is malformed — kick
    back (return False) rather than advance on an uninterpretable critique.
    """
    if is_clean(report):
        return True
    if _BLOCKING_SEVERITY_RE.search(report):
        return False
    return _ANY_SEVERITY_RE.search(report) is not None


__all__ = [
    "ANALYZE_SYSTEM_PROMPT_PATH",
    "ANALYZE_SYSTEM_PROMPT_PATHS",
    "analyze_advance_ok",
    "is_clean",
    "run_analyze",
]
