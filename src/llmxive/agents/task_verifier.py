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
from typing import Any

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


# A task line in tasks.md: ``- [ ] T001 [P?] [US1?] desc with path``. group(1) is
# the bullet+space prefix, group(2) the mark, group(3) the rest (id + desc).
_TASK_LINE_RE = re.compile(r"^(\s*-\s*)\[([ xX~])\](\s.*)$")
#: A task the implementer keeps failing verification is, after this many
#: consecutive rejections, ACCEPTED with a logged warning — the downstream LLM
#: review panel is the final backstop, and an unbreakable redo loop would
#: otherwise wedge the project forever at in_progress.
REJECT_CAP = 3
#: Max verifier LLM calls per tick (bounds cost; the rest verify on later ticks).
DEFAULT_VERIFY_CAP = 6


#: Annotations the claims layer RE-STAMPS on every tick, minting a FRESH id each pass
#: (``[UNRESOLVED-CLAIM: c_a1b2 — status=not_enough_info]``). They are not identity.
_VOLATILE_MARK_RE = re.compile(r"\s*\[(?:UNRESOLVED-CLAIM|UNVERIFIED):[^\]]*\]")
#: The leading speckit task id — ``T009``, ``T005C``, ``PT005C`` — a task's TRUE identity.
_TASK_ID_RE = re.compile(r"^\*{0,2}([A-Za-z]{1,4}\d+[A-Za-z0-9]*)\b")


def _task_key(rest: str) -> str:
    """Stable identity of a task line: its speckit task id (mark-independent).

    MUST NOT depend on the line's prose. The claims layer re-annotates tasks.md every
    tick with freshly-minted ``[UNRESOLVED-CLAIM: …]`` ids, so a text-derived key
    changed on every pass — which silently defeated BOTH loop guards: the
    ``already_verified`` snapshot stopped matching settled ``[X]`` work (re-judged,
    then un-checked back to ``[ ]``), and ``reject_counts`` never accumulated, so
    REJECT_CAP never fired. That made the redo loop unbreakable and no project could
    ever drain in_progress. Falls back to claim-marker-stripped prose for the rare
    id-less task line, so identity is stable under re-annotation either way."""
    body = rest.strip()
    m = _TASK_ID_RE.match(body)
    if m:
        return m.group(1)
    return _VOLATILE_MARK_RE.sub("", body).strip()


def claimed_done_keys(tasks_text: str) -> set[str]:
    """Keys of tasks currently marked ``[X]`` (already verified-accepted)."""
    out: set[str] = set()
    for line in tasks_text.splitlines():
        m = _TASK_LINE_RE.match(line)
        if m and m.group(2) in ("x", "X"):
            out.add(_task_key(m.group(3)))
    return out


