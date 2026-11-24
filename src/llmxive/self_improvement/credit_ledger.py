"""The Attempt-scoped credit ledger (FR-033) — the concrete lane ``ReservationAuthority``.
An event-sourced projection over the per-Problem stream's ``AttemptCredit*`` (+ the
reconcile-driving ``DispatchUnknown``) events, enforcing a fail-closed transition matrix."""

from __future__ import annotations

import math
import threading
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

from llmxive.self_improvement.attempt_config import bind_attempt_config
from llmxive.self_improvement.events import Event, derive_event_id, payload_field
from llmxive.self_improvement.lane_log import (
    LaneContention,
    LaneLogConfig,
    LaneRevisionConflict,
    append,
    read,
)

_MAX_RETRIES = 8

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


def _validated_amount(credits: float, reservation_id: str) -> float:
    """The amount, or ``ValueError`` — never ``False``.

    The admission test is ``counting_total + credits > budget``, so an unchecked amount
    defeats the cap in several different ways at once: a NEGATIVE one lowers
    ``counting_total`` and hands back budget already spent; ``nan`` makes every comparison
    False so the cap admits everything; ``inf`` and ``0`` describe a paid dispatch the cap
    can never meaningfully bind; and ``True`` is a perfectly good ``int`` to Python.

    It raises rather than returning ``False`` because ``False`` is the answer to an
    ordinary budget denial — a malformed request reported that way would read as a routine
    skip. ``allow_nan=False`` in the serializer would eventually reject nan/inf, but only
    as a SERIALIZATION error after admission was already decided, and it never catches a
    negative."""
    if (isinstance(credits, bool) or not isinstance(credits, (int, float))
            or not math.isfinite(credits) or credits <= 0):
        raise ValueError(
            f"reserved credits must be a finite number > 0, got {credits!r} "
            f"(reservation {reservation_id!r})"
        )
    return float(credits)


