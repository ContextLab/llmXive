"""The Attempt state machine (spec 025 Transition Table), declared ONCE as data.

The table is the contract. A function that re-encoded a row in an ``if`` chain would be a
second source of truth that can disagree with this one (Constitution I), so nothing below
branches on a specific state name — every decision is a lookup.

Attempt states are NOT Problem dispositions: ``cooldown`` is keyed by ``problem_id`` and
lives in :mod:`cooldown`. Collapsing them is how a Problem's rest gets misreported as an
Attempt's outcome."""

from __future__ import annotations

import enum
from collections import deque
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from llmxive.git_event_log import Seam
from llmxive.self_improvement.coordinator import project_coordinator
from llmxive.self_improvement.events import (
    COORDINATOR_STREAM,
    REVIEW_STAGES,
    Event,
    coord_event,
    derive_event_id,
    payload_field,
)
from llmxive.self_improvement.lane_log import LaneLogConfig, append_many, read
from llmxive.self_improvement.pairing import replayed_transaction


class IllegalTransition(ValueError):
    """The history is not something the machine could have produced. Always raised, never
    downgraded to a skip: a projection that tolerates an impossible history is a projection
    that cannot be used for recovery."""


class AttemptState(enum.StrEnum):
    PROPOSED = "proposed"
    PROPOSAL_VERIFIED = "proposal_verified"
    CLAIMED = "claimed"
    IMPLEMENTING = "implementing"
    PROMOTING = "promoting"
    PROMOTION_REQUESTED = "promotion_requested"
    MONITORING = "monitoring"
    REVERT_REQUESTED = "revert_requested"
    # --- terminals ---
    REJECTED = "rejected"
    REVIEW_ABORTED = "review_aborted"
    ATTEMPT_ABANDONED = "attempt_abandoned"
    IMPL_FAILED = "impl_failed"
    PUBLISH_FAILED = "publish_failed"
    TEST_FAILED = "test_failed"
    EVAL_FAILED = "eval_failed"
    UNSUPPORTED_SCOPE = "unsupported_scope"
    SUPERSEDED = "superseded"
    PROMOTION_ABORTED = "promotion_aborted"
    REVERTED = "reverted"
    RETAINED = "retained"
    CIRCUIT_BROKEN = "circuit_broken"


class ProblemDisposition(enum.StrEnum):
    """Per-PROBLEM, deliberately a separate namespace from :class:`AttemptState`."""

    ACTIVE = "active"
    COOLDOWN = "cooldown"


@dataclass(frozen=True)
class StateWitness:
    """A payload term that redundantly NAMES which of a multi-source transition's
    ``from_states`` the event was taken from.

    A witnessed field is checkable, and therefore must be checked. ``ReviewAborted`` is
    legal from `proposed` (where the PROPOSAL review runs) and from `implementing` (where
    the PATCH review runs), and its ``stage`` says which — so a ``stage="patch"`` abort
    recorded from `proposed` is a durable record asserting a review that provably never
    ran. The write boundary cannot catch it: ``_one_of`` sees a term from the legal
    vocabulary, and the state it disagrees with is not in the record. Only the fold, which
    knows the state the transition is LEAVING, can.

    ``by_state`` is a tuple of pairs rather than a mapping to keep :class:`Transition`
    hashable. It is exhaustive over ``from_states`` AND over the field's write-boundary
    vocabulary, both asserted at import by :func:`_validate_declarations` — a source state
    with no term would be unwitnessable, and a term no source state can produce is a term
    no writer could legally use."""

    field: str
    by_state: tuple[tuple[AttemptState, str], ...]

    def term(self, state: AttemptState | None) -> str | None:
        return next((term for s, term in self.by_state if s is state), None)

    @property
    def states(self) -> frozenset[AttemptState]:
        return frozenset(s for s, _ in self.by_state)

    @property
    def terms(self) -> frozenset[str]:
        return frozenset(term for _, term in self.by_state)


#: The write-boundary vocabulary each witnessed field is constrained to, named by the layer
#: that OWNS it. `_validate_declarations` asserts each witness covers its field's vocabulary
#: exactly, so the `_one_of` set and the state map cannot drift into disagreeing about which
#: terms exist.
_WITNESS_VOCABULARY: dict[str, frozenset[str]] = {"stage": REVIEW_STAGES}


