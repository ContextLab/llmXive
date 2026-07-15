"""Independent task-completion verifier (spec-contract consistency).

The speckit implementer checks off a task as soon as it BELIEVES it did the work.
That self-report is exactly how a project's implementation can drift from its spec
(PROJ-604: tasks claimed a benchmark was produced; the artifacts were random
numbers). This module adds an INDEPENDENT check — outside the implementer's
prompt/session — that looks at the task's REQUIREMENTS and the ACTUAL
artifacts/evidence and decides whether the work is genuinely done.

Two-tier verification (issue #1139, defect D6 — throughput + fail-open fix):

  1. DETERMINISTIC-FIRST (free, no LLM). Before spending any model call, each
     claimed/under-review task is settled from FILESYSTEM STATE: a task whose
     declared artifacts all exist and validate (data outputs parse + have rows)
     is ACCEPTED ``[X]``; a production task whose declared artifacts are all
     missing/empty is REOPENED ``[ ]``. This is what drains the huge ``[~]``
     backlog cheaply — the throughput lever is deterministic draining, NOT a
     bigger LLM cap. The artifact-path detector is broadened well beyond the old
     code/data/figures/results/outputs roots (now also src/, tests/, scripts/,
     config/, and bare build/config files) so setup/config/test tasks are judged
     from STATE, not prose.
  2. SEMANTIC RESIDUE (bounded LLM). Only genuinely ambiguous tasks (no
     detectable artifact path, or a mixed/partial state) reach the single
     temp-0 LLM call in :func:`verify_task`, bounded to ``cap`` calls per tick.
     Each semantic verdict is bound to a ``(task_key, evidence_hash)`` cache so
     re-verifying an unchanged task is free and a verdict invalidates the moment
     the evidence bytes change.

Verdict → mark: COMPLETE → ``[X]``; INCOMPLETE → ``[ ]`` (implementer REDOES it)
+ a note the next session reads; DEFER (backend outage / over-cap) → ``[~]``
(under review; re-verified later, NOT redone). A task that receives ``REJECT_CAP``
consecutive INCOMPLETE verdicts is NEVER force-accepted — it is reopened ``[ ]``
AND recorded in :mod:`llmxive.state.unverifiable`, which stops the redo loop
(the recorded task is not re-judged until cleared) and signals CORE to route the
project to ``research_full_revision``. Fails CLOSED (defer), never open.
"""

from __future__ import annotations

import dataclasses
import hashlib
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

# --- Artifact-path detection (the deterministic evidence a task line references) ---
#
# Broadened well beyond the original code/data/figures/results/outputs roots so
# scaffolding / config / test tasks are judged from real files, not prose.
#: Directory-rooted artifact paths with a real dotted extension.
_ROOTED_PATH_RE = re.compile(
    r"\b((?:code|data|figures|results|outputs|src|tests?|scripts|config|configs|"
    r"notebooks|docs|assets|models|reports)/[\w./-]+\.\w+)"
)
#: Bare (optionally path-prefixed) build/config filenames a task may reference.
_CONFIG_FILE_RE = re.compile(
    r"\b((?:[\w./-]+/)?(?:pyproject\.toml|setup\.cfg|setup\.py|"
    r"requirements(?:-[\w.]+)?\.txt|environment\.ya?ml|tox\.ini|noxfile\.py|"
    r"conftest\.py|pytest\.ini|mkdocs\.ya?ml|Makefile|Dockerfile))\b"
)
#: Generic config-extension files (…toml/…cfg/…yaml/…ini) referenced under the project.
_CONFIG_EXT_RE = re.compile(r"\b((?:[\w./-]+/)?[\w-]+\.(?:toml|cfg|ya?ml|ini))\b")
#: Back-compat alias — some callers/tests reference the historical single regex; it
#: now points at the primary rooted-path pattern (the deterministic detector uses
#: the full :func:`_declared_paths` union).
_PATH_RE = _ROOTED_PATH_RE

_MAX_EVIDENCE_FILES = 6
_MAX_BYTES_PER_FILE = 3000
#: Cap bytes read when VALIDATING a data/JSON artifact (parse cheaply, not fully).
_VALIDATE_MAX_BYTES = 200_000
_DATA_EXTS = {".csv", ".tsv"}
_JSON_EXTS = {".json"}

