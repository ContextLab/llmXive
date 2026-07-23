"""Typed hook contracts for the spec-025 self-improvement lane (026 follow-up).

The lane cannot enforce a per-Attempt credit budget or capture routing provenance
from outside ``route_chat`` (the candidate + its ``worst_case_credits`` are unknown
until ``select`` runs, and ``route_chat`` returns only a ``ChatResponse``). So the
chokepoint accepts two OPTIONAL hooks the lane injects:

- ``ReservationAuthority`` — an ENFORCEMENT gate consulted before each paid dispatch;
  it can DENY (skip the candidate). Its ``reserve`` MUST NOT raise for an ordinary
  budget denial (it returns ``False``); an infrastructure failure may raise and is
  surfaced.
- ``RouteAudit`` — a MANDATORY, SYNCHRONOUS, durable audit sink (NOT best-effort
  telemetry). It follows an OUTBOX lifecycle: ``ChainResolved`` → ``ReservationOpened``
  → ``DispatchStarted`` (all durable BEFORE the backend call) → ``DispatchCompleted``.
  A ``record`` exception is never swallowed: pre-dispatch it is route-fatal
  (``RouteAuditError``), post-dispatch the call fails closed with the reservation
  preserved. ``DispatchUnknown`` is produced by the lane's reconciler from a durable
  un-completed ``DispatchStarted`` — the chokepoint never emits it.

Every event carries a ``route_id`` (threaded from ``route_chat``/``execute``) and an
auto-derived, deterministic-within-a-route ``event_id`` (spec-025 maintainer review
F1) so the lane can correlate/pair events (e.g. a ``DispatchStarted`` with its
``DispatchCompleted``) without inventing its own correlation scheme. Candidate
events additionally carry the full ``ModelRef`` identity + a ``candidate_index``
(F2) so the lane can reconstruct an ``InvocationIdentity`` without a second lookup.

This module is pure types (no I/O, no networked imports), so it is safe to import
eagerly from the package root — unlike ``snapshot``/``route``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from llmxive.model_selection.types import ModelRef, SnapshotProvenance


class RouteAuditError(RuntimeError):
    """A mandatory ``RouteAudit.record`` call failed. Route-fatal when raised
    pre-dispatch: it ABORTS the logical route call and NEVER advances to another
    candidate (an audit outage must not silently change which model executes).
    Distinct from ``ModelUnavailable`` (nothing eligible) and ``ChainExhausted``
    (the chain ran, none succeeded), so it does not trigger the proposal reroute."""


class RouteReplayError(RuntimeError):
    """Raised by ``execute`` when ``RouteAudit.claim_dispatch`` reports that this
    (route_id, candidate) already crossed the dispatch boundary — a REPLAY. The
    backend is NOT re-invoked; any paid reservation is RETAINED (the original
    dispatch owns it), and the caller/lane reconciles from durable events (e.g. a
    ``DispatchStarted`` with no ``DispatchCompleted`` → ``DispatchUnknown`` → fail
    the Attempt closed). Distinct from ``RouteAuditError`` (the sink itself failed)
    and ``ModelUnavailable``/``ChainExhausted``."""


def _candidate_event_id(route_id: str, candidate_index: int, kind: str) -> str:
    return f"{route_id}:candidate:{candidate_index}:{kind}"


@runtime_checkable
class ReservationAuthority(Protocol):
    """An Attempt-scoped budget gate (FR-033). Injected by the lane; the
    model-selection layer only CALLS it, never constructs it."""

    def reserve(self, credits: float, *, reservation_id: str, call_id: str) -> bool:
        """Atomically reserve ``credits`` (the worst-case x retries envelope)
        against the Attempt budget. Return ``True`` if admitted, ``False`` if it
        would exceed the budget (the candidate is skipped/advanced). MUST NOT raise
        for an ordinary budget denial.

        **Collision semantics (spec-025 maintainer review fix #5), mirroring the
        026 ledger's own ``reserve`` (``reservations.py`` ``prepare()``,
        ~lines 236-255):**

        - a repeated ``reservation_id`` with the SAME ``(credits, call_id)``
          identity (e.g. a replayed/retried candidate re-deriving the identical
          reservation) is an IDEMPOTENT SUCCESS — return the same admit result
          WITHOUT opening a second hold or double-counting the budget;
        - the same ``reservation_id`` with a DIFFERENT ``credits``/identity is an
          INTEGRITY VIOLATION — raise, never silently overwrite the existing hold
          (a bigger call must never run under an older, smaller reservation);
        - concurrent duplicate reservations for one id must settle on exactly ONE
          durable reservation (a compare-and-swap / unique-insert, not a
          read-then-write).

        A real slice-1 ``AttemptCreditLedger`` MUST enforce all three; so must any
        in-memory test double used in place of it."""

    def release(self, reservation_id: str) -> None:
        """Release a reservation that definitively did NOT dispatch (``open →
        released`` — e.g. the 026 daily reserve failed after this one opened, or a
        pre-dispatch audit failure aborted the route)."""

    def mark_retained(self, reservation_id: str) -> None:
        """Mark a DISPATCHED reservation reconciliation-pending (``open →
        retained``); the lane's reconciler later moves it to ``reconciled``."""