@dataclass(frozen=True)
class Transition:
    event: str
    from_states: frozenset[AttemptState]
    to_state: AttemptState
    key_suffix: str                       # the idempotency key's 2nd element, per the spec
    coordinator_effects: tuple[str, ...]  # the spec table's † and ◇ markers
    #: Set only where the payload names its own source state; see :class:`StateWitness`.
    witness: StateWitness | None = None

    @property
    def terminal(self) -> bool:
        """DERIVED, never stored: a second field could disagree with ``to_state``, and the
        one place that must not have two answers is "may anything follow this?"."""
        return self.to_state in TERMINAL_STATES

    @property
    def releases_claim(self) -> bool:
        """Also derived — from the effect list that actually produces the release, so the
        predicate and the write can never disagree. Deliberately NOT a synonym for
        ``terminal``: ``PromotionObserved`` releases without ending the Attempt, and the
        monitoring-phase terminals end it without holding a claim to release."""
        return "ClaimReleased" in self.coordinator_effects


def _t(event: str, froms: tuple[AttemptState, ...], to: AttemptState, key: str,
       *, effects: tuple[str, ...] = (), witness: StateWitness | None = None) -> Transition:
    return Transition(event, frozenset(froms), to, key, effects, witness)


_RELEASES = ("ClaimReleased",)


S = AttemptState

TRANSITIONS: tuple[Transition, ...] = (
    _t("Proposed", (), S.PROPOSED, "proposed"),
    _t("ProposalVerified", (S.PROPOSED,), S.PROPOSAL_VERIFIED, "verified"),
    _t("Rejected", (S.PROPOSED, S.PROPOSAL_VERIFIED), S.REJECTED, "reject"),
    # `stage` is not free-form: `proposed` is where the proposal review runs and
    # `implementing` is where the patch review runs, so the source state DETERMINES it.
    _t("ReviewAborted", (S.PROPOSED, S.IMPLEMENTING), S.REVIEW_ABORTED, "reviewabort",
       effects=_RELEASES,
       witness=StateWitness("stage", ((S.PROPOSED, "proposal"), (S.IMPLEMENTING, "patch")))),
    _t("ClaimGranted", (S.PROPOSAL_VERIFIED,), S.CLAIMED, "claim"),
    _t("Implementing", (S.CLAIMED,), S.IMPLEMENTING, "impl"),
    _t("ImplementationFailed", (S.CLAIMED, S.IMPLEMENTING), S.IMPL_FAILED, "implfail",
       effects=_RELEASES),
    _t("PublishFailed", (S.IMPLEMENTING,), S.PUBLISH_FAILED, "pubfail", effects=_RELEASES),
    _t("TestingFailed", (S.IMPLEMENTING,), S.TEST_FAILED, "testfail", effects=_RELEASES),
    _t("EvaluationFailed", (S.IMPLEMENTING,), S.EVAL_FAILED, "evalfail", effects=_RELEASES),
    _t("ScopeUnsupported", (S.PROPOSAL_VERIFIED, S.CLAIMED, S.IMPLEMENTING),
       S.UNSUPPORTED_SCOPE, "unsupported", effects=_RELEASES),
    _t("FreshnessStale", (S.CLAIMED, S.IMPLEMENTING), S.SUPERSEDED, "stale",
       effects=_RELEASES),
    _t("EvaluationPassed", (S.IMPLEMENTING,), S.PROMOTING, "eval"),
    _t("PromotionRequested", (S.PROMOTING,), S.PROMOTION_REQUESTED, "promo-req"),
    # Matrix row 4. The claim ends here, not at a terminal: the merge has landed and the
    # monitoring window is unattended, so holding the singleton lane through it would block
    # every other Problem for the whole window. MonitorStarted precedes ClaimReleased
    # because BOTH require that this Attempt holds the lane: releasing first would leave
    # MonitorStarted with no owner to match, so it is MONITORSTARTED's ownership check —
    # not the release's — that rejects the reversed order.
    _t("PromotionObserved", (S.PROMOTION_REQUESTED,), S.MONITORING, "promo-obs",
       effects=("MonitorStarted", "ClaimReleased")),
    _t("PromotionAborted", (S.PROMOTION_REQUESTED,), S.PROMOTION_ABORTED, "promo-abort",
       effects=_RELEASES),
    _t("RevertRequested", (S.MONITORING,), S.REVERT_REQUESTED, "revert-req"),
    _t("RevertObserved", (S.REVERT_REQUESTED,), S.REVERTED, "revert-obs"),
    _t("RevertAborted", (S.REVERT_REQUESTED,), S.MONITORING, "revert-abort"),
    _t("Retained", (S.MONITORING,), S.RETAINED, "retain"),
    _t("BreakerTripped",
       (S.PROPOSED, S.PROPOSAL_VERIFIED, S.CLAIMED, S.IMPLEMENTING, S.PROMOTING,
        S.PROMOTION_REQUESTED), S.CIRCUIT_BROKEN, "breaker", effects=_RELEASES),
    # FR-035: the one terminal written by a DIFFERENT run than the one that abandoned it.
    _t("ClaimExpired",
       (S.CLAIMED, S.IMPLEMENTING, S.PROMOTING, S.PROMOTION_REQUESTED),
       S.ATTEMPT_ABANDONED, "claimexpired", effects=_RELEASES),
)

