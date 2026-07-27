"""The Attempt-scoped credit ledger (FR-033) — the concrete lane ``ReservationAuthority``.
An event-sourced projection over the per-Problem stream's ``AttemptCredit*`` (+ the
reconcile-driving ``DispatchUnknown``) events, enforcing a fail-closed transition matrix."""

from __future__ import annotations

from dataclasses import dataclass, replace

from llmxive.self_improvement.events import Event, payload_field

STATE_OPEN, STATE_RETAINED, STATE_RECONCILED, STATE_RELEASED = (
    "open", "retained", "reconciled", "released",
)
#: A reservation in any of these states still counts against the Attempt's budget. Only a
#: RELEASED one gives its credits back — and only from ``open``, because a reservation whose
#: call was dispatched has already committed real spend.
COUNTING_STATES = frozenset({STATE_OPEN, STATE_RETAINED, STATE_RECONCILED})

#: event_type → {from_state: to_state}. Hoisted to module scope because it IS the policy:
#: the legal edges of the money state machine, readable in one place rather than rebuilt
#: per event inside the fold. ``DispatchUnknown`` is the only self-edge — reconciliation
#: may observe the same unknown dispatch more than once, and the second observation must
#: not be an error (this is the atomic reconcile effect).
_TRANSITIONS: dict[str, dict[str, str]] = {
    "AttemptCreditRetained": {STATE_OPEN: STATE_RETAINED},
    "AttemptCreditReleased": {STATE_OPEN: STATE_RELEASED},
    "AttemptCreditReconciled": {STATE_RETAINED: STATE_RECONCILED},
    "DispatchUnknown": {STATE_OPEN: STATE_RETAINED, STATE_RETAINED: STATE_RETAINED},
}


@dataclass(frozen=True)
class AttemptReservation:
    reservation_id: str
    call_id: str
    reserved_credits: float
    state: str


def project_reservations(events: list[Event], attempt_id: str) -> dict[str, AttemptReservation]:
    """Fold one Attempt's reservations, enforcing the legal transition matrix.

    This projection is the authority on how much of an Attempt's budget is committed, so
    an illegal history RAISES rather than resolving to a plausible number: a transition for
    an unknown reservation, a duplicate reserve, or an edge outside :data:`_TRANSITIONS`
    (``released → retained``, anything out of ``reconciled``) all fail closed."""
    out: dict[str, AttemptReservation] = {}
    for e in events:
        if e.attempt_id != attempt_id:
            continue
        if e.event_type == "AttemptCreditReserved":
            rid = str(payload_field(e, "reservation_id"))
            if rid in out:
                raise ValueError(f"illegal duplicate AttemptCreditReserved for {rid!r}")
            out[rid] = AttemptReservation(rid, str(payload_field(e, "call_id")),
                                          float(payload_field(e, "reserved_credits")), STATE_OPEN)
            continue
        transitions = _TRANSITIONS.get(e.event_type)
        if transitions is None:
            continue  # not a reservation-affecting event (audit/other)
        if e.event_type == "DispatchUnknown":
            # The ONLY type whose reservation_id is legitimately absent: a free candidate
            # spends nothing, so its unknown dispatch has no reservation to retain.
            raw_rid = e.payload.get("reservation_id") if isinstance(e.payload, dict) else None
            if raw_rid is None:
                continue
        else:
            # For a credit transition, a missing id is malformed, not optional. Skipping it
            # would leave a released reservation counting against the budget forever.
            raw_rid = payload_field(e, "reservation_id")
        rid = str(raw_rid)
        if rid not in out:
            raise ValueError(f"illegal {e.event_type} for unknown reservation {rid!r}")
        cur = out[rid].state
        if cur not in transitions:
            raise ValueError(f"illegal transition {e.event_type} from {cur!r} for {rid!r}")
        out[rid] = replace(out[rid], state=transitions[cur])
    return out


def counting_total(reservations: dict[str, AttemptReservation]) -> float:
    return sum(r.reserved_credits for r in reservations.values() if r.state in COUNTING_STATES)


__all__ = [
    "COUNTING_STATES",
    "STATE_OPEN",
    "STATE_RECONCILED",
    "STATE_RELEASED",
    "STATE_RETAINED",
    "AttemptReservation",
    "counting_total",
    "project_reservations",
]
