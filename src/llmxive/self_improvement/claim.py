"""Taking, holding, and losing the singleton lane (spec 025 slice 2, FR-035).

Everything here spans BOTH streams — the coordinator's ownership record and the claiming
Attempt's own timeline — so everything here sits above both.

**Why not `coordinator.py`.** Granting the lane is a transition in the Attempt table
(`proposal_verified → claimed`), so `cas_claim` must read the Attempt's state to refuse a
claim on an Attempt that is not verified. That is a `lifecycle` import, and `lifecycle`
already imports `coordinator` for the lane's ownership — putting the claim service in
`coordinator.py` makes that a cycle. The layering instead: `coordinator.py` owns the
coordinator STREAM and never imports `lifecycle`; `pairing.py` sits below both and knows
only whether a stored transaction is intact; this module sits above both and is the ONE
place a claim is taken, renewed, or reclaimed.

There is deliberately no second claim API. Slice 1A's coordinator-only `cas_claim` was
REPLACED rather than kept alongside this one: two ways to take the same lock is the
duplication Constitution I forbids, and the older one would be the unsafe path — it wrote
the coordinator half alone, which is a lane wedged behind an Attempt that never started.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.git_event_log import Seam
from llmxive.self_improvement.coordinator import (
    ClaimOutcome,
    ClaimTerms,
    _outcome,
    project_coordinator,
)
from llmxive.self_improvement.events import (
    COORDINATOR_STREAM,
    Event,
    coordinator_event_id,
    payload_field,
)
from llmxive.self_improvement.lane_log import (
    LaneLogConfig,
    append_many,
    events_by_commit,
    read,
)
from llmxive.self_improvement.lifecycle import (
    _BY_EVENT,
    AttemptState,
    IllegalTransition,
    project_attempt,
)
from llmxive.self_improvement.pairing import (
    LaneInconsistent,
    assert_member_identity,
    assert_partner_intact,
)

#: The fields a claim's two halves MUST agree on, because one construction wrote both.
#: Named once and shared by the write boundary's replay check and (Task 8's auditor) the
#: historical walk, so the two cannot come to hold different notions of a well-formed claim.
_CLAIM_PAIR_FIELDS = ("claim_generation", "lane_revision", "claim_expiry_s",
                      "max_claim_hold_time_s", "max_clock_skew_s", "policy_version")


def _granted_in(problem_events: list[Event], attempt_id: str) -> Event | None:
    """This Attempt's ``ClaimGranted``, located by TYPE rather than by derived id.

    The grant's key carries the lane revision it was granted at, and a replay cannot
    reconstruct that: the coordinator's revision has moved by then, not least because this
    claim's own ``ClaimAcquired`` landed. Re-deriving the id from CURRENT state would miss
    the stored grant and report a complete claim as half-present — turning the ordinary
    lost-acknowledgement retry into a hard `LaneInconsistent`.

    Locating by type is not a weaker identity, it is the underlying one: the TABLE forbids
    re-claiming an Attempt (`ClaimGranted` is legal only from `proposal_verified`, which is
    never re-entered), so at most one can exist. Anything else on this stream naming this
    Attempt is caught by `assert_member_identity` below."""
    grants = [e for e in problem_events
              if e.event_type == "ClaimGranted" and e.attempt_id == attempt_id]
    if len(grants) > 1:
        raise LaneInconsistent(
            f"{attempt_id!r} has {len(grants)} ClaimGranted records — the table allows one, "
            "so this history was not written by this path")
    return grants[0] if grants else None


def _validate_claim_pair(repo: Path, acquired: Event, granted: Event, problem_id: str,
                         attempt_id: str, *, config: LaneLogConfig | None = None) -> None:
    """Row 1's stored pair, checked BEFORE it is reused — through the shared check.

    A wrapper, not a second implementation: a claim pair IS a pairing, with ``ClaimGranted``
    on the Problem stream as the anchor and ``ClaimAcquired`` on the coordinator as the
    partner, sharing :data:`_CLAIM_PAIR_FIELDS` — so the write boundary and the auditor
    cannot come to hold two notions of what a well-formed claim is.

    Row 1 keeps its OWN half-presence logic in :func:`cas_claim` (a bidirectional check,
    which must also catch a lone ``ClaimAcquired``), and delegates only the both-present
    case here. That split is the reason this wrapper exists rather than a direct call."""
    assert_member_identity(granted, "ClaimGranted", problem_id, problem_id, attempt_id)
    assert_partner_intact(
        anchor=granted, partner=acquired,
        coordinator_event="ClaimAcquired", compare=_CLAIM_PAIR_FIELDS,
        commit_of=events_by_commit(repo, config=config),
        problem_id=problem_id, attempt_id=attempt_id)


def cas_claim(repo: Path, *, problem_id: str, attempt_id: str, actor: str,
              timestamp: str, terms: ClaimTerms,
              config: LaneLogConfig | None = None,
              _after_parent: Seam = None, _before_ref_update: Seam = None,
              _after_push: Seam = None) -> ClaimOutcome:
    """Take the singleton lane for ``(problem_id, attempt_id)`` and move that Attempt to
    ``claimed`` — ONE transaction over the coordinator and Problem subtrees.

    The two records are written together because a claim that exists on one stream and not
    the other is not a weaker claim, it is a corrupt one: a coordinator entry with no
    Attempt transition wedges the lane behind an Attempt that never started, and an Attempt
    transition with no coordinator entry lets a second runner claim the same lane.

    **Returning without raising does NOT mean you hold the lane** — read
    :attr:`ClaimOutcome.acquired`. A replay arriving after this claim was released and the
    lane re-granted appends nothing and reports the CURRENT owner, while still reporting its
    own generation."""
    coordinator_events = read(repo, COORDINATOR_STREAM, config=config)
    problem_events = read(repo, problem_id, config=config)
    current = project_coordinator(coordinator_events)
    acquired_id = coordinator_event_id("ClaimAcquired", problem_id, attempt_id)
    stored = (next((e for e in coordinator_events if e.event_id == acquired_id), None),
              _granted_in(problem_events, attempt_id))

    if all(stored):
        # A REPLAY reuses the STORED PAIR VERBATIM — generation, terms, timestamp, and
        # ACTOR. Two independent reasons, and the second is the one a first draft missed:
        #
        # (1) Recomputing `claim_generation + 1` builds a DIFFERENT body under the SAME id,
        #     which the append-only check rejects as a content violation — turning a
        #     harmless retry into a hard failure, and doing it only once the generation has
        #     advanced, which is exactly when a retry is most likely.
        # (2) `actor` is NOT in `lane_log._IDENTITY_EXCLUDE` (only `seq`, `timestamp` and
        #     the revision anchors are), so it IS part of an event's identity. Recovery
        #     routinely happens under a different trusted runner identity than the one that
        #     first wrote the claim, and rebuilding with the CURRENT caller's actor would
        #     make the cross-runner retry — the whole reason lost acknowledgements are
        #     survivable — fail append-only validation.
        #
        # Reusing them verbatim is why they must be VALIDATED here. `append_many` compares
        # each stored event against itself, so it is a tautology on this path: a pair whose
        # halves disagree — mismatched generation, terms edited by a hand repair, a grant
        # naming another Attempt, or two halves added by two DIFFERENT COMMITS — would
        # replay "successfully" and be reported as a live claim. `assert_lane_consistent`
        # would catch it eventually, but a direct `cas_claim` can return long before any
        # audit runs, and a corrupt claim is exactly the thing a caller must never be handed.
        acquired, granted = stored
        _validate_claim_pair(repo, acquired, granted, problem_id, attempt_id, config=config)
    elif any(stored):
        # Exactly one half present, which no transaction could have produced. Refuse here
        # rather than reconstructing the missing half from the surviving one — that would
        # "complete" a transaction that was never atomically started, which is precisely
        # what `append_transaction`'s partial-presence guard exists to prevent.
        raise LaneInconsistent(
            f"claim {problem_id}/{attempt_id} is half-present: "
            f"ClaimAcquired={'yes' if stored[0] else 'no'}, "
            f"ClaimGranted={'yes' if stored[1] else 'no'}")
    else:
        # ONE body, embedded in both halves, so they cannot drift. `lane_revision` is part
        # of the grant's idempotency key, which is why it is carried rather than left to the
        # envelope: the Attempt-side half's envelope records the PROBLEM revision.
        body = {"problem_id": problem_id, "attempt_id": attempt_id,
                "claim_generation": current.claim_generation + 1,
                "lane_revision": current.lane_revision, **terms.as_payload()}
        acquired = Event(
            event_id=acquired_id,
            event_type="ClaimAcquired", problem_id=COORDINATOR_STREAM, actor=actor,
            payload=body, timestamp=timestamp, attempt_id=attempt_id)
        granted = Event(
            # Through the ROW, the one derivation site for every Attempt transition's id.
            event_id=_BY_EVENT["ClaimGranted"].event_id(problem_id, attempt_id, body),
            event_type="ClaimGranted", problem_id=problem_id, actor=actor,
            payload=dict(body), timestamp=timestamp, attempt_id=attempt_id)

    def _free_and_verified(observed: dict[str, list[Event]]) -> tuple[bool, str]:
        if any(e.event_id == acquired.event_id for e in observed[COORDINATOR_STREAM]):
            return (True, "")                      # idempotent replay of THIS claim
        holder = project_coordinator(observed[COORDINATOR_STREAM])
        if holder.active_problem_id is not None:
            return (False, f"lane occupied by {holder.active_problem_id}/"
                           f"{holder.active_attempt_id}")
        history = [e for e in observed[problem_id] if e.attempt_id == attempt_id]
        if not history:
            return (False, f"{attempt_id!r} has no events — a claim is a TRANSITION")
        try:
            state = project_attempt(history).state
        except IllegalTransition as exc:  # a history we cannot trust → refuse to add to it
            return (False, f"unprojectable history: {exc}")
        if state is not AttemptState.PROPOSAL_VERIFIED:
            return (False, f"{attempt_id!r} is {state.value!r}, not proposal_verified")
        return (True, "")

    result = append_many(repo, [acquired, granted],
                         expected_revisions={COORDINATOR_STREAM: current.lane_revision,
                                             problem_id: len(problem_events)},
                         precondition=_free_and_verified, config=config,
                         _after_parent=_after_parent,
                         _before_ref_update=_before_ref_update, _after_push=_after_push)
    # Ownership comes from the CURRENT projection — "who holds the lane now" is a question
    # about now. Generation and `created` come from THIS transaction and its own event
    # pair, because they are questions about THIS claim, and after a release-and-regrant the
    # coordinator's counter cannot answer either one. Discarding `result` and re-deriving
    # both from the projection is how a replay would report `created=True` and somebody
    # else's generation.
    return _outcome(project_coordinator(read(repo, COORDINATOR_STREAM, config=config)),
                    problem_id, attempt_id,
                    generation=payload_field(acquired, "claim_generation"),
                    created=result.created)


__all__ = ["cas_claim"]