def _validate_declarations(transitions: tuple[Transition, ...]) -> None:
    """Refuse a malformed table AT IMPORT, not on the first history that trips over it.

    Takes the table as an argument so the check is itself testable: a rule enforced only
    over the one table that already satisfies it is a rule with no evidence it does
    anything. Called below with `TRANSITIONS`.

    A witness whose `by_state` disagrees with its row's `from_states` is the drift this
    exists to prevent — add a source state to a witnessed row and the fold would otherwise
    silently stop checking that state, which is exactly the hole being closed here."""
    for t in transitions:
        if t.witness is None:
            continue
        if not t.from_states:
            raise ValueError(
                f"{t.event}: a state witness on an opening transition witnesses nothing")
        if t.witness.states != t.from_states:
            raise ValueError(
                f"{t.event}: witness covers {sorted(s.value for s in t.witness.states)} "
                f"but the row is legal from {sorted(s.value for s in t.from_states)}")
        vocabulary = _WITNESS_VOCABULARY.get(t.witness.field)
        if vocabulary is None:
            raise ValueError(
                f"{t.event}: no write-boundary vocabulary declared for witnessed field "
                f"{t.witness.field!r} — the fold and `_one_of` would be unrelated checks")
        if t.witness.terms != vocabulary:
            raise ValueError(
                f"{t.event}: witness terms {sorted(t.witness.terms)} disagree with the "
                f"{t.witness.field!r} vocabulary {sorted(vocabulary)}")


_validate_declarations(TRANSITIONS)


TERMINAL_STATES: frozenset[AttemptState] = frozenset({
    S.REJECTED, S.REVIEW_ABORTED, S.ATTEMPT_ABANDONED, S.IMPL_FAILED, S.PUBLISH_FAILED,
    S.TEST_FAILED, S.EVAL_FAILED, S.UNSUPPORTED_SCOPE, S.SUPERSEDED, S.PROMOTION_ABORTED,
    S.REVERTED, S.RETAINED, S.CIRCUIT_BROKEN,
})

#: Counted toward the per-Problem QUALITY cap (M=3 → 30-day cooldown). The operational
#: terminals are deliberately absent: counting one would let a provider outage or a crashed
#: runner consume a Problem's quality budget, which FR-001 forbids.
COUNTED_TERMINALS: frozenset[AttemptState] = frozenset({
    S.IMPL_FAILED, S.PUBLISH_FAILED, S.TEST_FAILED, S.EVAL_FAILED, S.REVERTED,
})

#: Uncounted terminals that feed the OPERATIONAL streak instead (FR-034).
OPERATIONAL_TERMINALS: frozenset[AttemptState] = frozenset({
    S.REVIEW_ABORTED, S.ATTEMPT_ABANDONED,
})


def _claim_holding_states() -> frozenset[AttemptState]:
    """Every state an Attempt can occupy while STILL HOLDING the lane: reachable from
    ``claimed`` without crossing a transition that releases.

    Walked, not listed. A hand-written set goes stale exactly when a phase is inserted
    between `claimed` and the release — the only time it ever changes — and a comment
    calling a hand-written set "derived" is worse than no comment, because it tells the
    next reader not to check."""
    holding, queue = {S.CLAIMED}, deque([S.CLAIMED])
    while queue:
        state = queue.popleft()
        for t in TRANSITIONS:
            if state in t.from_states and not t.releases_claim and t.to_state not in holding:
                holding.add(t.to_state)
                queue.append(t.to_state)
    return frozenset(holding)


#: Consumed by `coordinator.assert_lane_consistent` (Task 8) to decide whether a held claim
#: agrees with its Attempt's own timeline, and whether a declared coordinator effect was
#: required at the point it would have been written.
CLAIM_HOLDING_STATES: frozenset[AttemptState] = _claim_holding_states()


