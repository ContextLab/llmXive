"""The singleton LaneCoordinator (FR-007): a projection over the coordinator stream
that serializes the pre-merge pipeline, plus its ownership-checked CAS transitions
(FR-008). Slice 1A delivers the projection + claim/release; the label/comment side
effect (US2) is a later slice."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from llmxive.self_improvement.events import Event

_COORDINATOR_TYPES = {"ClaimAcquired", "ClaimReleased", "MonitorStarted", "PromotionEnabledSet"}


@dataclass(frozen=True)
class LaneCoordinator:
    """The lane's singleton control record (FR-007). Never constructed from live state —
    always FOLDED from the coordinator stream, so a crashed runner recovers the same
    answer the previous one had."""

    lane_revision: int
    active_problem_id: str | None
    active_attempt_id: str | None
    monitored_attempts: tuple[str, ...]
    promotion_enabled: bool
    last_autonomous_merge_at: str | None
    policy_version: int


EMPTY_COORDINATOR = LaneCoordinator(0, None, None, (), False, None, 0)


def _field(event: Event, key: str) -> Any:
    """A payload field the fold acts on, as a ValueError rather than a KeyError.

    ``validate_lane_event`` already rejects a malformed coordinator payload at the write
    boundary; this is what keeps a hand-built or otherwise unvalidated ``Event`` from
    reaching the fold as a crash instead of a refusal."""
    try:
        return event.payload[key]
    except (KeyError, TypeError) as exc:
        raise ValueError(
            f"{event.event_type} event {event.event_id!r} payload lacks {key!r} — fail closed"
        ) from exc


def project_coordinator(events: list[Event]) -> LaneCoordinator:
    """Fold the coordinator stream, enforcing the LEGAL TRANSITION MATRIX. The projection
    is the recovery authority, so it fails closed on any illegal history — a
    stray/duplicate/out-of-order transition RAISES, it is never ignored."""
    c = EMPTY_COORDINATOR
    for position, e in enumerate(events):
        if e.seq != position:
            # seq is the lane's ordering authority and ORDER decides ownership here: a
            # list sorted any other way (by timestamp, say) would hand the claim to the
            # wrong Attempt. `lane_log.read` guarantees this; anything else must prove it.
            raise ValueError(
                f"coordinator events are out of order at position {position}: seq={e.seq!r}"
            )
        if e.event_type not in _COORDINATOR_TYPES:
            raise ValueError(f"unknown coordinator event {e.event_type!r} — fail closed")
        if e.event_type == "ClaimAcquired":
            if c.active_problem_id is not None:  # only idle → claimed
                raise ValueError(
                    f"illegal transition ClaimAcquired while active ({c.active_problem_id!r})"
                )
            c = replace(c, active_problem_id=_field(e, "problem_id"),
                        active_attempt_id=_field(e, "attempt_id"))
        elif e.event_type == "ClaimReleased":
            if c.active_problem_id is None:  # only active → idle
                raise ValueError("illegal transition ClaimReleased while idle")
            if (c.active_problem_id, c.active_attempt_id) != (
                _field(e, "problem_id"), _field(e, "attempt_id")
            ):
                raise ValueError("illegal transition ClaimReleased by a non-owner")
            c = replace(c, active_problem_id=None, active_attempt_id=None)
        elif e.event_type == "MonitorStarted":
            c = replace(c, monitored_attempts=(*c.monitored_attempts, _field(e, "attempt_id")))
        elif e.event_type == "PromotionEnabledSet":
            enabled = _field(e, "promotion_enabled")
            if not isinstance(enabled, bool):
                # NOT coerced: bool("false") is True, so coercion would open the
                # autonomous-merge gate a record was written to close.
                raise ValueError(
                    f"PromotionEnabledSet promotion_enabled must be a bool, got {enabled!r}"
                )
            c = replace(c, promotion_enabled=enabled,
                        policy_version=e.payload.get("policy_version", c.policy_version))
        c = replace(c, lane_revision=c.lane_revision + 1)
    return c


__all__ = ["EMPTY_COORDINATOR", "LaneCoordinator", "project_coordinator"]