@dataclass(frozen=True)
class ChainResolved:
    """Emitted once after ``select`` succeeds, before any dispatch. Carries the
    full provenance the lane needs to build an ``InvocationIdentity`` for the
    winning candidate (FR-002): the candidate ``ModelRef``s (→ model/backend/
    family/vendor/endpoint), the requirement + prompt + context digests, the
    snapshot digest AND per-component provenance, and the selection policy
    version. ``prompt_digest``/``context_digest`` are caller-supplied (route_chat
    defaults them to a digest of the actual routed messages)."""

    route_id: str
    requirement_digest: str
    prompt_digest: str
    context_digest: str
    snapshot_digest: str
    snapshot_provenance: Mapping[str, SnapshotProvenance]
    selection_policy_version: int
    resolved_at: str
    explanation: tuple[str, ...]
    candidates: tuple[ModelRef, ...]
    event_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", f"{self.route_id}:chain-resolved")


@dataclass(frozen=True)
class SelectionFailure:
    """Emitted when ``select`` raises ``ModelUnavailable`` (the failed first leg
    of the proposal reroute, FR-002/F3). Raw failure only — no causal claim.
    ``snapshot_provenance`` is the full per-component mapping."""

    route_id: str
    exception_type: str
    message: str
    requirement_digest: str
    snapshot_provenance: Mapping[str, SnapshotProvenance]
    event_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", f"{self.route_id}:selection-failure")


@dataclass(frozen=True)
class ReservationOpened:
    """Emitted once per paid candidate whose Attempt + 026 reservations both opened."""

    route_id: str
    candidate_index: int
    candidate: ModelRef
    reservation_id: str
    reserved_credits: float
    event_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "event_id", _candidate_event_id(self.route_id, self.candidate_index, "reservation-opened")
        )


@dataclass(frozen=True)
class DispatchStarted:
    """Emitted (durably) immediately BEFORE the backend call for a candidate."""

    route_id: str
    candidate_index: int
    candidate: ModelRef
    reservation_id: str | None
    event_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "event_id", _candidate_event_id(self.route_id, self.candidate_index, "dispatch-started")
        )


@dataclass(frozen=True)
class DispatchCompleted:
    """Emitted immediately AFTER a successful backend call for a candidate."""

    route_id: str
    candidate_index: int
    candidate: ModelRef
    reservation_id: str | None
    event_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "event_id", _candidate_event_id(self.route_id, self.candidate_index, "dispatch-completed")
        )


@dataclass(frozen=True)
class DispatchUnknown:
    """NOT emitted by ``execute``; the lane's reconciler produces it from a durable
    ``DispatchStarted`` with no matching ``DispatchCompleted``."""

    route_id: str
    candidate_index: int
    candidate: ModelRef
    reservation_id: str | None
    event_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "event_id", _candidate_event_id(self.route_id, self.candidate_index, "dispatch-unknown")
        )


@dataclass(frozen=True)
class CandidateOutcome:
    """Emitted once per candidate terminal disposition."""

    route_id: str
    candidate_index: int
    candidate: ModelRef
    outcome: str  # "success" | "skip" | "advance" | "abort"
    reason: str
    event_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", _candidate_event_id(self.route_id, self.candidate_index, "outcome"))


RouteAuditEvent = (
    ChainResolved | SelectionFailure | ReservationOpened | DispatchStarted
    | DispatchCompleted | DispatchUnknown | CandidateOutcome
)


