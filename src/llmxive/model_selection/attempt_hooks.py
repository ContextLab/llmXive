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

This module is pure types (no I/O, no networked imports), so it is safe to import
eagerly from the package root — unlike ``snapshot``/``route``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


class RouteAuditError(RuntimeError):
    """A mandatory ``RouteAudit.record`` call failed. Route-fatal when raised
    pre-dispatch: it ABORTS the logical route call and NEVER advances to another
    candidate (an audit outage must not silently change which model executes).
    Distinct from ``ModelUnavailable`` (nothing eligible) and ``ChainExhausted``
    (the chain ran, none succeeded), so it does not trigger the proposal reroute."""


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
    """Emitted once after ``select`` succeeds, before any dispatch."""

    snapshot_digest: str
    selection_policy_version: int
    resolved_at: str
    explanation: tuple[str, ...]
    candidate_model_ids: tuple[str, ...]


@dataclass(frozen=True)
class SelectionFailure:
    """Emitted when ``select`` raises ``ModelUnavailable`` (so the failed first leg
    of the proposal reroute is auditable). Carries the KNOWN raw failure only — no
    causal claim (FR-002/F3)."""

    exception_type: str
    message: str
    requirement_digest: str
    snapshot_provenance: str


@dataclass(frozen=True)
class ReservationOpened:
    """Emitted once per paid candidate whose Attempt + 026 reservations both opened."""

    reservation_id: str
    model_id: str
    reserved_credits: float


@dataclass(frozen=True)
class DispatchStarted:
    """Emitted (durably) immediately BEFORE the backend call for a candidate."""

    model_id: str
    reservation_id: str | None


@dataclass(frozen=True)
class DispatchCompleted:
    """Emitted immediately AFTER a successful backend call for a candidate."""

    model_id: str
    reservation_id: str | None


@dataclass(frozen=True)
class DispatchUnknown:
    """NOT emitted by ``execute``. The lane's reconciler produces this from a
    durable ``DispatchStarted`` with no matching ``DispatchCompleted`` (a crash
    between). Defined here so the lane and the chokepoint share one event vocabulary."""

    model_id: str
    reservation_id: str | None


@dataclass(frozen=True)
class CandidateOutcome:
    """Emitted once per candidate terminal disposition."""

    model_id: str
    outcome: str  # "success" | "skip" | "advance" | "abort"
    reason: str


RouteAuditEvent = (
    ChainResolved
    | SelectionFailure
    | ReservationOpened
    | DispatchStarted
    | DispatchCompleted
    | DispatchUnknown
    | CandidateOutcome
)


@runtime_checkable
class RouteAudit(Protocol):
    """A mandatory, synchronous, durable audit sink (FR-033a). ``record`` MUST make
    the event durable before returning; raising is never swallowed (see
    ``RouteAuditError``)."""

    def record(self, event: RouteAuditEvent) -> None: ...