def holds_claim(state: AttemptState | None) -> bool:
    """Does an Attempt in ``state`` hold the lane?

    The ONE reading of that question, and it has three callers that must never disagree:
    `lifecycle._claim_required` (does this transition owe the coordinator an event?),
    `coordinator.assert_lane_consistent`'s historical walk (was a partner required at this
    point?), and its active-projection check (is the current holder in a sane state?).
    `None` — an Attempt with no events yet — holds nothing."""
    return state in CLAIM_HOLDING_STATES


def released_claim(transition: Transition, state_before: AttemptState | None) -> bool:
    """Did this transition ACTUALLY emit the coordinator's ``ClaimReleased``?

    ``Transition.releases_claim`` is the ROW's declaration; emission is conditional on the
    Attempt holding the lane in the state the transition is LEAVING. The spec says so
    directly — the dagger marks "must not leave the lane occupied", not "always mutates the
    coordinator" — and three declared-release rows are reachable from non-holding states
    (`ReviewAborted` from `proposed`, `ScopeUnsupported` from `proposal_verified`,
    `BreakerTripped` from either), where there is nothing to release and the effect is
    correctly skipped.

    Reading the row alone is the exact false positive `assert_lane_consistent` case 12j
    exists to catch, one layer up: it reports a release that was never written, so a
    consumer reconciling the coordinator against it goes looking for a partner event that
    correctly does not exist.

    ``state_before``, never the current state — the event has already moved it. Task 7's
    `_claim_required` ("does this transition owe the coordinator an event AT ALL?") asks a
    different question of the same row, but it MUST gate on the same `holds_claim` and the
    same `state_before`: two readings of "does the lane change here" is how a writer ends
    up manufacturing precisely the half-state its auditor is looking for."""
    return transition.releases_claim and holds_claim(state_before)


@dataclass(frozen=True)
class NonTransition:
    """An event that lives on an Attempt's stream, carries its ``attempt_id``, and moves NO
    state — the spec's ``‡`` rows keyed by ``attempt_id`` — TOGETHER WITH the rules that
    make one legal.

    A bare set of names was not enough. `walk_attempt` skipped every member without
    checking anything, so a heartbeat before the grant, after the terminal, or stamped with
    a stale generation folded cleanly — in the one component whose job is to refuse
    histories the machine could not have produced. `cas_heartbeat` will not write any of
    them, so accepting them is the auditor believing something no writer can create.

    ``legal_states`` is the state the Attempt must be in when the event is recorded.
    ``generation_field``, when set, names a payload field that must equal the claim
    generation in force at that point.

    There is deliberately NO ``required_payload`` here, though it was asked for: the
    payload contract for every event type is declared once, in `events.py`'s validator
    table, and enforced at the write boundary for records this fold only ever reads back.
    A second list of required fields would be a second contract, and the first divergence
    between them would be silent."""

    event: str
    legal_states: frozenset[AttemptState]
    generation_field: str | None


#: `ClaimHeartbeat` is the one Slice 2 writes (`cas_heartbeat`, Task 10);
#: `PublishRequested`/`Published` join it in a later slice, with their own rules.
NON_TRANSITIONS: tuple[NonTransition, ...] = (
    NonTransition(event="ClaimHeartbeat", legal_states=CLAIM_HOLDING_STATES,
                  generation_field="claim_generation"),
)

#: Declared, not remembered: `project_attempt` folds every event on the stream and fails
#: closed on any type it does not recognise — correct for an unknown type, wrong for a
#: heartbeat. Without this the first heartbeat would make every later projection of that
#: Attempt raise `IllegalTransition`, which `cas_attempt_transition` reads as an
#: untrustworthy history and refuses to add to: a live claim wedging itself by proving it
#: was alive.
NON_TRANSITION_EVENTS: frozenset[str] = frozenset(n.event for n in NON_TRANSITIONS)
_BY_NON_TRANSITION: dict[str, NonTransition] = {n.event: n for n in NON_TRANSITIONS}

_BY_EVENT: dict[str, Transition] = {t.event: t for t in TRANSITIONS}
ATTEMPT_EVENT_TYPES: frozenset[str] = frozenset(_BY_EVENT) | NON_TRANSITION_EVENTS

#: The transitions that carry the claim generation forward. Both write it because a grant
#: opens a generation and an expiry closes the one it names (FR-035); no other row changes
#: which generation is in force.
_GENERATION_EVENTS = ("ClaimGranted", "ClaimExpired")


def legal_events_from(state: AttemptState) -> frozenset[str]:
    return frozenset(t.event for t in TRANSITIONS if state in t.from_states)


