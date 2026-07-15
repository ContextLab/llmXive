"""Typed advancement-failure ledger (issue #1139, defect D5).

Before this module the pipeline wrote ``state/advance_errors/<id>.json`` on every
per-project advancement exception, incremented a bare ``count``, and then never
read it: no backoff gated reselection and no success path cleared it. The
scheduler re-picked a permanently-failing project every tick, so one dead
reference or template-rejecting emitter burned unlimited scheduler slots
(PROJ-077 alone looped 365x; 733 wasted attempts across 74 records).

This is the ONE shared read/write/classify module for that ledger — both
``cli.py`` (writer + success-path clear) and ``pipeline/scheduler.py``
(``_eligible_candidates`` backoff/hold gate) route through it (Constitution I).

Record schema (``state/advance_errors/<id>.json``, atomic via ``state/_io``)::

    {
      "project_id":        str,
      "stage":             str,            # project.current_stage.value at failure
      "class":             ErrorClass,     # taxonomy that drives control behavior
      "fingerprint":       str,            # one of the 9 real fingerprints (+ unknown)
      "consecutive_count": int,            # CONSECUTIVE failures (reset by clear())
      "first_seen":        ISO-8601 str,
      "last_seen":         ISO-8601 str,
      "retry_after":       ISO-8601 str | None,  # None => never retried via backoff
      "last_error":        str,            # truncated raw exception text
      "evidence":          str,            # concise, whitespace-collapsed excerpt
      "remediation":       str,            # class-level "what to do about it"
      "status":            LedgerStatus,
    }

Control behavior (assigned by :func:`disposition` off the :class:`ErrorClass`):

* ``transient`` (backend/model chain flap, unrecognized error) — retry with
  EXPONENTIAL BACKOFF ``retry_after = last_seen + BASE * 2**min(count, cap)``;
  ``status=retry_scheduled``. The scheduler skips it until ``retry_after``.
* ``deterministic_repair`` (``[Errno 17]`` file-exists collision) — same bounded
  backoff so it does NOT loop every tick; the real fix is idempotent artifact
  creation in the execution stage, and the remediation says so.
* ``invariant`` (invalid state-machine transition) — ``status=terminal``,
  ``retry_after=None``: a code bug retrying can never fix. Never consumes retry
  budget; routed to AGENT_BLOCKED / operator.
* ``permanent`` (unreachable reference w/o replacement, unfilled-template emit)
  and ``emitter_context`` (unresolved markers / no seed draft / zero tasks) —
  ``status=rerouted``, ``retry_after=None``: do NOT re-dispatch unchanged; return
  the evidence to a source-aware re-plan or the emitter.

The scheduler honours the disposition via :func:`is_on_hold`: a project is
SKIPPED while its record (for the project's *current* stage) is either in a
pending backoff window or in a ``rerouted``/``terminal`` hold. A record for a
DIFFERENT stage than the project now sits at is stale (the project advanced past
the failing step) and is ignored. A successful advancement step calls
:func:`clear`, resetting ``consecutive_count`` so it always reflects
*consecutive* failures.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path

from llmxive.state._io import atomic_write_text

# --------------------------------------------------------------------------
# Constants (kept HERE, not in config.py, per issue #1139 scoping)
# --------------------------------------------------------------------------

#: Ledger directory, relative to the repo root.
LEDGER_SUBDIR: tuple[str, ...] = ("state", "advance_errors")

#: Exponential-backoff base (seconds) for a transient/deterministic-repair retry.
#: 5 minutes — long enough that a flapping backend is not re-hammered every tick,
#: short enough that a genuinely transient failure recovers within a cron cycle.
BASE_BACKOFF_SECONDS: float = 300.0

#: Cap on the backoff exponent. 2**8 == 256, so the retry window saturates at
#: ``256 * 5 min`` ≈ 21.3 h — roughly one retry per day once a failure has
#: recurred ~8 times, instead of the unbounded every-tick re-pick it replaces.
BACKOFF_CAP: int = 8

#: Max characters of raw exception text persisted in ``last_error``.
_MAX_ERROR_CHARS: int = 1000
#: Max characters of the whitespace-collapsed ``evidence`` excerpt.
_MAX_EVIDENCE_CHARS: int = 400


class ErrorClass(StrEnum):
    """Why an advancement attempt failed — drives the control disposition.

    ``str``-valued so it round-trips through the JSON record verbatim.
    """

    #: Flaky/recoverable (backend or model chain flap, network, unrecognized) —
    #: retry with exponential backoff.
    TRANSIENT = "transient"
    #: The source or emitted artifact cannot be advanced as-is (dead reference
    #: without a replacement, unfilled-template emit) — reroute, do not re-emit.
    PERMANENT = "permanent"
    #: An invalid state-machine transition — a code bug; retrying can never fix
    #: it. Terminal / route to AGENT_BLOCKED.
    INVARIANT = "invariant"
    #: A deterministic filesystem collision (dir/file already exists) — the step
    #: must be made idempotent; backoff prevents the every-tick loop meanwhile.
    DETERMINISTIC_REPAIR = "deterministic_repair"
    #: The emitter produced insufficient output (unresolved markers, no seed
    #: draft, zero tasks) — supply the missing context, do not blindly re-emit.
    EMITTER_CONTEXT = "emitter_context"


class LedgerStatus(StrEnum):
    """Current disposition of a ledger record."""

    #: Transient/deterministic-repair — eligible again once ``retry_after`` passes.
    RETRY_SCHEDULED = "retry_scheduled"
    #: Permanent/emitter-context — held out of scheduling pending a re-plan /
    #: emitter re-input (do NOT re-dispatch unchanged).
    REROUTED = "rerouted"
    #: Invariant — held out of scheduling; a code bug for AGENT_BLOCKED/operator.
    TERMINAL = "terminal"
    #: A subsequent step succeeded — record neutralized; ``consecutive_count`` 0.
    CLEARED = "cleared"


#: Statuses whose projects the scheduler holds out of reselection until a
#: re-plan / operator / stage-change releases them (see :func:`is_schedulable`).
_HOLD_STATUSES: frozenset[str] = frozenset(
    {LedgerStatus.REROUTED.value, LedgerStatus.TERMINAL.value}
)

# --------------------------------------------------------------------------
# The nine real fingerprints (recon C) + an unknown catch-all.
# --------------------------------------------------------------------------

FP_UNREACHABLE_REFERENCE = "unreachable_reference"
FP_TEMPLATE_REJECTION = "template_rejection"
FP_BACKEND_CHAIN_FAILED = "backend_chain_failed"
FP_INVALID_TRANSITION = "invalid_transition"
FP_FILESYSTEM_FILE_EXISTS = "filesystem_file_exists"
FP_MODEL_CHAIN_FAILED = "model_chain_failed"
FP_UNRESOLVED_MARKERS = "unresolved_markers"
FP_NO_SEED_DRAFT = "no_seed_draft"
FP_TASKER_ZERO_TASKS = "tasker_zero_tasks"
FP_UNKNOWN = "unknown"

#: Fingerprint -> class. An unrecognized error defaults to ``transient`` (retry
#: with backoff) — the safe default: it neither loops every tick nor permanently
#: abandons a project on a signature we simply do not recognize yet.
_FINGERPRINT_CLASS: dict[str, ErrorClass] = {
    FP_UNREACHABLE_REFERENCE: ErrorClass.PERMANENT,
    FP_TEMPLATE_REJECTION: ErrorClass.PERMANENT,
    FP_BACKEND_CHAIN_FAILED: ErrorClass.TRANSIENT,
    FP_INVALID_TRANSITION: ErrorClass.INVARIANT,
    FP_FILESYSTEM_FILE_EXISTS: ErrorClass.DETERMINISTIC_REPAIR,
    FP_MODEL_CHAIN_FAILED: ErrorClass.TRANSIENT,
    FP_UNRESOLVED_MARKERS: ErrorClass.EMITTER_CONTEXT,
    FP_NO_SEED_DRAFT: ErrorClass.EMITTER_CONTEXT,
    FP_TASKER_ZERO_TASKS: ErrorClass.EMITTER_CONTEXT,
    FP_UNKNOWN: ErrorClass.TRANSIENT,
}

#: Class-level remediation threaded into the record for review / re-plan.
REMEDIATION: dict[ErrorClass, str] = {
    ErrorClass.TRANSIENT: (
        "Backend/model chain or network flaked (or the signature is unrecognized). "
        "Retry with exponential backoff. If it persists past the cap the chain/model "
        "config or the remote is genuinely down — check backend health."
    ),
    ErrorClass.PERMANENT: (
        "The reference/source is unreachable, or the emitted artifact is an unfilled "
        "template with no valid content. Do NOT re-dispatch unchanged: route the "
        "evidence to a source-aware re-plan (inject a verified replacement source) or "
        "back to the emitter, or mark terminal if genuinely unrecoverable."
    ),
    ErrorClass.INVARIANT: (
        "An invalid state-machine transition was attempted — a code bug, not a flake; "
        "retrying can never fix it. Route to AGENT_BLOCKED and fix the transition logic."
    ),
    ErrorClass.DETERMINISTIC_REPAIR: (
        "A deterministic filesystem collision (a dir/file already exists). Make the "
        "step idempotent (exist_ok=True / reconcile the existing artifact) then retry; "
        "backoff spaces the retries so it does not loop every tick meanwhile."
    ),
    ErrorClass.EMITTER_CONTEXT: (
        "The emitter produced insufficient output (unresolved markers / no seed draft / "
        "zero tasks). Supply the missing inputs/context and re-run; do not blindly "
        "re-emit the same empty artifact."
    ),
}


def classify_message(message: str) -> tuple[str, ErrorClass]:
    """Fingerprint a failure from its exception text, returning ``(fingerprint, class)``.

    Ordering is load-bearing: a ``backend_chain_failed`` message wraps a nested
    ``every model in chain ...`` error, so "every backend in chain" MUST be tested
    before "every model in chain" or the outer failure would misclassify.
    """
    low = (message or "").lower()
    if "invalid transition" in low:
        fp = FP_INVALID_TRANSITION
    elif "refused to emit a 'template'" in low or "unfilled_bracket" in low:
        fp = FP_TEMPLATE_REJECTION
    elif "[errno 17]" in low:  # "[Errno 17] File exists: '.../code'"
        fp = FP_FILESYSTEM_FILE_EXISTS
    elif "reference is unreachable" in low:
        fp = FP_UNREACHABLE_REFERENCE
    elif "every backend in chain" in low:  # BEFORE "every model in chain" (nested)
        fp = FP_BACKEND_CHAIN_FAILED
    elif "every model in chain" in low:
        fp = FP_MODEL_CHAIN_FAILED
    elif "markers unresolved" in low:  # "Clarifier left 3 of 3 markers unresolved"
        fp = FP_UNRESOLVED_MARKERS
    elif "draft to seed" in low or "to seed from" in low:
        fp = FP_NO_SEED_DRAFT
    elif "tasker produced only" in low or ("task id" in low and "produced" in low):
        fp = FP_TASKER_ZERO_TASKS
    else:
        fp = FP_UNKNOWN
    return fp, _FINGERPRINT_CLASS[fp]


def classify(exc: Exception) -> tuple[str, ErrorClass]:
    """Fingerprint + class for an exception (message- and type-keyed)."""
    return classify_message(str(exc))


def compute_retry_after(last_seen: datetime, consecutive_count: int) -> datetime:
    """Exponential-backoff next-eligible time: ``last_seen + BASE * 2**min(n, cap)``.

    Monotonically non-decreasing in ``consecutive_count`` and capped at
    :data:`BACKOFF_CAP` so the retry window saturates instead of growing forever.
    """
    exp = min(max(int(consecutive_count), 0), BACKOFF_CAP)
    return last_seen + timedelta(seconds=BASE_BACKOFF_SECONDS * (2**exp))


def disposition(
    error_class: ErrorClass, *, last_seen: datetime, consecutive_count: int
) -> tuple[LedgerStatus, datetime | None]:
    """Map a class to ``(status, retry_after)``.

    Transient / deterministic-repair get a backoff ``retry_after``; invariant is
    terminal; permanent / emitter-context are rerouted. The latter three carry NO
    ``retry_after`` — they never consume the backoff budget (retrying cannot fix a
    code bug, a dead source, or an empty template).
    """
    if error_class in (ErrorClass.TRANSIENT, ErrorClass.DETERMINISTIC_REPAIR):
        return LedgerStatus.RETRY_SCHEDULED, compute_retry_after(
            last_seen, consecutive_count
        )
    if error_class == ErrorClass.INVARIANT:
        return LedgerStatus.TERMINAL, None
    # PERMANENT and EMITTER_CONTEXT
    return LedgerStatus.REROUTED, None


def _evidence(message: str) -> str:
    """A concise, single-line excerpt of the failure for review / re-plan."""
    return " ".join((message or "").split())[:_MAX_EVIDENCE_CHARS]


def make_record(
    *,
    project_id: str,
    stage: str,
    message: str,
    consecutive_count: int,
    first_seen: str,
    last_seen: datetime,
) -> dict:
    """Build a fully-typed record dict from its parts (shared by the live writer
    and the one-time migration). ``last_seen`` is a datetime (used for backoff)."""
    fingerprint, error_class = classify_message(message)
    status, retry_after = disposition(
        error_class, last_seen=last_seen, consecutive_count=consecutive_count
    )
    return {
        "project_id": project_id,
        "stage": stage,
        "class": error_class.value,
        "fingerprint": fingerprint,
        "consecutive_count": int(consecutive_count),
        "first_seen": first_seen,
        "last_seen": last_seen.isoformat(),
        "retry_after": retry_after.isoformat() if retry_after is not None else None,
        "last_error": (message or "")[:_MAX_ERROR_CHARS],
        "evidence": _evidence(message),
        "remediation": REMEDIATION[error_class],
        "status": status.value,
    }


# --------------------------------------------------------------------------
# Path + IO
# --------------------------------------------------------------------------


def _repo_base(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return Path(repo_root)
    from llmxive.config import repo_root as _rr

    return _rr()


def record_path(project_id: str, repo_root: Path | None = None) -> Path:
    """Absolute path to a project's ledger file."""
    return _repo_base(repo_root).joinpath(*LEDGER_SUBDIR, f"{project_id}.json")


