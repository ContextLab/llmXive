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
    coord_event,
    coordinator_event_id,
    payload_field,
)
from llmxive.self_improvement.lane_log import LaneLogConfig, append, read
from llmxive.self_improvement.pairing import LaneInconsistent

_COORDINATOR_TYPES = {"ClaimAcquired", "ClaimReleased", "MonitorStarted", "PromotionEnabledSet"}


@dataclass(frozen=True)
class ClaimTerms:
    """The policy a claim was granted UNDER, recorded on the claim itself.

    Read by any later reclaimer from the ``ClaimGranted`` payload rather than from live
    policy, so editing the Policy Contract while a run holds the lane cannot retroactively
    expire it. Same discipline as ``bind_attempt_config``."""

    claim_expiry_s: int
    max_claim_hold_time_s: int
    max_clock_skew_s: int
    policy_version: int

    def as_payload(self) -> dict[str, int]:
        """The four terms as payload fields. BOTH halves of a claim embed the result of ONE
        call, so they cannot drift."""
        return {"claim_expiry_s": self.claim_expiry_s,
                "max_claim_hold_time_s": self.max_claim_hold_time_s,
                "max_clock_skew_s": self.max_clock_skew_s,
                "policy_version": self.policy_version}

    @classmethod
    def from_payload(cls, event: Event) -> ClaimTerms:
        """The terms a stored claim was granted under — from the RECORD, never from live
        policy. This direction is the one that carries the guarantee: a reclaimer deciding
        whether a holder has expired must use the holder's terms, not today's."""
        return cls(*(payload_field(event, f) for f in (
            "claim_expiry_s", "max_claim_hold_time_s", "max_clock_skew_s",
            "policy_version")))


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

    #: The FENCING TOKEN (FR-035), incremented by every ``ClaimAcquired`` and NEVER reset —
    #: a reset makes two different claims indistinguishable, which is the one thing a
    #: fencing token exists to prevent. A release does not bump it: a generation identifies
    #: a CLAIM and a released lane holds none, so the next ``ClaimAcquired`` takes the next
    #: number either way, and a stale worker at generation *g* is already defeated by "the
    #: lane is not held by me" before any generation is compared.
    #:
    #: This is the counter's CURRENT value. It cannot answer a question about a PAST claim —
    #: see :attr:`ClaimOutcome.generation`, which reads that claim's own record instead.
    claim_generation: int = 0


EMPTY_COORDINATOR = LaneCoordinator(0, None, None, (), False, None, 0, 0)


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

    Note the two TIME FRAMES on one record, and that this is deliberate: ``acquired`` and
    ``owner_*`` are about NOW, while ``generation`` and ``created`` are about THIS CALL's
    claim. A replay of a finished claim reports somebody else as the owner and still reports
    its own generation, because those are answers to different questions."""

    acquired: bool
    owner_problem_id: str | None
    owner_attempt_id: str | None
    coordinator: LaneCoordinator

    #: The generation of the claim THIS call concerns, read from its own ``ClaimAcquired``
    #: record. NOT :attr:`LaneCoordinator.claim_generation`, which is the counter's current
    #: value: after generation 1 was released and generation 2 granted elsewhere, a replay
    #: of the generation-1 claim must still report 1. The counter cannot answer a question
    #: about a past claim, and answering it from the counter is how a stale worker would be
    #: handed a fencing token that is not its own.
    generation: int

    #: True iff THIS call wrote the records. False for an idempotent replay — including a
    #: retry after a lost acknowledgement, which is the normal recovery path and must be
    #: distinguishable from a fresh grant by callers that log or meter claims.
    created: bool


def _outcome(coordinator: LaneCoordinator, problem_id: str, attempt_id: str, *,
             generation: int, created: bool) -> ClaimOutcome:
    """Both past-tense fields are passed EXPLICITLY rather than derived here: there is
    exactly one place each is known — the transaction's own result, and the claim's own
    event pair — and a helper that guessed would be guessing about the past."""
    owner = (coordinator.active_problem_id, coordinator.active_attempt_id)
    return ClaimOutcome(
        acquired=owner == (problem_id, attempt_id),
        owner_problem_id=owner[0], owner_attempt_id=owner[1], coordinator=coordinator,
        generation=generation, created=created,
    )


def _acquired_for(coordinator_events: list[Event], problem_id: str,
                  attempt_id: str) -> Event:
    """The ``ClaimAcquired`` of THIS pair's claim, found by derived id.

    There is at most one per ``(problem_id, attempt_id)`` — the id is derived from exactly
    those two, and the table forbids re-claiming an Attempt — so this is unambiguous rather
    than "the most recent match".

    Note the asymmetry with the grant, which is NOT locatable this way: the grant's key
    carries the lane revision it was granted at (`(attempt_id,"claim",lane_revision)`), and
    by the time anyone replays, the coordinator's revision has moved — not least because
    this very ``ClaimAcquired`` landed. The coordinator half is the anchor precisely because
    its key has no variable component."""
    acquired_id = coordinator_event_id("ClaimAcquired", problem_id, attempt_id)
    acquired = next((e for e in coordinator_events if e.event_id == acquired_id), None)
    if acquired is None:
        raise LaneInconsistent(
            f"no ClaimAcquired for {problem_id}/{attempt_id}: a claim record is being "
            "reported on, so its grant must exist")
    return acquired


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
            # ONLY here. Every other event leaves the counter alone, including the release:
            # see `LaneCoordinator.claim_generation`.
            c = replace(c, active_problem_id=payload_field(e, "problem_id"),
                        active_attempt_id=payload_field(e, "attempt_id"),
                        claim_generation=c.claim_generation + 1)
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


def _already_landed(events: list[Event], event_id: str) -> bool:
    return any(e.event_id == event_id for e in events)


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
    event = coord_event("ClaimReleased", problem_id=problem_id, attempt_id=attempt_id,
                        payload={"problem_id": problem_id, "attempt_id": attempt_id},
                        actor=actor, timestamp=timestamp)

    def _owns_or_landed(evs: list[Event]) -> tuple[bool, str]:
        if _already_landed(evs, event.event_id):
            return (True, "")  # this exact release already landed → idempotent
        c = project_coordinator(evs)
        owns = (c.active_problem_id, c.active_attempt_id) == (problem_id, attempt_id)
        return (owns, "" if owns else
                f"release owner mismatch: active={c.active_problem_id!r}/"
                f"{c.active_attempt_id!r}, releasing {problem_id!r}/{attempt_id!r}")

    result = append(repo, event, expected_revision=revision,
                    precondition=_owns_or_landed, config=config)
    coordinator_events = read(repo, COORDINATOR_STREAM, config=config)
    # The generation of the claim being RELEASED, from that claim's own record. Not
    # `project_coordinator(...).claim_generation`: after this release the lane may already
    # have been re-granted, and the counter would then hand back the NEXT holder's token —
    # to a caller asking about its own, finished claim. `ClaimReleased` carries no
    # generation of its own (one owner for the number), so the claim's `ClaimAcquired` is
    # the only place the answer exists. `created` is False on the idempotent path, which is
    # what a delayed duplicate release must report.
    return _outcome(project_coordinator(coordinator_events), problem_id, attempt_id,
                    generation=payload_field(
                        _acquired_for(coordinator_events, problem_id, attempt_id),
                        "claim_generation"),
                    created=result.created)


__all__ = [
    "EMPTY_COORDINATOR",
    "ClaimOutcome",
    "LaneCoordinator",
    "cas_release",
    "project_coordinator",
]