@dataclass(frozen=True)
class AttemptProjection:
    attempt_id: str
    state: AttemptState
    revision: int
    claim_generation: int | None
    #: Whether the LAST transition actually emitted a `ClaimReleased` — the conditional
    #: reading (:func:`released_claim`), not the row's declaration. Named in the past tense
    #: for that reason: `Transition.releases_claim` is what the row says, this is what
    #: happened.
    released_claim: bool

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    @property
    def counts_against_quality(self) -> bool:
        return self.state in COUNTED_TERMINALS

    @property
    def counts_against_operational(self) -> bool:
        return self.state in OPERATIONAL_TERMINALS


@dataclass(frozen=True)
class TransitionOutcome:
    """What a cross-stream write returns: the resulting projection, and whether THIS call
    wrote it.

    `created` exists on all four matrix rows for one reason — the lost-acknowledgement
    contract. A durable transaction whose caller never learned it landed is
    indistinguishable, to that caller, from one that never ran, so the recovery path is the
    ordinary retry and the retry must report "already yours" rather than either raising or
    claiming fresh work. `ClaimOutcome.created` (row 1) answers it for the claim grant;
    this answers it for rows 2, 3 and 4. One question, one shape, four rows — which is also
    what lets the lost-ack suite be parameterized over the matrix instead of written four
    times with four different assertions."""

    projection: AttemptProjection
    created: bool


@dataclass(frozen=True)
class Step:
    """One state-moving event, with everything a consumer needs about its position in the
    history. A record rather than a tuple because it has grown twice already, and each
    consumer reads a different subset."""

    state_before: AttemptState | None
    event: Event
    transition: Transition
    state_after: AttemptState
    #: The claim generation in force AFTER this event, or `None` before any grant.
    claim_generation: int | None


def _required_field(event: Event, key: str) -> object:
    """`payload_field`, but the refusal is an :class:`IllegalTransition`.

    `payload_field` raises a bare `ValueError`, and every caller of this fold catches
    `IllegalTransition` — a `ClaimGranted` with no `claim_generation` is a record the
    writers cannot produce, so it must be refused the same way every other impossible
    history is, not escape as a different exception type that `cas_attempt_transition`
    does not recognise as "this history is untrustworthy"."""
    try:
        return payload_field(event, key)
    except ValueError as exc:
        raise IllegalTransition(str(exc)) from exc


def walk_attempt(events: list[Event]) -> Iterator[Step]:
    """The ONE fail-closed Attempt fold. Yields a :class:`Step` per state-moving event, in
    order, and raises on any history the machine could not have produced — an unknown
    event, an out-of-order ``seq``, a transition with no row, a transition illegal from the
    state it is in, a second terminal, or a non-transition event recorded somewhere its
    rule forbids.

    It is a generator so that BOTH consumers get the same interpretation:
    :func:`project_attempt` needs only the final state, while
    ``coordinator.assert_lane_consistent`` needs the state BEFORE each event (to decide
    whether a declared coordinator effect was required at that point). A checker that
    advanced state on its own — ``state = transition.to_state``, no legality check — would
    be a second, weaker lifecycle interpreter: it would accept completed illegal histories
    and could misclassify effect applicability, in the one component whose entire job is to
    disbelieve the history. Constitution I applies to the auditor too.

    ``events`` MUST be this Attempt's events filtered from a COMPLETE Problem stream as
    returned by :func:`lane_log.read`, which has already validated that the stream's ``seq``
    line is gap-free. What is checked here is only that the filtered sequence STRICTLY
    INCREASES: a Problem's stream carries every Attempt on that Problem plus Problem-level
    events, so one Attempt's events are legitimately non-contiguous, and re-checking
    contiguity on the subset would reject every healthy interleaved history. Strictly
    increasing is the real invariant — it catches a caller that concatenated two reads,
    sorted by timestamp, or fed events from a stream whose continuity was never
    established."""
    if not events:
        raise IllegalTransition("an Attempt projection needs at least its Proposed event")
    state: AttemptState | None = None
    generation: int | None = None
    attempt_id = events[0].attempt_id
    previous_seq = -1
    for position, e in enumerate(events):
        if e.attempt_id != attempt_id:
            raise IllegalTransition(
                f"event {position} belongs to {e.attempt_id!r}, not {attempt_id!r}")
        if e.seq is None or e.seq <= previous_seq:
            raise IllegalTransition(
                f"event {position} of {attempt_id!r} has seq {e.seq!r}, which does not "
                f"follow {previous_seq} — the history is not in authoritative order")
        previous_seq = e.seq
        rule = _BY_NON_TRANSITION.get(e.event_type)
        if rule is not None:
            # Moves no state, but is not therefore unconstrained. `cas_heartbeat` writes a
            # beat only while the claim it names is held at the generation it stamps, so a
            # beat anywhere else is a record no writer could have produced.
            if state not in rule.legal_states:
                raise IllegalTransition(
                    f"{e.event_type!r} at {state.value if state is not None else None!r}: "
                    f"legal only in {sorted(s.value for s in rule.legal_states)}")
            if rule.generation_field is not None:
                stamped = _required_field(e, rule.generation_field)
                if stamped != generation:
                    raise IllegalTransition(
                        f"{e.event_type!r} stamps {rule.generation_field}={stamped!r} but "
                        f"the claim in force is generation {generation!r} — a beat for a "
                        "claim this Attempt no longer holds")
            continue
        transition = _BY_EVENT.get(e.event_type)
        if transition is None:
            raise IllegalTransition(f"unknown Attempt event {e.event_type!r} — fail closed")
        if state is None:
            if transition.from_states:
                raise IllegalTransition(
                    f"an Attempt cannot open with {e.event_type!r}")
        elif state in TERMINAL_STATES:
            raise IllegalTransition(
                f"{attempt_id!r} is already terminal at {state.value!r}; "
                f"{e.event_type!r} would be a SECOND terminal")
        elif state not in transition.from_states:
            raise IllegalTransition(
                f"illegal transition {e.event_type!r} from {state.value!r}")
        if transition.witness is not None:
            # Checkable here and NOWHERE ELSE: `validate_lane_event` sees one record and
            # the state it contradicts is not in it, so a `stage` from the legal vocabulary
            # always passes the write boundary. Only the fold knows the state being left.
            expected = transition.witness.term(state)
            actual = _required_field(e, transition.witness.field)
            if actual != expected:
                raise IllegalTransition(
                    f"{e.event_type!r} from {state.value!r} carries "
                    f"{transition.witness.field}={actual!r}, but only {expected!r} is "
                    f"possible there — the record claims something its own history denies")
        if e.event_type in _GENERATION_EVENTS:
            generation = _required_field(e, "claim_generation")
        yield Step(state, e, transition, transition.to_state, generation)
        state = transition.to_state