#: A task line whose text shows the implementer was meant to PRODUCE an artifact.
#: Gate for deterministic-REJECT (a "remove/delete" task legitimately ends with the
#: artifact absent, so those are routed to the semantic verifier instead).
_PRODUCE_RE = re.compile(
    r"\b(creat\w*|writ\w*|produc\w*|generat\w*|implement\w*|add\w*|build\w*|"
    r"sav\w*|export\w*|output\w*|comput\w*|plot\w*|train\w*|populat\w*|render\w*|"
    r"serializ\w*|dump\w*|emit\w*|scaffold\w*|configur\w*|initializ\w*|set up|setup)\b",
    re.IGNORECASE,
)
_REMOVE_RE = re.compile(
    r"\b(remov\w*|delet\w*|drop\w*|deprecat\w*|clean up)\b", re.IGNORECASE
)


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


def _declared_paths(task_text: str) -> list[str]:
    """Every artifact path a task line references (rooted paths + build/config
    files), de-duplicated in first-seen order."""
    out: list[str] = []
    seen: set[str] = set()
    for rx in (_ROOTED_PATH_RE, _CONFIG_FILE_RE, _CONFIG_EXT_RE):
        for m in rx.finditer(task_text):
            rel = m.group(1)
            if rel and rel not in seen:
                seen.add(rel)
                out.append(rel)
    return out


def _artifact_valid(project_dir: Path, rel: str) -> bool:
    """True iff ``rel`` exists, is non-empty, AND (for declared data outputs) parses
    with at least one data row. Pure filesystem + stdlib parse — never an LLM."""
    import json

    f = project_dir / rel
    if not f.is_file():
        return False
    try:
        size = f.stat().st_size
    except OSError:
        return False
    if size == 0:
        return False
    ext = f.suffix.lower()
    try:
        if ext in _DATA_EXTS:
            text = f.read_text(encoding="utf-8", errors="ignore")[:_VALIDATE_MAX_BYTES]
            rows = [ln for ln in text.splitlines() if ln.strip()]
            return len(rows) >= 2  # header + >=1 data row
        if ext in _JSON_EXTS:
            if size > _VALIDATE_MAX_BYTES:
                return True  # too large to parse cheaply; non-empty is the check
            data = json.loads(f.read_text(encoding="utf-8", errors="ignore") or "null")
            if isinstance(data, (list, dict)):
                return len(data) > 0
            return data is not None
        # code / config / text / binary artifact: non-empty with real content.
        return bool(f.read_bytes()[:_VALIDATE_MAX_BYTES].strip())
    except (OSError, ValueError):
        return False  # a malformed data/JSON file is NOT valid evidence


def _has_production_intent(task_text: str) -> bool:
    return bool(_PRODUCE_RE.search(task_text)) and not _REMOVE_RE.search(task_text)


def _deterministic_verdict(project_dir: Path, task_text: str) -> tuple[str | None, str]:
    """Settle a claimed task from FILESYSTEM STATE alone — no LLM.

    Returns ``("accept", reason)`` when every declared artifact exists and
    validates, ``("reject", reason)`` when a production task's declared artifacts
    are all missing/empty/invalid, or ``(None, "")`` when the task is genuinely
    ambiguous (no detectable artifact path, or a mixed/partial state) and must go
    to the semantic verifier."""
    paths = _declared_paths(task_text)
    if not paths:
        return None, ""
    statuses = [(p, _artifact_valid(project_dir, p)) for p in paths]
    if all(valid for _, valid in statuses):
        present = ", ".join(p for p, _ in statuses)
        return "accept", f"all declared artifacts exist and validate: {present}"
    missing = [p for p, valid in statuses if not valid]
    if len(missing) == len(statuses) and _has_production_intent(task_text):
        return "reject", (
            f"declared artifact(s) missing/empty/invalid: {', '.join(missing)}"
        )
    return None, ""


def gather_evidence(project_dir: Path, task_text: str) -> str:
    """Collect the artifacts a task references (head of each) as evidence text.

    Uses the broadened :func:`_declared_paths` detector, so a setup/config/test
    task (``pyproject.toml``, ``tests/…``, ``src/…``) yields REAL file evidence
    instead of the "no artifact path" prose fallback."""
    paths = _declared_paths(task_text)[:_MAX_EVIDENCE_FILES]
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
#: A task that receives this many consecutive INCOMPLETE verdicts is NOT
#: force-accepted (that was the fail-open removed in issue #1139). It is reopened
#: ``[ ]`` AND recorded in :mod:`llmxive.state.unverifiable`, which BOTH breaks the
#: redo loop (the recorded task is not re-judged until cleared) and signals CORE to
#: route the whole project to ``research_full_revision``. Incomplete work must
#: never count as done.
REJECT_CAP = 3
#: Max verifier LLM calls per tick (bounds cost). Deterministic accepts/rejects and
#: evidence-hash cache hits are FREE and do NOT count against this — so the huge
#: ``[~]`` backlog drains without a bigger cap; only genuinely ambiguous residue
#: consumes the budget, and anything past it defers to a later tick.
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


