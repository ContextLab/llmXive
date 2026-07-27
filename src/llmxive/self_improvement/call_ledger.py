"""Durable per-Attempt admission for logical ``route_chat`` invocations (Policy Contract
line 313).

The ceiling is scoped to the ATTEMPT, so it cannot live in a process's memory: a restart,
a retry on another runner, or a duplicate worker would each start at zero and let one
Attempt spend the ceiling repeatedly. Every logical call therefore CAS-appends a
``LaneCallClaimed`` event to the authoritative lane ref, and the count of those events IS
the spend. The claim key is deterministic, so a replayed operation returns the SAME
``route_id`` — which is also what lets slice-0's dispatch-idempotency gate recognize a
retried call instead of double-dispatching it (``route.py:291-293``)."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from llmxive.self_improvement.attempt_config import bind_attempt_config
from llmxive.self_improvement.events import (
    LEGS,
    Event,
    derive_event_id,
    derive_route_id,
    payload_field,
)
from llmxive.self_improvement.lane_log import (
    LaneContention,
    LaneLogConfig,
    LaneRevisionConflict,
    append,
    read,
)

_MAX_RETRIES = 8


class LaneCallCeilingExceeded(RuntimeError):
    """This Attempt has spent its logical-``route_chat`` ceiling (Policy Contract line
    313). The Attempt fails closed — never a silent extra call."""


@dataclass(frozen=True)
class CallClaim:
    operation_id: str
    leg: str
    route_id: str
    seq: int


def project_call_claims(events: list[Event], attempt_id: str) -> dict[tuple[str, str], CallClaim]:
    """The Attempt's admitted calls, keyed ``(operation_id, leg)``, in authoritative seq
    order. A duplicate key with a DIFFERENT route_id is corruption (the CAS makes it
    unreachable) → fail closed rather than silently pick one."""
    claims: dict[tuple[str, str], CallClaim] = {}
    for e in events:
        if e.event_type != "LaneCallClaimed" or e.payload.get("attempt_id") != attempt_id:
            continue
        key = (payload_field(e, "operation_id"), payload_field(e, "leg"))
        route_id = payload_field(e, "route_id")
        existing = claims.get(key)
        if existing is not None:
            if existing.route_id != route_id:
                raise ValueError(
                    f"corrupt call ledger: {key} claimed twice with different route ids "
                    f"({existing.route_id!r} then {route_id!r})"
                )
            continue
        claims[key] = CallClaim(key[0], key[1], route_id, int(e.seq))
    return claims


class LaneCallLedger:
    """Per-Attempt call admission on the lane ref.

    As with :class:`~llmxive.self_improvement.credit_ledger.AttemptCreditLedger`, the
    ref-CAS plus a ceiling precondition recomputed inside every attempt is what enforces the
    limit; the ``Lock`` keeps the panel's threads from burning the retry budget on churn."""

    def __init__(self, *, repo: Path, problem_id: str, attempt_id: str, call_ceiling: int,
                 attempt_budget_credits: float, actor: str, clock: Callable[[], str],
                 config: LaneLogConfig | None = None) -> None:
        self._repo, self._problem_id, self._attempt_id = repo, problem_id, attempt_id
        self._actor, self._clock, self._config = actor, clock, config
        # The ceiling this ledger ENFORCES is the Attempt's DURABLE one. Presenting a
        # different value raises AttemptConfigMismatch here, before a single call can be
        # admitted against a silently-raised cap. (bind_attempt_config validates positivity,
        # so there is no second local check — it lives in one place.)
        self._ceiling = bind_attempt_config(
            repo, problem_id=problem_id, attempt_id=attempt_id, call_ceiling=call_ceiling,
            attempt_budget_credits=attempt_budget_credits, actor=actor, clock=clock,
            config=config,
        ).call_ceiling
        self._lock = threading.Lock()  # the panel shares ONE instance across its threads

    def calls_used(self) -> int:
        """The DURABLE spend — read from the log, never a local counter."""
        return len(project_call_claims(read(self._repo, self._problem_id, config=self._config),
                                       self._attempt_id))

    def claim(self, *, operation_id: str, leg: str = "primary") -> str:
        """The ``route_id`` admitted for this logical call.

        Idempotent: an already-claimed ``(operation_id, leg)`` returns its recorded
        ``route_id`` and does NOT consume another call. Raises
        :class:`LaneCallCeilingExceeded` at the ceiling and ``LaneContention`` if the CAS
        never converged."""
        if leg not in LEGS:
            raise ValueError(f"unknown leg {leg!r} — must be one of {LEGS}")
        key = (operation_id, leg)
        route_id = derive_route_id(self._attempt_id, operation_id, leg)
        with self._lock:
            for _ in range(_MAX_RETRIES):
                events = read(self._repo, self._problem_id, config=self._config)
                claims = project_call_claims(events, self._attempt_id)
                landed = claims.get(key)
                if landed is not None:
                    return landed.route_id  # REPLAY — same id, not charged again
                if len(claims) >= self._ceiling:
                    raise LaneCallCeilingExceeded(
                        f"attempt {self._attempt_id!r} has spent its {self._ceiling} logical "
                        f"route_chat invocations (Policy Contract line 313) — failing closed"
                    )
                event = self._claim_event(operation_id, leg, route_id)

                def _admits(evs: list[Event], _k=key) -> tuple[bool, str]:
                    fresh = project_call_claims(evs, self._attempt_id)
                    if _k in fresh:
                        return (True, "")  # already landed → idempotent
                    return (len(fresh) < self._ceiling,
                            f"precondition: attempt at its {self._ceiling}-call ceiling")

                try:
                    # expected_revision=None for the same reason as the credit ledger: a
                    # revision CAS would compare the whole per-Problem stream, which also
                    # carries audit appends, so admission would lose its retry budget to
                    # events that have nothing to do with the ceiling. `_admits` is the
                    # invariant, recomputed inside every attempt.
                    append(self._repo, event, expected_revision=None, precondition=_admits,
                           config=self._config)
                    return route_id
                except LaneRevisionConflict:
                    # Lost the CAS to a competitor that just consumed a call. Re-read: the
                    # loop's pre-check then either finds our claim already landed, admits
                    # us, or raises LaneCallCeilingExceeded — so a ceiling loss surfaces as
                    # the CEILING error, never as contention.
                    continue
            raise LaneContention(f"call-claim CAS did not converge for {key}")

    def _claim_event(self, operation_id: str, leg: str, route_id: str) -> Event:
        return Event(
            event_id=derive_event_id(self._problem_id,
                                     f"call\x00{self._attempt_id}\x00{operation_id}\x00{leg}"),
            event_type="LaneCallClaimed", problem_id=self._problem_id, actor=self._actor,
            payload={"attempt_id": self._attempt_id, "operation_id": operation_id,
                     "leg": leg, "route_id": route_id, "call_ceiling": self._ceiling},
            timestamp=self._clock(), attempt_id=self._attempt_id,
        )


__all__ = [
    "CallClaim",
    "LaneCallCeilingExceeded",
    "LaneCallLedger",
    "project_call_claims",
]
