"""Independent task-completion verifier (spec-contract consistency).

The speckit implementer checks off a task as soon as it BELIEVES it did the work.
That self-report is exactly how a project's implementation can drift from its spec
(PROJ-604: tasks claimed a benchmark was produced; the artifacts were random
numbers). This module adds an INDEPENDENT check — a SEPARATE LLM call, outside the
implementer's prompt/session — that looks at the task's REQUIREMENTS and the ACTUAL
artifacts/evidence and decides whether the work is genuinely done.

Flow (wired in ``pipeline.graph`` run_one_step, after the implement batch):
  - implementer marks a task ``- [X]`` (claims done),
  - the verifier judges it: COMPLETE → keep ``- [X]``; INCOMPLETE → mark
    ``- [~]`` (under review) and append the reason to a notes file the NEXT
    implementer session reads as context,
  - a transient backend failure DEFERS (``- [~]``) — never silently accepts —
    so a task is checked off complete ONLY on a real COMPLETE verdict.

Modeled on ``librarian.relevance_judge`` (a deterministic, temp-0 LLM judge), but
fails CLOSED (defer), not open: an unverifiable task must not count as done.
"""

from __future__ import annotations

import dataclasses
import logging
import re
from pathlib import Path

from llmxive.backends.base import ChatMessage
from llmxive.backends.router import REASONING_MAX_TOKENS, chat_with_fallback

LOGGER = logging.getLogger(__name__)

VERIFIER_TEMPERATURE = 0.0

_SYSTEM_PROMPT = """\
You are an INDEPENDENT task-completion verifier in an automated research pipeline.
A different agent (the implementer) has CLAIMED it completed a task. Your job is to
decide — skeptically, from the ACTUAL evidence — whether the work is GENUINELY done
and matches the task's stated requirements. Do NOT trust the claim; trust the
artifacts.

Return VERDICT: COMPLETE only if ALL hold:
  - the artifact(s) the task requires actually EXIST and are non-empty;
  - their CONTENT matches what the task asked for (the right kind of output, the
    right columns/fields/behavior, the real quantity — not a placeholder, stub,
    `TODO`, `NotImplementedError`, or fabricated/random/"simulated" stand-in);
  - the work addresses the task's REQUIREMENT, not a different, easier thing.

Return VERDICT: INCOMPLETE if the required artifact is missing, empty, a
stub/placeholder, fabricated (e.g. metrics drawn from random numbers, or synthetic
data where real data was required), or simply does not satisfy what the task asked
for.

Output the FIRST line as EXACTLY one of:
VERDICT: COMPLETE
VERDICT: INCOMPLETE
Then 1-3 sentences naming the evidence you checked. If INCOMPLETE, state CONCRETELY
what is missing or wrong, so the next implementer can fix it.
"""

# File paths a task line references (the evidence to inspect): code/data/figures/
# results/outputs rooted, with a real extension.
_PATH_RE = re.compile(r"\b((?:code|data|figures|results|outputs)/[\w./-]+\.\w+)")
_MAX_EVIDENCE_FILES = 6
_MAX_BYTES_PER_FILE = 3000


@dataclasses.dataclass(frozen=True)
class TaskVerdict:
    """One verification result. ``complete is None`` = DEFERRED (could not verify
    this tick, e.g. a backend outage) — treat as under-review, retry later; never
    as accepted."""
    complete: bool | None
    reason: str

    @property
    def deferred(self) -> bool:
        return self.complete is None


def gather_evidence(project_dir: Path, task_text: str) -> str:
    """Collect the artifacts a task references (head of each) as evidence text."""
    paths = []
    seen: set[str] = set()
    for m in _PATH_RE.finditer(task_text):
        rel = m.group(1)
        if rel in seen:
            continue
        seen.add(rel)
        paths.append(rel)
        if len(paths) >= _MAX_EVIDENCE_FILES:
            break
    chunks: list[str] = []
    for rel in paths:
        f = project_dir / rel
        if not f.is_file():
            chunks.append(f"- `{rel}`: MISSING (file does not exist)")
            continue
        try:
            size = f.stat().st_size
            head = f.read_text(encoding="utf-8", errors="ignore")[:_MAX_BYTES_PER_FILE]
        except OSError as exc:
            chunks.append(f"- `{rel}`: unreadable ({exc})")
            continue
        chunks.append(
            f"- `{rel}` ({size} bytes):\n```\n{head}\n```"
            + ("" if size <= _MAX_BYTES_PER_FILE else "\n…(truncated)")
        )
    if not chunks:
        chunks.append(
            "(the task references no code/data/figure artifact path; verify from "
            "the task description + the project context alone)"
        )
    return "\n".join(chunks)


def verify_task(
    *,
    task_text: str,
    evidence: str,
    spec_context: str = "",
    model: str = "openai.gpt-oss-120b",
    default_backend: str = "dartmouth",
    fallback_backends: tuple[str, ...] = ("local",),
) -> TaskVerdict:
    """Independently judge whether ``task_text`` is genuinely complete given the
    ACTUAL ``evidence``. DEFERS (``complete=None``) on a backend failure so an
    unverifiable task is never wrongly accepted."""
    user = (
        "# Task the implementer claims is complete\n\n"
        f"{task_text.strip()}\n\n"
    )
    if spec_context.strip():
        user += f"# Project requirements (spec excerpt)\n\n{spec_context.strip()[:4000]}\n\n"
    user += (
        "# Actual artifacts / evidence on disk\n\n"
        f"{evidence.strip()}\n\n"
        "# Your judgment\n\n"
        "Does the evidence GENUINELY satisfy the task's requirement? Apply the "
        "system-prompt rules strictly."
    )
    try:
        response = chat_with_fallback(
            [
                ChatMessage(role="system", content=_SYSTEM_PROMPT),
                ChatMessage(role="user", content=user),
            ],
            default_backend=default_backend,
            fallback_backends=list(fallback_backends),
            model=model,
            temperature=VERIFIER_TEMPERATURE,
            max_tokens=REASONING_MAX_TOKENS,
        )
    except Exception as exc:  # transient outage → defer, do NOT accept
        LOGGER.warning("[task-verifier] backend failure: %s", exc)
        return TaskVerdict(complete=None, reason=f"(verifier unreachable: {type(exc).__name__})")
    return _parse(response.text)


def _parse(text: str) -> TaskVerdict:
    """Parse the FIRST-line verdict. An uninterpretable response DEFERS (not
    accept, not reject) — re-judged next tick."""
    if not text or not text.strip():
        return TaskVerdict(complete=None, reason="(empty verifier response)")
    cleaned = text.strip()
    first = cleaned.splitlines()[0].strip().upper()
    rest = "\n".join(cleaned.splitlines()[1:]).strip() or cleaned
    if first.startswith("VERDICT: COMPLETE") or first == "COMPLETE":
        return TaskVerdict(complete=True, reason=rest[:600])
    if first.startswith("VERDICT: INCOMPLETE") or first == "INCOMPLETE":
        return TaskVerdict(complete=False, reason=rest[:600])
    head = cleaned[:200].lower()
    if "verdict: incomplete" in head:
        return TaskVerdict(complete=False, reason=cleaned[:600])
    if "verdict: complete" in head:
        return TaskVerdict(complete=True, reason=cleaned[:600])
    return TaskVerdict(complete=None, reason=f"(unparseable verifier response) {cleaned[:200]}")


__all__ = ["TaskVerdict", "gather_evidence", "verify_task", "VERIFIER_TEMPERATURE"]
