"""The Attempt's DURABLE safety limits.

An earlier design made the call SPEND durable but left the LIMIT in a constructor
argument — and a durable count checked against a mutable bound is not a durable cap: a
restarted worker, a config change, or a competing worker could simply present a bigger
ceiling. The same held for the credit budget, which guards money. Both now come from ONE
``AttemptConfigured`` event per Attempt: the first writer binds them under the ref-CAS, and
every later worker must present identical values or fail closed."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from llmxive.self_improvement.events import Event, derive_event_id, payload_field
from llmxive.self_improvement.lane_log import (
    LaneContention,
    LaneLogConfig,
    LaneRevisionConflict,
    append,
    read,
)

_MAX_RETRIES = 8


class AttemptConfigMismatch(ValueError):
    """A worker presented limits that differ from the Attempt's bound record (or the
    Attempt has none). Fail closed — never adopt the presented value, in EITHER direction:
    a larger ceiling defeats the cap, and a smaller one silently strands admitted work."""


@dataclass(frozen=True)
class AttemptConfig:
    attempt_id: str
    call_ceiling: int
    attempt_budget_credits: float


def _config_event_id(problem_id: str, attempt_id: str) -> str:
    return derive_event_id(problem_id, f"attempt-config\x00{attempt_id}")


def load_attempt_config(events: list[Event], attempt_id: str) -> AttemptConfig | None:
    """The Attempt's bound limits, or ``None`` if it was never configured. Two records for
    one Attempt is corruption — the deterministic ``event_id`` makes it unreachable through
    the CAS, so reaching it means the log was tampered with."""
    found = [e for e in events
             if e.event_type == "AttemptConfigured" and e.payload.get("attempt_id") == attempt_id]
    if not found:
        return None
    if len(found) > 1:
        raise AttemptConfigMismatch(
            f"attempt {attempt_id!r} has {len(found)} AttemptConfigured records — corrupt log"
        )
    return AttemptConfig(attempt_id, int(payload_field(found[0], "call_ceiling")),
                         float(payload_field(found[0], "attempt_budget_credits")))


def require_attempt_config(events: list[Event], attempt_id: str) -> AttemptConfig:
    """Fail-closed read: no lane work runs against limits nobody wrote down."""
    cfg = load_attempt_config(events, attempt_id)
    if cfg is None:
        raise AttemptConfigMismatch(f"attempt {attempt_id!r} is not configured — bind its "
                                    "limits before claiming calls or reserving credits")
    return cfg


def _compare(bound: AttemptConfig, presented: AttemptConfig) -> AttemptConfig:
    for field in ("call_ceiling", "attempt_budget_credits"):
        if getattr(bound, field) != getattr(presented, field):
            raise AttemptConfigMismatch(
                f"attempt {bound.attempt_id!r} is bound to {field}="
                f"{getattr(bound, field)!r}; this worker presented "
                f"{getattr(presented, field)!r} — refusing to rebind a safety limit"
            )
    return bound


def _validate_limits(call_ceiling: int, attempt_budget_credits: float) -> None:
    """Checked at the PUBLIC boundary as well as the event boundary: a caller deserves a
    clear refusal before anything is serialized, and neither check may be the only one —
    the event validator also guards a hand-written record."""
    if isinstance(call_ceiling, bool) or not isinstance(call_ceiling, int) or call_ceiling <= 0:
        raise ValueError(f"call_ceiling must be a positive int, got {call_ceiling!r}")
    if (isinstance(attempt_budget_credits, bool)
            or not isinstance(attempt_budget_credits, (int, float))):
        raise ValueError(f"attempt_budget_credits must be a number, got {attempt_budget_credits!r}")
    if not math.isfinite(attempt_budget_credits):
        # THE dangerous one: the ledger admits while `counting_total + credits > budget` is
        # False, and every comparison against NaN is False — a NaN budget admits everything.
        raise ValueError(
            f"attempt_budget_credits must be FINITE, got {attempt_budget_credits!r} — a "
            "non-finite budget disables the per-Attempt spend cap"
        )
    if attempt_budget_credits < 0:
        raise ValueError(
            f"attempt_budget_credits must be non-negative, got {attempt_budget_credits!r}"
        )


def bind_attempt_config(repo: Path, *, problem_id: str, attempt_id: str, call_ceiling: int,
                        attempt_budget_credits: float, actor: str, clock: Callable[[], str],
                        config: LaneLogConfig | None = None) -> AttemptConfig:
    """Bind (or verify) this Attempt's limits. Idempotent for identical values; raises
    ``AttemptConfigMismatch`` for any difference. Concurrent binders converge: exactly one
    CAS lands and the loser re-reads and compares."""
    _validate_limits(call_ceiling, attempt_budget_credits)
    presented = AttemptConfig(attempt_id, call_ceiling, float(attempt_budget_credits))
    for _ in range(_MAX_RETRIES):
        bound = load_attempt_config(read(repo, problem_id, config=config), attempt_id)
        if bound is not None:
            return _compare(bound, presented)
        event = Event(
            event_id=_config_event_id(problem_id, attempt_id),
            event_type="AttemptConfigured", problem_id=problem_id, actor=actor,
            payload={"attempt_id": attempt_id, "call_ceiling": call_ceiling,
                     "attempt_budget_credits": float(attempt_budget_credits)},
            timestamp=clock(), attempt_id=attempt_id,
        )

        def _unbound(evs: list[Event], _a=attempt_id, _p=presented) -> tuple[bool, str]:
            fresh = load_attempt_config(evs, _a)
            if fresh is None:
                return (True, "")
            # A competitor bound it between our read and this CAS attempt. Identical values
            # → idempotent success; different → deny, and the loop's re-read raises the
            # mismatch with the real bound values in the message.
            return (fresh == _p, "precondition: attempt already bound to different limits")

        try:
            append(repo, event, expected_revision=None, precondition=_unbound, config=config)
            return presented
        except LaneRevisionConflict:
            continue  # re-read: either adopt the identical record or raise mismatch
    raise LaneContention(f"attempt-config CAS did not converge for {attempt_id!r}")


__all__ = [
    "AttemptConfig",
    "AttemptConfigMismatch",
    "bind_attempt_config",
    "load_attempt_config",
    "require_attempt_config",
]