def project_attempt(events: list[Event]) -> AttemptProjection:
    """Fold one Attempt's events into its state. All validation lives in
    :func:`walk_attempt`; this adds only what a projection carries beyond the state."""
    state: AttemptState | None = None
    last: Step | None = None
    generation: int | None = None
    for step in walk_attempt(events):
        state, last, generation = step.state_after, step, step.claim_generation
    if state is None or last is None:
        # Unreachable through the public vocabulary today — every declared non-transition
        # is legal only in a claim-holding state, so a stream of nothing but those already
        # fails inside `walk_attempt`. Kept because the alternative failure mode is an
        # `AttributeError` on `last`, and a fold whose "impossible" branch crashes instead
        # of refusing is one that cannot be used for recovery.
        raise IllegalTransition(
            f"{events[0].attempt_id!r} has only non-transition events — no state to project")
    return AttemptProjection(
        attempt_id=events[0].attempt_id, state=state, revision=len(events),
        # The last TRANSITION, not the last event: a heartbeat DURING a held claim is legal
        # and can be the final record on the stream, and `_BY_EVENT[...]` would raise on it.
        # (A heartbeat AFTER a terminal is NOT legal — `walk_attempt` refuses it, since no
        # terminal is claim-holding — which an earlier draft of this comment had backwards.)
        claim_generation=generation,
        released_claim=released_claim(last.transition, last.state_before),
    )


def _release_effect(problem_id: str, attempt_id: str, actor: str, timestamp: str) -> Event:
    """The coordinator's release. Carries NO generation: the fencing token advances on
    ``ClaimAcquired`` alone, so putting one here would be a second, unread copy of a number
    with one owner."""
    return coord_event("ClaimReleased", problem_id=problem_id, attempt_id=attempt_id,
                       payload={"problem_id": problem_id, "attempt_id": attempt_id},
                       actor=actor, timestamp=timestamp)


def _monitor_effect(problem_id: str, attempt_id: str, actor: str, timestamp: str) -> Event:
    """Matrix row 4. ``merged_at`` is this transaction's instant — the SAME clock read the
    Attempt's ``PromotionObserved`` carries, because they are one commit. It is the value
    ``last_autonomous_merge_at`` folds to, so the coordinator never has to guess when the
    merge it is monitoring actually landed."""
    return coord_event("MonitorStarted", problem_id=problem_id, attempt_id=attempt_id,
                       payload={"problem_id": problem_id, "attempt_id": attempt_id,
                                "merged_at": timestamp},
                       actor=actor, timestamp=timestamp)


