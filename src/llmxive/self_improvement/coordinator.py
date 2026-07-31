"""The singleton LaneCoordinator (FR-007): a projection over the coordinator stream
that serializes the pre-merge pipeline, plus its ownership-checked CAS transitions
(FR-008). Slice 1A delivers the projection + claim/release; the label/comment side
effect (US2) is a later slice."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from llmxive.self_improvement.events import (
    COORDINATOR_STREAM,
    Event,
    derive_event_id,
    payload_field,
)
from llmxive.self_improvement.lane_log import LaneLogConfig, append, read

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


@dataclass(frozen=True)
class ClaimOutcome:
    """What a claim/release call ACTUALLY tells you: who holds the lane now.

    Returned instead of a bare projection because "the call did not raise" is not an
    ownership signal (spec 025 rev 22): both CAS entry points short-circuit when their own
    event already landed, so a replay that arrives after the lane was released and
    re-granted returns NORMALLY while somebody else owns the claim. Handing back a
    ``LaneCoordinator`` made every caller re-derive ownership by comparing projection
    fields — exactly the reconstruction a safety-critical lifecycle should not repeat at
    each call site, and exactly the misuse FR-035 makes routine by turning re-grants
    (``ClaimExpired``) into an ordinary event rather than a rarity.

    ``acquired`` answers the only question callers actually have: does the
    ``(problem_id, attempt_id)`` I named hold the lane now? It is therefore False after a
    successful release, and False for a superseded replay.

    The FR-035 fencing token (``claim_generation``) belongs on this record and joins it
    with that slice; it is deliberately absent rather than faked, because the coordinator
    stream does not yet carry generations."""

    acquired: bool
    owner_problem_id: str | None
    owner_attempt_id: str | None
    coordinator: LaneCoordinator


def _outcome(coordinator: LaneCoordinator, problem_id: str, attempt_id: str) -> ClaimOutcome:
    owner = (coordinator.active_problem_id, coordinator.active_attempt_id)
    return ClaimOutcome(
        acquired=owner == (problem_id, attempt_id),
        owner_problem_id=owner[0], owner_attempt_id=owner[1], coordinator=coordinator,
    )


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
            c = replace(c, active_problem_id=payload_field(e, "problem_id"),
                        active_attempt_id=payload_field(e, "attempt_id"))
        elif e.event_type == "ClaimReleased":
            if c.active_problem_id is None:  # only active → idle
                raise ValueError("illegal transition ClaimReleased while idle")
            if (c.active_problem_id, c.active_attempt_id) != (
                payload_field(e, "problem_id"), payload_field(e, "attempt_id")
            ):
                raise ValueError("illegal transition ClaimReleased by a non-owner")
            c = replace(c, active_problem_id=None, active_attempt_id=None)
        elif e.event_type == "MonitorStarted":
            c = replace(c, monitored_attempts=(*c.monitored_attempts, payload_field(e, "attempt_id")))
        elif e.event_type == "PromotionEnabledSet":
            enabled = payload_field(e, "promotion_enabled")
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


def _coord_event(event_type: str, idem: tuple[str, ...], payload: dict, actor: str,
                 timestamp: str, attempt_id: str) -> Event:
    """One coordinator event with a DETERMINISTIC id, so a re-invoked operation rebuilds
    the same event rather than minting a second record of the same decision.

    The revision anchors and ``seq`` are deliberately left unset: the store stamps all of
    them inside the CAS from the verified parent (see ``lane_log._finalize``), and a value
    fixed out here would be a guess about a revision we have not yet won."""
    return Event(
        event_id=derive_event_id(COORDINATOR_STREAM, "\x00".join(idem)), event_type=event_type,
        problem_id=COORDINATOR_STREAM, actor=actor, payload=payload, timestamp=timestamp,
        attempt_id=attempt_id,
    )


def _already_landed(events: list[Event], event_id: str) -> bool:
    return any(e.event_id == event_id for e in events)


def cas_claim(repo: Path, *, problem_id: str, attempt_id: str, actor: str, timestamp: str,
              config: LaneLogConfig | None = None) -> ClaimOutcome:
    """Take the lane's singleton claim for ``(problem_id, attempt_id)``, or raise
    :class:`LaneRevisionConflict` if another Problem holds it (or the lane revision moved
    under us — the caller recomputes and retries or yields; it NEVER forces).

    Re-invoking with the same pair is idempotent: the event id is derived from
    ``("claim", problem_id, attempt_id)``, so a retry after a lost acknowledgement finds
    its own record and does not append a second claim. That rests on Attempt ids being
    single-use, which spec 025 guarantees — a crashed Attempt is a FAILED Attempt and its
    successor gets a new id.

    **Returning without raising does NOT mean you hold the lane** — check
    :attr:`ClaimOutcome.acquired`, which is the whole reason this returns an outcome rather
    than a projection. The idempotency branch asks "did THIS event already land", not "do I
    own the claim now", so a replay arriving after the claim was released and the lane
    re-granted appends nothing and returns ``acquired=False`` with ``owner_*`` naming the
    Attempt that actually holds it. Pinned by
    ``test_a_replayed_claim_returns_successfully_while_someone_else_owns_the_lane``, and
    load-bearing under spec 025 FR-035, where ``ClaimExpired`` makes re-granting routine."""
    events = read(repo, COORDINATOR_STREAM, config=config)
    revision = project_coordinator(events).lane_revision
    event = _coord_event("ClaimAcquired", ("claim", problem_id, attempt_id),
                         {"problem_id": problem_id, "attempt_id": attempt_id},
                         actor, timestamp, attempt_id)

    def _idle_or_landed(evs: list[Event]) -> tuple[bool, str]:
        if _already_landed(evs, event.event_id):
            return (True, "")  # this exact claim already landed → idempotent
        active = project_coordinator(evs).active_problem_id
        return (active is None, "" if active is None else f"lane occupied by {active!r}")

    append(repo, event, expected_revision=revision, precondition=_idle_or_landed, config=config)
    return _outcome(project_coordinator(read(repo, COORDINATOR_STREAM, config=config)),
                    problem_id, attempt_id)


def cas_release(repo: Path, *, problem_id: str, attempt_id: str, actor: str, timestamp: str,
                config: LaneLogConfig | None = None) -> ClaimOutcome:
    """Release the lane's claim, or raise :class:`LaneRevisionConflict` if
    ``(problem_id, attempt_id)`` does not own it.

    The ownership check is what stops a DELAYED release from clearing someone else's
    claim: a caller that still believes it holds the lane cannot evict the Attempt that
    actually does. A release whose own record already landed is idempotent — it is
    reporting a fact, not requesting a change, so it neither appends a second record nor
    fails.

    Returns the same :class:`ClaimOutcome` as :func:`cas_claim`, read the same way:
    ``acquired`` is False once you have released (you no longer hold the lane), and
    ``owner_*`` names whoever holds it now — which, after a delayed duplicate release, is
    another Attempt entirely."""
    events = read(repo, COORDINATOR_STREAM, config=config)
    revision = project_coordinator(events).lane_revision
    event = _coord_event("ClaimReleased", ("release", problem_id, attempt_id),
                         {"problem_id": problem_id, "attempt_id": attempt_id},
                         actor, timestamp, attempt_id)

    def _owns_or_landed(evs: list[Event]) -> tuple[bool, str]:
        if _already_landed(evs, event.event_id):
            return (True, "")  # this exact release already landed → idempotent
        c = project_coordinator(evs)
        owns = (c.active_problem_id, c.active_attempt_id) == (problem_id, attempt_id)
        return (owns, "" if owns else
                f"release owner mismatch: active={c.active_problem_id!r}/"
                f"{c.active_attempt_id!r}, releasing {problem_id!r}/{attempt_id!r}")

    append(repo, event, expected_revision=revision, precondition=_owns_or_landed, config=config)
    return _outcome(project_coordinator(read(repo, COORDINATOR_STREAM, config=config)),
                    problem_id, attempt_id)


__all__ = [
    "EMPTY_COORDINATOR",
    "ClaimOutcome",
    "LaneCoordinator",
    "cas_claim",
    "cas_release",
    "project_coordinator",
]