def load_record(project_id: str, *, repo_root: Path | None = None) -> dict | None:
    """Read a project's ledger record, or ``None`` if absent/unreadable."""
    path = record_path(project_id, repo_root)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write(path: Path, record: dict) -> None:
    atomic_write_text(path, json.dumps(record, indent=2))


def record_failure(
    project,
    exc: Exception,
    *,
    repo_root: Path | None = None,
    now: datetime | None = None,
) -> dict:
    """Persist a typed advancement-failure record, incrementing the CONSECUTIVE
    failure count (a prior ``cleared``/absent record restarts the count at 1).

    Returns the written record. Never raises through to the caller's control flow
    beyond normal IO exceptions — the CLI wraps this so recording can never crash
    the run.
    """
    now = now or datetime.now(UTC)
    path = record_path(project.id, repo_root)
    prior = load_record(project.id, repo_root=repo_root)
    prior_count = 0
    first_seen = now.isoformat()
    if prior is not None and prior.get("status") != LedgerStatus.CLEARED.value:
        prior_count = int(prior.get("consecutive_count", 0) or 0)
        first_seen = prior.get("first_seen") or first_seen
    record = make_record(
        project_id=project.id,
        stage=project.current_stage.value,
        message=str(exc),
        consecutive_count=prior_count + 1,
        first_seen=first_seen,
        last_seen=now,
    )
    _write(path, record)
    return record