def task_keys(tasks_text: str | list[str]) -> dict[int, str]:
    """Map line-index -> UNIQUE stable key, for every task line in ``tasks_text``.

    The bare task id is not always unique: 18% of live projects (78/433, 240 lines)
    carry DUPLICATE ids — two genuinely different tasks both numbered ``T001``, from
    merged task lists. Collapsing them would let the second inherit the first's
    ``[X]`` snapshot entry and ESCAPE independent verification, and would make them
    share a reject counter (firing REJECT_CAP early). So repeats are disambiguated
    by occurrence: ``T001``, ``T001#1``, ``T001#2``.

    Occurrence order — not prose — is the discriminator, precisely because the claims
    layer rewrites prose every tick but never reorders the list. Keys are therefore
    stable across ticks while staying unique within the file."""
    lines = tasks_text.splitlines() if isinstance(tasks_text, str) else tasks_text
    seen: dict[str, int] = {}
    out: dict[int, str] = {}
    for i, line in enumerate(lines):
        m = _TASK_LINE_RE.match(line)
        if not m:
            continue
        base = _task_key(m.group(3))
        n = seen.get(base, 0)
        seen[base] = n + 1
        out[i] = base if n == 0 else f"{base}#{n}"
    return out


def claimed_done_keys(tasks_text: str) -> set[str]:
    """Keys of tasks currently marked ``[X]`` (already verified-accepted)."""
    lines = tasks_text.splitlines()
    keys = task_keys(lines)
    out: set[str] = set()
    for i, key in keys.items():
        m = _TASK_LINE_RE.match(lines[i])
        if m and m.group(2) in ("x", "X"):
            out.add(key)
    return out


def _resolve_ids(
    project_dir: Path, project_id: str | None, repo_root: Path | None
) -> tuple[str, Path]:
    """Derive ``(project_id, repo_root)`` from ``project_dir`` when not supplied.

    graph.py calls the verifier with only ``project_dir`` (``…/projects/<id>``), so
    the project id is the dir name and the repo root is two levels up. Tests may
    pass either explicitly (e.g. a ``tmp_path`` project dir that is itself the root)."""
    pid = project_id if project_id is not None else project_dir.name
    if repo_root is not None:
        return pid, repo_root
    if project_dir.parent.name == "projects":
        return pid, project_dir.parent.parent
    return pid, project_dir


def _evidence_hash(evidence: str) -> str:
    return hashlib.sha256(evidence.encode("utf-8")).hexdigest()


def _cache_path(state_path: Path) -> Path:
    """Sibling of the reject-count state file holding the (key -> evidence-hash +
    verdict) cache. Kept separate so the reject-count file's schema is unchanged."""
    return state_path.parent / "task_verify_cache.yaml"