class AttemptCreditLedger:
    """One Attempt's paid-spend authority (FR-033), durable on the lane ref.

    **The ref-CAS is what makes overspending impossible**, in-process and across clones
    alike: the budget precondition is recomputed against FRESH events inside every CAS
    attempt, so a competitor that consumed the headroom flips the next recompute to a
    denial. Nothing else is load-bearing for that guarantee.

    The in-process ``Lock`` is a CONTENTION measure, not the safety mechanism. Without it
    a wide panel sharing one ledger instance would have every thread read, build, lose the
    ref-CAS, and retry — quadratic churn that can exhaust the retry budget and report
    ``LaneContention`` for what is really just crowding. Serializing them in-process is
    cheap and leaves the CAS to decide the outcome.
    """

    def __init__(self, *, repo: Path, problem_id: str, attempt_id: str,
                 attempt_budget_credits: float, call_ceiling: int, actor: str,
                 clock: Callable[[], str], config: LaneLogConfig | None = None) -> None:
        self._repo = repo
        self._problem_id = problem_id
        self._attempt_id = attempt_id
        self._actor = actor
        self._clock = clock
        self._config = config
        # The budget this ledger ENFORCES is the Attempt's DURABLE one, not whatever this
        # worker was constructed with. A different value fails closed HERE, before a single
        # reservation can be admitted against a silently-raised cap. One AttemptConfigured
        # record binds BOTH limits, which is why the call ceiling is passed in too — two
        # records could drift, and the drift would be invisible until a limit was exceeded.
        self._budget = bind_attempt_config(
            repo, problem_id=problem_id, attempt_id=attempt_id, call_ceiling=call_ceiling,
            attempt_budget_credits=attempt_budget_credits, actor=actor, clock=clock,
            config=config,
        ).attempt_budget_credits
        self._lock = threading.Lock()

    # -- helpers ---------------------------------------------------------------

    def _read(self) -> list[Event]:
        return read(self._repo, self._problem_id, config=self._config)

    def _event_id(self, idem: tuple[str, ...]) -> str:
        return derive_event_id(
            self._problem_id, "credit\x00" + "\x00".join((self._attempt_id, *idem))
        )

    def _event(self, event_type: str, event_id: str, payload: dict) -> Event:
        # The revision anchors and seq are left unset: the store stamps them inside the
        # CAS from the verified parent (lane_log._finalize).
        return Event(event_id=event_id, event_type=event_type, problem_id=self._problem_id,
                     actor=self._actor, payload=payload, timestamp=self._clock(),
                     attempt_id=self._attempt_id)

    # -- reserve ---------------------------------------------------------------

    def reserve(self, credits: float, *, reservation_id: str, call_id: str) -> bool:
        """Reserve ``credits`` against this Attempt's budget. ``True`` if reserved (or
        already reserved identically), ``False`` if the budget cannot cover it.

        Raises ``ValueError`` for a malformed amount or a reservation-id COLLISION (the
        same id presented with a different call or amount — an integrity violation, not a
        budget outcome), and ``LaneContention`` if the CAS never converged."""
        amount = _validated_amount(credits, reservation_id)
        with self._lock:
            for _ in range(_MAX_RETRIES):
                events = self._read()
                res = project_reservations(events, self._attempt_id)
                existing = res.get(reservation_id)
                if existing is not None:
                    if existing.call_id == call_id and existing.reserved_credits == amount:
                        return True  # idempotent replay of the same reservation
                    raise ValueError(
                        f"reservation {reservation_id!r} COLLISION — integrity violation: "
                        f"stored ({existing.call_id!r}, {existing.reserved_credits}) vs "
                        f"requested ({call_id!r}, {amount})"
                    )
                if counting_total(res) + amount > self._budget:
                    return False
                event = self._event(
                    "AttemptCreditReserved", self._event_id(("reserve", reservation_id)),
                    {"reservation_id": reservation_id, "call_id": call_id,
                     "reserved_credits": amount},
                )

                def _budget_ok(evs: list[Event], _rid=reservation_id) -> tuple[bool, str]:
                    # Re-checked against FRESH events every attempt: a competitor in
                    # another clone may have consumed the headroom since the read above.
                    fresh = project_reservations(evs, self._attempt_id)
                    if _rid in fresh:
                        return (True, "")  # already landed → idempotent
                    ok = counting_total(fresh) + amount <= self._budget
                    return (ok, "" if ok else "precondition: over budget")

                try:
                    # expected_revision=None ON PURPOSE. A revision CAS here would compare
                    # the length of the whole per-Problem stream, which also carries the
                    # audit sink's unconditional appends — so a busy route would spend
                    # reserve's retry budget losing to events that have no bearing on
                    # money, then raise LaneContention. The budget precondition above is
                    # the actual invariant, and it is recomputed inside every CAS attempt.
                    append(self._repo, event, expected_revision=None,
                           precondition=_budget_ok, config=self._config)
                    return True
                except LaneRevisionConflict:
                    continue  # the stream moved; recompute against the new tip
            raise LaneContention(f"reserve CAS did not converge for {reservation_id!r}")

    # -- transitions -----------------------------------------------------------

    def _cas_append(self, event_type: str, idem: tuple[str, ...], payload: dict) -> bool:
        """Append one state transition; ``True`` iff THIS call committed it.

        ``False`` covers both no-op cases — the reservation is no longer in a legal source
        state, or an identical transition was already committed — so a caller can report
        what it actually did rather than what merely ended up true. The legal sources are
        read from :data:`_TRANSITIONS`, the SAME table the projection folds, so the CAS can
        never admit an edge the projection would then reject."""
        rid = str(payload["reservation_id"])
        legal_sources = _TRANSITIONS[event_type]
        event_id = self._event_id(idem)
        for _ in range(_MAX_RETRIES):
            events = self._read()
            landed = any(e.event_id == event_id for e in events)
            current = project_reservations(events, self._attempt_id).get(rid)
            if not landed and (current is None or current.state not in legal_sources):
                # A concurrent LEGAL transition won (a release lost to a retain, say). The
                # method contract is idempotent, so this is a no-op — not a retry, and not
                # an error.
                return False
            event = self._event(event_type, event_id, payload)

            def _may_transition(evs: list[Event], _rid=rid) -> tuple[bool, str]:
                if any(x.event_id == event_id for x in evs):
                    return (True, "")  # this exact transition already landed → idempotent
                r = project_reservations(evs, self._attempt_id).get(_rid)
                if r is None:
                    return (False, f"unknown reservation {_rid!r}")
                ok = r.state in legal_sources
                return (ok, "" if ok else f"illegal transition from {r.state!r}")

            try:
                return append(self._repo, event, expected_revision=None,
                              precondition=_may_transition, config=self._config).created
            except LaneRevisionConflict:
                continue  # revision moved; the top-of-loop re-check decides no-op vs retry
        raise LaneContention(f"{event_type} CAS did not converge for {rid!r}")

    def _transition_if(self, reservation_id: str, event_type: str, idem_verb: str,
                       required: str) -> None:
        with self._lock:
            r = project_reservations(self._read(), self._attempt_id).get(reservation_id)
            if r is None or r.state != required:
                return
            self._cas_append(event_type, (idem_verb, reservation_id),
                             {"reservation_id": reservation_id})

    def release(self, reservation_id: str) -> None:
        """Give the credits back — legal ONLY from ``open``. A reservation whose call was
        dispatched has committed real spend, so a release against it is a no-op rather than
        a refund of money that left (FR-033). Absent or already-released is also a no-op."""
        self._transition_if(reservation_id, "AttemptCreditReleased", "release", STATE_OPEN)

    def mark_retained(self, reservation_id: str) -> None:
        """Keep the credits counted because the call was dispatched. Legal only from
        ``open``; anything else is a no-op."""
        self._transition_if(reservation_id, "AttemptCreditRetained", "retain", STATE_OPEN)

    # -- reconcile -------------------------------------------------------------

    def reconcile(self, reconciled_ledger_ids: set[str]) -> list[str]:
        """Move every ``retained`` reservation whose id settled upstream to ``reconciled``.

        The returned ids are the ones THIS call transitioned — not merely the ones that are
        now reconciled. Two concurrent identical reconciles therefore do not both claim the
        same id: the loser's append is an idempotent no-op and it reports nothing, so a
        consumer counting these as work performed counts each transition once.

        Idempotent: an already-reconciled id is not re-moved, and a retained id absent from
        the settled set is left alone."""
        with self._lock:
            res = project_reservations(self._read(), self._attempt_id)
            moved: list[str] = []
            for rid, r in res.items():
                if (r.state == STATE_RETAINED and rid in reconciled_ledger_ids
                        and self._cas_append("AttemptCreditReconciled", ("reconcile", rid),
                                             {"reservation_id": rid})):
                    moved.append(rid)
            return moved


__all__ = [
    "COUNTING_STATES",
    "STATE_OPEN",
    "STATE_RECONCILED",
    "STATE_RELEASED",
    "STATE_RETAINED",
    "AttemptCreditLedger",
    "AttemptReservation",
    "counting_total",
    "project_reservations",
]