#: Keyed by the exact names :attr:`Transition.coordinator_effects` uses. A row naming an
#: effect with no builder is caught by `test_every_declared_effect_has_a_builder`, not at
#: runtime in production — the table and this registry are two halves of one declaration.
_COORDINATOR_EFFECTS: dict[str, Callable[[str, str, str, str], Event]] = {
    "ClaimReleased": _release_effect,
    "MonitorStarted": _monitor_effect,
}


def _claim_required(transition: Transition, state_before: AttemptState | None) -> bool:
    """Does this transition, from this state, have to write the coordinator too?

    The matrix's conditional-effects clause, in code: the row must declare effects AND the
    Attempt must hold the lane in the state the transition is LEAVING. "Holds the lane" is
    read from the Attempt's own timeline (:func:`holds_claim`) rather than from the
    coordinator, so that this — the WRITER's rule — and ``assert_lane_consistent``'s rule
    are the same predicate over the same input. Two readings of "is a release required" is
    how a writer ends up manufacturing precisely the half-state its auditor is looking for.

    It takes a STATE, not a history, because a replay must ask the question about the state
    the stored event was written FROM — which is not the current state, since the event
    already moved it. Passing a history would silently answer about the present.

    Sibling of :func:`released_claim`, which asks the narrower "was a ``ClaimReleased``
    among them?". They differ ONLY in which declaration they consult — both gate on the
    same ``holds_claim(state_before)``, and neither may re-derive that gate. (They currently
    agree on every row, because every row that declares any effect declares a release; a
    future ``◇``-only row is exactly when they must not be collapsed into one.)"""
    return bool(transition.coordinator_effects) and holds_claim(state_before)


def _state_before(history: list[Event], event_id: str) -> AttemptState | None:
    """The state this Attempt was in immediately before ``event_id`` was applied.

    Read back through the SAME fold everything else uses, so a replay's applicability answer
    is the one the original write computed and the one the auditor will compute."""
    for step in walk_attempt(history):
        if step.event.event_id == event_id:
            return step.state_before
    raise IllegalTransition(f"{event_id} is not a transition in this history")