def run_verification_pass(
    project_dir: Path,
    tasks_path: Path,
    *,
    already_verified: set[str],
    spec_context: str = "",
    model: str = "openai.gpt-oss-120b",
    default_backend: str = "dartmouth",
    fallback_backends: tuple[str, ...] = ("local",),
    notes_path: Path,
    state_path: Path,
    cap: int = DEFAULT_VERIFY_CAP,
) -> dict[str, Any]:
    """Independently verify each newly-claimed (``[X]`` not in ``already_verified``)
    or previously-deferred (``[~]``) task in ``tasks_path``, rewriting its mark:

      - COMPLETE   → ``[X]`` (truly done),
      - INCOMPLETE → ``[ ]`` (implementer REDOES it) + a note in ``notes_path``;
        after ``REJECT_CAP`` rejections the task is accepted (``[X]``) with a log,
      - DEFER      → ``[~]`` (under review; re-verified next tick, NOT redone).

    Returns a summary dict ``{accepted, rejected:[(key,reason)], deferred:[key]}``.
    Bounded to ``cap`` LLM calls per tick. Pure file IO + the injected
    :func:`verify_task`; safe to call once per implement-batch."""
    import yaml

    text = tasks_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    try:
        reject_counts = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        reject_counts = {}
    if not isinstance(reject_counts, dict):
        reject_counts = {}

    accepted = 0
    rejected: list[tuple[str, str]] = []
    deferred: list[str] = []
    budget = cap
    for i, line in enumerate(lines):
        m = _TASK_LINE_RE.match(line)
        if not m:
            continue
        mark, rest = m.group(2), m.group(3)
        key = _task_key(rest)
        newly_claimed = mark in ("x", "X") and key not in already_verified
        under_review = mark == "~"
        if not (newly_claimed or under_review):
            continue
        if budget <= 0:
            # Over the per-tick LLM cap → DEFER to a later tick. Mark ``[~]`` so an
            # unverified ``[X]`` does not silently escape verification (next tick's
            # snapshot would otherwise treat it as already-accepted).
            if mark != "~":
                lines[i] = f"{m.group(1)}[~]{rest}"
            deferred.append(key)
            continue
        budget -= 1
        verdict = verify_task(
            task_text=rest.strip(),
            evidence=gather_evidence(project_dir, rest),
            spec_context=spec_context,
            model=model,
            default_backend=default_backend,
            fallback_backends=fallback_backends,
        )
        if verdict.complete is True:
            lines[i] = f"{m.group(1)}[X]{rest}"
            accepted += 1
            reject_counts.pop(key, None)
        elif verdict.complete is False:
            count = int(reject_counts.get(key, 0)) + 1
            reject_counts[key] = count
            if count >= REJECT_CAP:
                lines[i] = f"{m.group(1)}[X]{rest}"
                reject_counts.pop(key, None)
                LOGGER.warning(
                    "[task-verifier] %r rejected %dx — accepting to avoid an "
                    "unbreakable redo loop (review panel is the final backstop)",
                    key, count,
                )
            else:
                lines[i] = f"{m.group(1)}[ ]{rest}"
                rejected.append((key, verdict.reason))
        else:  # deferred (backend outage / unparseable)
            lines[i] = f"{m.group(1)}[~]{rest}"
            deferred.append(key)

    new_text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    if new_text != text:
        tasks_path.write_text(new_text, encoding="utf-8")

    # Drop reject counts for tasks that no longer exist in tasks.md. This also
    # self-heals the legacy text-keyed entries stranded by the identity fix above
    # (projects had accumulated ~205 dead keys for ~132 real tasks), so a task's
    # count reflects ONLY its own consecutive rejections and REJECT_CAP can fire.
    live_keys = {
        _task_key(m.group(3))
        for m in (_TASK_LINE_RE.match(line) for line in lines)
        if m
    }
    reject_counts = {k: v for k, v in reject_counts.items() if k in live_keys}

    state_path.parent.mkdir(parents=True, exist_ok=True)
    if reject_counts:
        state_path.write_text(yaml.safe_dump(reject_counts, sort_keys=True), encoding="utf-8")
    else:
        state_path.unlink(missing_ok=True)

    _write_notes(notes_path, rejected)
    return {"accepted": accepted, "rejected": rejected, "deferred": deferred}


def _write_notes(notes_path: Path, rejected: list[tuple[str, str]]) -> None:
    """Rewrite the implementer-facing rejection note (or remove it when empty)."""
    if not rejected:
        notes_path.unlink(missing_ok=True)
        return
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    out = [
        "# Tasks an independent verifier REJECTED (redo these)",
        "",
        "A separate model checked the artifacts you produced for the tasks below "
        "and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the "
        "evidence genuinely satisfies the requirement (produce the real artifact, "
        "fix the content, remove any placeholder/fabricated stand-in). Do NOT just "
        "re-check the box without changing the work.",
        "",
    ]
    for key, reason in rejected:
        out.append(f"- **{key}** — {reason.strip()}")
    notes_path.write_text("\n".join(out) + "\n", encoding="utf-8")


__all__ = [
    "DEFAULT_VERIFY_CAP",
    "REJECT_CAP",
    "VERIFIER_TEMPERATURE",
    "TaskVerdict",
    "claimed_done_keys",
    "gather_evidence",
    "run_verification_pass",
    "verify_task",
]
