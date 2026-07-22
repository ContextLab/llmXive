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
        for an ordinary budget denial."""

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
    ``RouteAuditError``)."""

    def record(self, event: RouteAuditEvent) -> None: ...


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