@runtime_checkable
class RouteAudit(Protocol):
    """A mandatory, synchronous, durable audit sink (FR-033a). ``record`` MUST make
    the event durable before returning; raising is never swallowed (see
    ``RouteAuditError``).

    **Collision semantics (spec-025 maintainer review F2).** Every event's
    ``event_id`` is derived from ``route_id`` alone (plus, for candidate events,
    ``candidate_index`` + kind) — NOT from the event's other fields. So a retried
    ``route_chat(route_id="fixed")`` that re-selects could, in principle, produce a
    DIFFERENT chain/candidate under the SAME ``event_id``. ``record`` MUST
    therefore implement:

    - a ``record(event)`` call for an ``event_id`` that is ALREADY durably
      recorded with a BYTE-IDENTICAL canonical payload (all fields equal) is an
      IDEMPOTENT SUCCESS — no duplicate is stored and no error is raised;
    - a ``record(event)`` call for an ``event_id`` that is already durably
      recorded with a DIFFERENT payload is an INTEGRITY VIOLATION — the sink
      MUST raise. ``emit_audit`` normalizes ANY such exception to
      ``RouteAuditError`` (route-fatal), so conflicting payloads under the same
      ``event_id`` are NEVER silently accepted as a duplicate.

    A genuinely reproducible retry therefore needs the caller to re-inject the
    ORIGINAL ``snapshot=`` (``route_chat`` already supports this seam) so
    re-``select``ion yields the identical chain/candidates and every event's
    payload matches byte-for-byte. Side-effect idempotency (never re-invoking the
    backend for an already-dispatched candidate) is provided ONLY by
    ``claim_dispatch`` below — a plain, idempotent ``record`` is NOT sufficient
    for that: the caller cannot tell a newly-persisted start from an
    already-persisted one from ``record``'s return value (``None`` either way), so
    it cannot gate a side effect. A durable resume-from-cached-result path (return
    the PREVIOUSLY-recorded event/response so orchestration resumes rather than
    merely refuses to re-dispatch) would need a future lookup method and is out of
    scope for slice 0 — slice 0's guarantee is "never re-dispatch", NOT "resume
    the prior result".
    """

    def record(self, event: RouteAuditEvent) -> None: ...

    def claim_dispatch(self, event: DispatchStarted) -> bool:
        """ATOMICALLY claim the dispatch boundary for ``event.event_id`` AND
        durably record the ``DispatchStarted``. Returns:

        - ``True``  — FIRST claim: this caller now OWNS the dispatch (invoke the
          backend);
        - ``False`` — a ``DispatchStarted`` with this ``event_id`` was ALREADY
          durably recorded with a BYTE-IDENTICAL payload (a legitimate replay): the
          caller MUST NOT invoke the backend.

        MUST be atomic under CONCURRENT workers sharing a ``route_id`` — exactly
        one claimant gets ``True`` (a compare-and-swap / unique-insert, not a
        read-then-write). An idempotent ``record`` append is NOT sufficient: the
        caller cannot tell a newly-persisted start from an existing one, so a
        plain ``record`` cannot gate a side effect.

        **Collision semantics (finding #2), mirroring ``record`` above.** ``False``
        is returned ONLY when the already-recorded ``DispatchStarted`` payload is
        byte-identical. A claim for an ``event_id`` already recorded with a
        DIFFERENT payload (e.g. a different ``reservation_id`` — a conflicting
        dispatch masquerading as a replay) is an INTEGRITY VIOLATION and MUST RAISE
        (→ route-fatal ``RouteAuditError`` via the caller); it MUST NEVER be
        silently swallowed as a ``False`` replay. A sink infrastructure failure
        likewise RAISES — distinct from a ``False`` replay result."""
        ...


def emit_audit(route_audit: RouteAudit | None, event: RouteAuditEvent) -> None:
    """Emit one mandatory audit event. A ``None`` sink is a no-op. A sink exception
    is NEVER swallowed: a ``RouteAuditError`` propagates as-is; ANY other exception
    is normalized to ``RouteAuditError`` — so callers in BOTH ``route_chat`` and
    ``execute`` get ONE dependable failure type, distinct from ``ModelUnavailable``/
    ``ChainExhausted`` (F4). This is the SINGLE audit-emit path (Constitution I)."""
    if route_audit is None:
        return
    try:
        route_audit.record(event)
    except RouteAuditError:
        raise
    except Exception as exc:  # mandatory sink: surface, never swallow
        raise RouteAuditError(f"route_audit.record({type(event).__name__}) failed: {exc}") from exc