def _mark_counts(lines: list[str]) -> dict[str, int]:
    """Count real checkbox marks by kind (``X`` done / `` `` open / ``~`` under-review)."""
    out = {"X": 0, " ": 0, "~": 0}
    for line in lines:
        m = _TASK_LINE_RE.match(line)
        if not m:
            continue
        mk = m.group(2)
        if mk in ("x", "X"):
            out["X"] += 1
        elif mk == "~":
            out["~"] += 1
        else:
            out[" "] += 1
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
    project_id: str | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Independently verify each newly-claimed (``[X]`` not in ``already_verified``)
    or previously-deferred (``[~]``) task in ``tasks_path``, rewriting its mark.

    Two tiers (issue #1139): every task is first settled DETERMINISTICALLY from
    filesystem state (free) — declared artifacts all valid → ``[X]``; a production
    task's declared artifacts all missing → ``[ ]``. Only genuinely ambiguous tasks
    reach the bounded (``cap``) semantic LLM, whose verdicts are cached by
    ``(task_key, evidence_hash)`` so unchanged tasks re-verify for free and a verdict
    invalidates the instant the evidence bytes change.

      - COMPLETE   → ``[X]`` (truly done),
      - INCOMPLETE → ``[ ]`` (implementer REDOES it) + a note in ``notes_path``;
        after ``REJECT_CAP`` consecutive INCOMPLETE verdicts the task is NEVER
        force-accepted — it is reopened ``[ ]`` AND recorded in
        :mod:`llmxive.state.unverifiable` (loop broken by escalation, not by lying),
      - DEFER      → ``[~]`` (under review; re-verified later, NOT redone).

    Returns ``{accepted, rejected:[(key,reason)], deferred:[key],
    unverifiable:[key]}``. ``unverifiable`` is non-empty iff this pass recorded (or
    re-encountered) a repeatedly-unverifiable task — CORE routes such a project to
    ``research_full_revision`` (see :mod:`llmxive.state.unverifiable`). Pure file IO
    + the injected :func:`verify_task`; safe to call once per implement-batch."""
    import yaml

    from llmxive.state import unverifiable as _unv
    from llmxive.state._io import atomic_write_text

    project_id, repo_root = _resolve_ids(project_dir, project_id, repo_root)

    text = tasks_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    try:
        reject_counts = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        reject_counts = {}
    if not isinstance(reject_counts, dict):
        reject_counts = {}
    cache_path = _cache_path(state_path)
    try:
        cache = yaml.safe_load(cache_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        cache = {}
    if not isinstance(cache, dict):
        cache = {}
    unv_keys = _unv.recorded_keys(project_id, repo_root=repo_root)

    accepted = 0
    rejected: list[tuple[str, str]] = []
    deferred: list[str] = []
    unverifiable_flagged: list[str] = []
    budget = cap
    keys = task_keys(lines)  # unique + churn-stable; see task_keys()

    def _accept(i: int, m: re.Match[str], rest: str, key: str) -> None:
        nonlocal accepted
        lines[i] = f"{m.group(1)}[X]{rest}"
        accepted += 1
        reject_counts.pop(key, None)

    def _reject(i: int, m: re.Match[str], rest: str, key: str, reason: str) -> None:
        count = int(reject_counts.get(key, 0)) + 1
        reject_counts[key] = count
        lines[i] = f"{m.group(1)}[ ]{rest}"
        rejected.append((key, reason))
        if count >= REJECT_CAP:
            _unv.record_unverifiable(project_id, key, reason, repo_root=repo_root)
            reject_counts.pop(key, None)
            cache.pop(key, None)
            unv_keys.add(key)
            if key not in unverifiable_flagged:
                unverifiable_flagged.append(key)
            LOGGER.warning(
                "[task-verifier] %r rejected %dx — recording UNVERIFIABLE and "
                "reopening [ ] (project routes to research_full_revision; never "
                "force-accepted)",
                key, count,
            )

    for i, line in enumerate(lines):
        m = _TASK_LINE_RE.match(line)
        if not m:
            continue
        mark, rest = m.group(2), m.group(3)
        key = keys[i]
        newly_claimed = mark in ("x", "X") and key not in already_verified
        under_review = mark == "~"
        if not (newly_claimed or under_review):
            continue
        task_text = rest.strip()

        # (A) Already recorded UNVERIFIABLE → do NOT re-judge (this is what breaks
        # the loop REJECT_CAP used to paper over). Keep it OUT of the done set
        # (reopen ``[ ]``) and re-signal so CORE still routes to re-plan.
        if key in unv_keys:
            if mark != " ":
                lines[i] = f"{m.group(1)}[ ]{rest}"
            if key not in unverifiable_flagged:
                unverifiable_flagged.append(key)
            continue

        # (B) DETERMINISTIC-FIRST settle (no LLM) — drains the ``[~]`` backlog cheaply.
        det, det_reason = _deterministic_verdict(project_dir, task_text)
        if det == "accept":
            _accept(i, m, rest, key)
            continue
        if det == "reject":
            _reject(i, m, rest, key, det_reason)
            continue

        # (C) Ambiguous residue → evidence-hash cache, else bounded semantic LLM.
        evidence = gather_evidence(project_dir, rest)
        ev_hash = _evidence_hash(evidence)
        cached = cache.get(key)
        if (
            isinstance(cached, dict)
            and cached.get("h") == ev_hash
            and isinstance(cached.get("c"), bool)
        ):
            complete: bool | None = cached["c"]
            reason = str(cached.get("r") or "(cached verdict; evidence unchanged)")
        elif budget <= 0:
            # Over the per-tick LLM cap with no cache hit → DEFER to a later tick.
            if mark != "~":
                lines[i] = f"{m.group(1)}[~]{rest}"
            deferred.append(key)
            continue
        else:
            budget -= 1
            verdict = verify_task(
                task_text=task_text,
                evidence=evidence,
                spec_context=spec_context,
                model=model,
                default_backend=default_backend,
                fallback_backends=fallback_backends,
            )
            complete = verdict.complete
            reason = verdict.reason
            if complete is not None:
                cache[key] = {"h": ev_hash, "c": complete, "r": reason[:600]}

        if complete is True:
            _accept(i, m, rest, key)
        elif complete is False:
            _reject(i, m, rest, key, reason)
        else:  # deferred (backend outage / unparseable)
            lines[i] = f"{m.group(1)}[~]{rest}"
            deferred.append(key)

    new_text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    if new_text != text:
        atomic_write_text(tasks_path, new_text)

    # Drop reject counts / cache entries for tasks that no longer exist in tasks.md.
    # This also self-heals legacy text-keyed entries stranded by the identity fix, so
    # a task's count reflects ONLY its own consecutive rejections and REJECT_CAP fires.
    live_keys = set(task_keys(lines).values())
    reject_counts = {k: v for k, v in reject_counts.items() if k in live_keys}
    cache = {k: v for k, v in cache.items() if k in live_keys}

    state_path.parent.mkdir(parents=True, exist_ok=True)
    if reject_counts:
        atomic_write_text(state_path, yaml.safe_dump(reject_counts, sort_keys=True))
    else:
        state_path.unlink(missing_ok=True)
    if cache:
        atomic_write_text(cache_path, yaml.safe_dump(cache, sort_keys=True))
    else:
        cache_path.unlink(missing_ok=True)

    _write_notes(notes_path, rejected)
    return {
        "accepted": accepted,
        "rejected": rejected,
        "deferred": deferred,
        "unverifiable": unverifiable_flagged,
    }


def drain_under_review(
    project_dir: Path,
    tasks_path: Path,
    *,
    project_id: str | None = None,
    repo_root: Path | None = None,
    state_path: Path | None = None,
    apply: bool = True,
) -> dict[str, Any]:
    """LLM-FREE maintenance sweep over a project's ``[~]`` (under-review) tasks.

    Re-runs the DETERMINISTIC checks (no model call) and reclassifies each ``[~]``:
    ``[~]``→``[X]`` when its declared artifacts now exist+validate; ``[~]``→``[ ]``
    when a production task's declared artifacts are missing (recording it
    UNVERIFIABLE when its stored reject_count already reached ``REJECT_CAP``); and
    a task already flagged unverifiable is reopened ``[ ]``. Genuinely-ambiguous
    ``[~]`` tasks (no detectable path) are LEFT ``[~]`` — they still need the
    semantic verifier. With ``apply=False`` (dry-run) the reclassification is
    computed WITHOUT writing tasks.md or recording anything.

    Returns ``{project_id, before:{X,' ',~}, after:{…}, accepted, reopened,
    unverifiable:[key], ambiguous}`` (``before``/``after`` are mark counts)."""
    import yaml

    from llmxive.state import unverifiable as _unv
    from llmxive.state._io import atomic_write_text

    project_id, repo_root = _resolve_ids(project_dir, project_id, repo_root)
    if state_path is None:
        state_path = project_dir / ".specify" / "memory" / "task_verify.yaml"

    text = tasks_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    try:
        reject_counts = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        reject_counts = {}
    if not isinstance(reject_counts, dict):
        reject_counts = {}
    unv_keys = _unv.recorded_keys(project_id, repo_root=repo_root)
    keys = task_keys(lines)
    before = _mark_counts(lines)

    accepted = reopened = ambiguous = 0
    newly_unverifiable: list[str] = []
    for i, line in enumerate(lines):
        m = _TASK_LINE_RE.match(line)
        if not m or m.group(2) != "~":
            continue
        rest = m.group(3)
        key = keys[i]
        task_text = rest.strip()
        if key in unv_keys:
            lines[i] = f"{m.group(1)}[ ]{rest}"
            reopened += 1
            continue
        det, reason = _deterministic_verdict(project_dir, task_text)
        if det == "accept":
            lines[i] = f"{m.group(1)}[X]{rest}"
            accepted += 1
        elif det == "reject":
            lines[i] = f"{m.group(1)}[ ]{rest}"
            reopened += 1
            if int(reject_counts.get(key, 0)) >= REJECT_CAP:
                if apply:
                    _unv.record_unverifiable(
                        project_id, key, reason, repo_root=repo_root
                    )
                newly_unverifiable.append(key)
        else:
            ambiguous += 1  # leave [~] — needs the semantic verifier

    after = _mark_counts(lines)
    if apply:
        new_text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
        if new_text != text:
            atomic_write_text(tasks_path, new_text)
    return {
        "project_id": project_id,
        "before": before,
        "after": after,
        "accepted": accepted,
        "reopened": reopened,
        "unverifiable": newly_unverifiable,
        "ambiguous": ambiguous,
    }


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
    "drain_under_review",
    "gather_evidence",
    "run_verification_pass",
    "task_keys",
    "verify_task",
]