def clear(
    project, *, repo_root: Path | None = None, now: datetime | None = None
) -> bool:
    """Neutralize a project's record after a SUCCESSFUL advancement step.

    Sets ``status=cleared`` and ``consecutive_count=0`` (preserving ``first_seen``
    for audit) so the next failure starts a fresh consecutive streak at 1. Returns
    ``True`` when a record existed. A no-op (returns ``False``) when there is none.
    """
    record = load_record(project.id, repo_root=repo_root)
    if record is None:
        return False
    if record.get("status") == LedgerStatus.CLEARED.value:
        return True
    now = now or datetime.now(UTC)
    record["status"] = LedgerStatus.CLEARED.value
    record["consecutive_count"] = 0
    record["retry_after"] = None
    record["last_seen"] = now.isoformat()
    _write(record_path(project.id, repo_root), record)
    return True


# --------------------------------------------------------------------------
# Scheduler gate
# --------------------------------------------------------------------------


def _parse(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def is_schedulable(record: dict | None, *, now: datetime | None = None) -> bool:
    """Whether a project carrying ``record`` may be scheduled right now.

    * no record / ``cleared`` -> schedulable.
    * ``retry_scheduled`` -> schedulable ONLY once ``retry_after`` has passed
      (this is the backoff gate that stops the every-tick re-pick).
    * ``rerouted`` / ``terminal`` -> NOT schedulable — held for re-plan / routing,
      never resurrected by backoff (they carry no ``retry_after``).
    """
    if record is None:
        return True
    status = record.get("status")
    if status in (None, LedgerStatus.CLEARED.value):
        return True
    if status in _HOLD_STATUSES:
        return False
    if status == LedgerStatus.RETRY_SCHEDULED.value:
        retry_after = record.get("retry_after")
        if not retry_after:
            return True
        now = now or datetime.now(UTC)
        try:
            return now >= _parse(retry_after)
        except (TypeError, ValueError):
            return True
    return True  # unknown status -> do not strand the project


def is_on_hold(project, *, repo_root: Path | None = None, now: datetime | None = None) -> bool:
    """True when the scheduler should SKIP ``project`` because of its ledger record.

    The record only applies while the project still sits at the stage it failed
    at: a record whose ``stage`` differs from ``project.current_stage`` is stale
    (the project advanced past the failing step, e.g. via an operator re-route)
    and is ignored, so a stale hold can never permanently strand a project.
    """
    record = load_record(project.id, repo_root=repo_root)
    if record is None:
        return False
    if record.get("stage") != project.current_stage.value:
        return False
    return not is_schedulable(record, now=now)


__all__ = [
    "BACKOFF_CAP",
    "BASE_BACKOFF_SECONDS",
    "REMEDIATION",
    "ErrorClass",
    "LedgerStatus",
    "classify",
    "classify_message",
    "clear",
    "compute_retry_after",
    "disposition",
    "is_on_hold",
    "is_schedulable",
    "load_record",
    "make_record",
    "record_failure",
    "record_path",
]