def cas_attempt_transition(repo: Path, *, problem_id: str, attempt_id: str,
                           event_type: str, payload: Mapping[str, Any], actor: str,
                           clock: Callable[[], str],
                           config: LaneLogConfig | None = None,
                           _after_parent: Seam = None, _before_ref_update: Seam = None,
                           _after_push: Seam = None) -> TransitionOutcome:
    """Append one Attempt transition — and the coordinator effects its row declares — under
    the table's rules, or raise ``LaneRevisionConflict``.

    Returns the resulting projection together with whether THIS call wrote it, so a retry
    after a lost acknowledgement is an ordinary no-op rather than an error.

    The precondition is re-evaluated against the projection the CAS commits against — never
    a stale read — so a terminal that landed while this caller was deciding defeats it. That
    is the whole mechanism behind FR-035's "exactly one terminal": ref-level CAS ORDERS two
    concurrent terminals, it does not reject either, so the rejection has to happen here."""
    if event_type in NON_TRANSITION_EVENTS:
        raise IllegalTransition(
            f"{event_type!r} moves no state and is not written through this path")
    transition = _BY_EVENT.get(event_type)
    if transition is None:
        raise IllegalTransition(f"unknown Attempt event {event_type!r}")
    if event_type == "ClaimExpired":
        # A reclaim's preconditions (expiry reached, no unreconciled intent, held at the
        # observed generation) are not decorations on this transition — they ARE the
        # reclaim. Reaching it through the generic path would skip them.
        raise IllegalTransition("ClaimExpired is written by cas_reclaim, not by this path")
    events = read(repo, problem_id, config=config)
    coordinator_events = read(repo, COORDINATOR_STREAM, config=config)
    coordinator = project_coordinator(coordinator_events)
    history = [e for e in events if e.attempt_id == attempt_id]
    event_id = derive_event_id(problem_id, f"{transition.key_suffix}\x00{attempt_id}")
    stored = next((e for e in history if e.event_id == event_id), None)

    if stored is not None:
        event = stored
        requires_claim = _claim_required(transition, _state_before(history, event_id))
        writes = replayed_transaction(
            repo, stored, transition.coordinator_effects, coordinator_events,
            problem_id=problem_id, attempt_id=attempt_id,
            expected_event_type=event_type, required=requires_claim, config=config)
    else:
        event = Event(
            event_id=event_id,
            event_type=event_type, problem_id=problem_id, actor=actor,
            payload={"problem_id": problem_id, "attempt_id": attempt_id, **payload},
            timestamp=clock(), attempt_id=attempt_id,
        )
        # Whether this transition must ALSO write the coordinator is a fact about the
        # ATTEMPT — exactly the predicate `assert_lane_consistent` audits with. Deriving it
        # from the coordinator's ownership instead makes a DISAGREEMENT between the two look
        # like "nothing to release": an Attempt in `implementing` whose claim record is
        # missing or names someone else would write its terminal alone, manufacturing the
        # half-state the transaction exists to prevent and leaving the auditor to find it
        # later. Reading it from the Attempt's own timeline makes the two readings agree by
        # construction, and turns a divergence into a REFUSAL here.
        requires_claim = _claim_required(
            transition, project_attempt(history).state if history else None)
        writes = [event, *(
            _COORDINATOR_EFFECTS[name](problem_id, attempt_id, actor, event.timestamp)
            for name in (transition.coordinator_effects if requires_claim else ()))]

    expected = {problem_id: len(events)}
    if requires_claim:
        expected[COORDINATOR_STREAM] = coordinator.lane_revision

    def _legal_or_landed(observed: dict[str, list[Event]]) -> tuple[bool, str]:
        evs = observed[problem_id]
        if any(e.event_id == event.event_id for e in evs):
            return (True, "")  # this exact transition already landed → idempotent
        history = [e for e in evs if e.attempt_id == attempt_id]
        if not history:
            return (not transition.from_states, "an Attempt cannot open with this event")
        try:
            current = project_attempt(history)
        except IllegalTransition as exc:   # a history we cannot trust → refuse to add to it
            return (False, f"unprojectable history: {exc}")
        if current.is_terminal:
            return (False, f"{attempt_id!r} already terminal at {current.state.value!r}")
        if current.state not in transition.from_states:
            return (False, f"illegal from {current.state.value!r}")
        if _claim_required(transition, current.state) != requires_claim:
            # Defence in depth behind the expected-revision pin above, which is what
            # actually rejects a claim status that moved: this Attempt's state cannot change
            # without its Problem stream growing, and a grown stream is already a stale
            # revision. The check stays because it is the ONE thing that would still be true
            # if that pin were ever loosened to allow per-Attempt concurrency — and because
            # `from_states` alone does not pin applicability: `ReviewAborted` is legal from
            # `proposed` (holds nothing) AND from `implementing` (holds the lane), so a
            # single-stream write built from a stale `proposed` would satisfy every other
            # check at a parent where the Attempt is claimed.
            return (False, "this Attempt's claim status changed while these writes were "
                           "being built — recompute against the new tip")
        if requires_claim:
            # Re-checked against the SAME parent the commit is built on, so a claim that
            # changed hands while this caller was deciding defeats the release half — and
            # because it is one transaction, it defeats the terminal too. Note this now runs
            # whenever the ATTEMPT holds, so an idle-or-foreign coordinator is a REFUSAL
            # rather than a silently claim-free terminal.
            now_holding = project_coordinator(observed[COORDINATOR_STREAM])
            if (now_holding.active_problem_id, now_holding.active_attempt_id) != (
                    problem_id, attempt_id):
                return (False,
                        f"{attempt_id!r} is {current.state.value!r} and so holds the lane, "
                        f"but the coordinator has "
                        f"{now_holding.active_problem_id}/{now_holding.active_attempt_id}")
        return (True, "")

    result = append_many(repo, writes, expected_revisions=expected,
                         precondition=_legal_or_landed, config=config,
                         _after_parent=_after_parent,
                         _before_ref_update=_before_ref_update, _after_push=_after_push)
    return TransitionOutcome(
        projection=project_attempt(
            [e for e in read(repo, problem_id, config=config)
             if e.attempt_id == attempt_id]),
        created=result.created)


__all__ = [
    "ATTEMPT_EVENT_TYPES",
    "CLAIM_HOLDING_STATES",
    "COUNTED_TERMINALS",
    "NON_TRANSITIONS",
    "NON_TRANSITION_EVENTS",
    "OPERATIONAL_TERMINALS",
    "TERMINAL_STATES",
    "TRANSITIONS",
    "AttemptProjection",
    "AttemptState",
    "IllegalTransition",
    "NonTransition",
    "ProblemDisposition",
    "StateWitness",
    "Step",
    "Transition",
    "TransitionOutcome",
    "cas_attempt_transition",
    "holds_claim",
    "legal_events_from",
    "project_attempt",
    "released_claim",
    "walk_attempt",
]
