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
from collections.abc import Iterator
from dataclasses import dataclass

from llmxive.self_improvement.events import Event, payload_field


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
class Transition:
    event: str
    from_states: frozenset[AttemptState]
    to_state: AttemptState
    key_suffix: str                       # the idempotency key's 2nd element, per the spec
    coordinator_effects: tuple[str, ...]  # the spec table's † and ◇ markers

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
       *, effects: tuple[str, ...] = ()) -> Transition:
    return Transition(event, frozenset(froms), to, key, effects)


_RELEASES = ("ClaimReleased",)


S = AttemptState

TRANSITIONS: tuple[Transition, ...] = (
    _t("Proposed", (), S.PROPOSED, "proposed"),
    _t("ProposalVerified", (S.PROPOSED,), S.PROPOSAL_VERIFIED, "verified"),
    _t("Rejected", (S.PROPOSED, S.PROPOSAL_VERIFIED), S.REJECTED, "reject"),
    _t("ReviewAborted", (S.PROPOSED, S.IMPLEMENTING), S.REVIEW_ABORTED, "reviewabort",
       effects=_RELEASES),
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
    # because the coordinator fold refuses a release by a non-owner.
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
    releases_claim: bool

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
        if e.event_type in _GENERATION_EVENTS:
            generation = _required_field(e, "claim_generation")
        yield Step(state, e, transition, transition.to_state, generation)
        state = transition.to_state


def project_attempt(events: list[Event]) -> AttemptProjection:
    """Fold one Attempt's events into its state. All validation lives in
    :func:`walk_attempt`; this adds only what a projection carries beyond the state."""
    state: AttemptState | None = None
    last: Transition | None = None
    generation: int | None = None
    for step in walk_attempt(events):
        state, last, generation = step.state_after, step.transition, step.claim_generation
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
        # The last TRANSITION, not the last event: a heartbeat after a terminal is a
        # legal record and `_BY_EVENT[...]` would raise on it.
        claim_generation=generation, releases_claim=last.releases_claim,
    )


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
    "Step",
    "Transition",
    "TransitionOutcome",
    "holds_claim",
    "legal_events_from",
    "project_attempt",
    "walk_attempt",
]
