"""The lane's append-only store on the DEDICATED authoritative ref (FR-009 rev-15): thin
wrappers over the shared :mod:`llmxive.git_event_log` CAS core. Per-Problem subtrees give
each Problem (and the coordinator) an authoritative, gap-checked ``seq`` line; the single
ref serializes all lane mutations (FR-008). Bootstrapped once, fetched by the transport,
FAILS CLOSED until bootstrapped, and supports ``expected_anchor`` pinning."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from llmxive.git_event_log import (
    AppendResult,
    GitLogDenied,
    GitLogError,
    LogRef,
    append_to_log,
    bootstrap_log,
    read_log,
    sync_and_verify,
)
from llmxive.self_improvement.events import (
    COORDINATOR_STREAM,
    SEQ_FIELD,
    Event,
    event_from_json,
    event_to_json,
    validate_lane_event,
)

LANE_REF = "refs/llmxive/self-improvement"
_LANE_GENESIS_MSG = "bootstrap self-improvement lane log v1"


@dataclass(frozen=True)
class LaneLogConfig:
    """Remote identity + pinned history anchor for the lane ref — parallel to
    ``LedgerConfig``. Threaded through EVERY lane bootstrap/read/append (and the
    coordinator/ledger/audit APIs) so a caller can PIN the history anchor — critical for
    an autonomous self-modifying system. Default is local-only (tests / single runner)."""

    remote: str | None = None
    expected_anchor: str | None = None


#: Fields excluded from the append-only IDENTITY comparison: the store-assigned ``seq``,
#: the FR-011 ``timestamp`` (one canonical field — NO duplicate ``ts``), and the four CAS
#: revision ANCHORS — none is part of an operation's semantic identity, so a re-invoked
#: operation whose event lands at a DIFFERENT revision/time is still an idempotent no-op,
#: not a spurious append-only raise.
_IDENTITY_EXCLUDE = frozenset({
    SEQ_FIELD, "timestamp", "expected_lane_revision", "resulting_lane_revision",
    "expected_problem_revision", "resulting_problem_revision",
})


class LaneRevisionConflict(RuntimeError):
    """The CAS precondition (expected_revision or a caller precondition) no longer holds
    against the authoritative tip — recompute and retry/yield (FR-008); never force."""


class LaneContention(RuntimeError):
    """A caller's bounded CAS retry loop never converged. Defined HERE, once, because every
    lane CAS user raises it (``AttemptCreditLedger``, ``LaneCallLedger``, the coordinator) —
    a per-module copy would give the same condition several unrelated types."""


def _log_ref(problem_id: str, config: LaneLogConfig | None = None) -> LogRef:
    # ONE ref; per-Problem (and coordinator) subtree → per-stream seq line. `None`
    # resolves to the local-only default HERE, as `ledger_transport._log_ref` does, so no
    # public signature carries a constructor call as its default.
    config = config or LaneLogConfig()
    return LogRef(ref=LANE_REF, event_dir=f"self-improvement/events/{problem_id}",
                  remote=config.remote, expected_anchor=config.expected_anchor)


def bootstrap_lane_log(repo: Path, *, config: LaneLogConfig,
                       _after_probe: Callable[[], None] | None = None) -> str:
    """One-time creation of the authoritative lane ref, mirroring the credit ledger's
    ``bootstrap_ledger``: a genesis anchor commit on ``LANE_REF``. Invoked ONCE by a
    privileged setup workflow — NOT by an ordinary lane call; every remote read/append
    FAILS CLOSED until it has run, exactly like the credit ledger. Idempotent (a repeat
    returns the same anchor, no second genesis); two concurrent bootstrappers converge on
    ONE ref (FF-push CAS); a divergent/wrong existing ref fails closed. Returns the genesis
    anchor OID — PIN it as ``LaneLogConfig.expected_anchor`` thereafter. The ref is
    protected: only the trusted lane transport advances it, fast-forward only.

    ``_after_probe`` is the TEST-ONLY barrier seam forwarded to the core so two
    bootstrappers can be held past the existence probe and genuinely race the push."""
    return bootstrap_log(repo, log=_log_ref(COORDINATOR_STREAM, config), message=_LANE_GENESIS_MSG,
                         remote=config.remote, _after_probe=_after_probe)


def _message(event: dict) -> str:
    return f"self-improvement: {event.get('event_type', '?')} {event['event_id']}"


def _sorted_by_seq(raw: list[dict]) -> list[dict]:
    return sorted(raw, key=lambda r: r.get("seq", -1))  # seq is the AUTHORITATIVE order


def _to_json(raw: dict) -> str:
    # allow_nan=False mirrors event_to_json — the canonical form is the SAME in both
    # directions, and neither may produce non-standard JSON.
    return json.dumps(raw, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def _to_event(raw: dict) -> Event:
    """One stored record → an ``Event`` through the canonical form.

    The re-serialization is not just symmetry: a hand-corrupted blob carrying bare ``NaN``
    parses in Python and would flow into a projection as a number every comparison answers
    False about. Corruption found on a read raises ``GitLogError`` — the same fail-closed
    type as a broken sequence, not a ``ValueError`` a caller could read as a schema
    complaint about its own argument."""
    try:
        return event_from_json(_to_json(raw))
    except ValueError as exc:
        raise GitLogError(f"corrupt lane event {raw.get('event_id')!r}: {exc}") from exc


def _check_continuity(raw_sorted: list[dict], problem_id: str) -> None:
    seqs = [r.get("seq") for r in raw_sorted]
    if seqs != list(range(len(raw_sorted))):
        # A gap/dup/fork is corruption of the authoritative sequence — fail closed,
        # never retry (a GitLogError propagates out of the CAS loop; NOT a conflict).
        raise GitLogError(f"corrupt sequence in stream {problem_id!r}: {seqs}")


def read(repo: Path, problem_id: str, *, config: LaneLogConfig | None = None) -> list[Event]:
    """Every event on one stream, ordered by the authoritative ``seq`` (never timestamps).

    Synchronizes FIRST: ``read_log`` is a LOCAL object-store read by design, so a public
    read that skipped this would project an empty log on any checkout that has not fetched
    the ref — and an empty log means "no claim, no reservation, no spend" to every
    projection built on it. ``sync_and_verify`` also fails closed on an unbootstrapped
    remote and on a tip that does not descend from the pinned anchor. Local-only configs
    make it a no-op, so this costs nothing in that mode."""
    log = _log_ref(problem_id, config)
    sync_and_verify(repo, log=log)
    raw_sorted = _sorted_by_seq(read_log(repo, log=log, validate=validate_lane_event))
    _check_continuity(raw_sorted, problem_id)
    return [_to_event(r) for r in raw_sorted]


def _finalize(built: dict, seq: int) -> dict:
    """Stamp the store-owned fields inside the CAS.

    ALL FOUR anchors are written, not only this stream's scope: the store is their sole
    authority (FR-011 requires ``expected == seq`` and ``resulting == seq + 1`` against the
    VERIFIED parent), so an anchor a caller pre-filled — on either scope — is overwritten
    rather than trusted. Leaving the other scope alone would let a caller's leftover value
    survive into history and fail validation on a stream it does not even belong to."""
    scope = "lane" if built["problem_id"] == COORDINATOR_STREAM else "problem"
    other = "problem" if scope == "lane" else "lane"
    return {**built, SEQ_FIELD: seq,
            f"expected_{scope}_revision": seq, f"resulting_{scope}_revision": seq + 1,
            f"expected_{other}_revision": None, f"resulting_{other}_revision": None}


def append(repo: Path, event: Event, *, expected_revision: int | None,
           precondition: Callable[[list[Event]], tuple[bool, str]] | None = None,
           config: LaneLogConfig | None = None,
           _after_parent: Callable[[], None] | None = None) -> AppendResult:
    """CAS-append one lane event. ``expected_revision=None`` = an UNCONDITIONAL append
    (audit events carry no revision precondition — just the ref-CAS + idempotency). Raises
    ``LaneRevisionConflict`` when the revision/precondition lost; a corrupt sequence raises
    ``GitLogError`` (fail closed). ``_after_parent`` is a TEST-ONLY seam forwarded to the
    core so a barrier can make the non-fast-forward race deterministic."""
    raw = json.loads(event_to_json(event))  # carries `timestamp`; NO duplicate `ts`

    def _predicate(existing: list[dict]) -> tuple[bool, str]:
        ordered = _sorted_by_seq(existing)
        _check_continuity(ordered, event.problem_id)  # BEFORE any other check
        if expected_revision is not None and len(ordered) != expected_revision:
            return (False, f"stale revision: expected {expected_revision}, actual {len(ordered)}")
        if precondition is not None:
            return precondition([_to_event(r) for r in ordered])
        return (True, "")

    try:
        return append_to_log(
            repo, log=_log_ref(event.problem_id, config), validate=validate_lane_event,
            message_fn=_message, event=raw, predicate=_predicate, finalize=_finalize,
            identity_exclude=_IDENTITY_EXCLUDE, _after_parent=_after_parent,
        )
    except GitLogDenied as exc:  # predicate returned False → a lane CAS conflict
        raise LaneRevisionConflict(str(exc)) from exc
    # a GitLogError from _check_continuity (corruption) propagates unchanged — fail closed.


__all__ = [
    "LANE_REF",
    "LaneContention",
    "LaneLogConfig",
    "LaneRevisionConflict",
    "append",
    "bootstrap_lane_log",
    "read",
]
