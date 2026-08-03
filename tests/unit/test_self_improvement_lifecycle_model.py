"""The Attempt machine as a MODEL, driven exhaustively rather than by hand-picked paths.

Exhaustive enumeration + seeded random walks rather than `hypothesis`: no new dependency,
fully deterministic, and the seed is printed on failure so any counterexample replays."""
from __future__ import annotations

import random
from dataclasses import replace

import pytest

from llmxive.self_improvement.events import Event
from llmxive.self_improvement.lifecycle import (
    _BY_EVENT,
    CLAIM_HOLDING_STATES,
    COUNTED_TERMINALS,
    NON_TRANSITION_EVENTS,
    OPERATIONAL_TERMINALS,
    TERMINAL_STATES,
    TRANSITIONS,
    AttemptState,
    IllegalTransition,
    holds_claim,
    legal_events_from,
    project_attempt,
    walk_attempt,
)
from tests.helpers.lane_lifecycle import attempt_event, drive


def test_every_transition_names_states_that_exist():
    for t in TRANSITIONS:
        assert t.to_state in AttemptState, t
        for s in t.from_states:
            assert s in AttemptState, t


def test_every_non_terminal_state_can_be_left():
    # A state with no outgoing transition is a silent dead end — an Attempt that reaches it
    # is stuck forever with no terminal, which the lane cannot represent.
    for state in AttemptState:
        if state in TERMINAL_STATES:
            continue
        assert legal_events_from(state), f"{state} is a non-terminal dead end"


def test_every_terminal_state_is_truly_terminal():
    for state in TERMINAL_STATES:
        assert not legal_events_from(state), f"{state} is terminal but has outgoing edges"


def test_counted_terminals_are_a_strict_subset_of_terminals():
    assert COUNTED_TERMINALS < TERMINAL_STATES
    # The uncounted operational terminals, named explicitly (spec table): counting one of
    # these would let infrastructure burn a Problem's quality budget (FR-001).
    for uncounted in (AttemptState.REJECTED, AttemptState.UNSUPPORTED_SCOPE,
                      AttemptState.SUPERSEDED, AttemptState.REVIEW_ABORTED,
                      AttemptState.ATTEMPT_ABANDONED):
        assert uncounted not in COUNTED_TERMINALS


def test_idempotency_keys_are_unique_per_transition():
    keys = [t.key_suffix for t in TRANSITIONS]
    assert len(keys) == len(set(keys)), "two transitions share an idempotency key"


@pytest.mark.parametrize("state", list(AttemptState))
def test_every_illegal_event_from_every_state_is_refused(state):
    # The whole (state x event) grid, not a sampled corner of it.
    legal = legal_events_from(state)
    for t in TRANSITIONS:
        if t.event in legal:
            continue
        with pytest.raises(IllegalTransition):
            project_attempt([*drive(state), attempt_event(t.event)])


def test_a_second_terminal_is_refused_whichever_two_they_are():
    for first in sorted(TERMINAL_STATES, key=lambda s: s.value):
        history = drive(first)
        for t in TRANSITIONS:
            if t.to_state not in TERMINAL_STATES:
                continue
            with pytest.raises(IllegalTransition):
                project_attempt([*history, attempt_event(t.event)])


def test_a_NON_CONTIGUOUS_seq_line_is_legal_because_streams_interleave():
    # A Problem's stream carries other Attempts and Problem-level events, so THIS Attempt's
    # events have gaps. Rejecting gaps would reject every healthy interleaved history.
    history = [attempt_event("Proposed", seq=0), attempt_event("ProposalVerified", seq=7),
               attempt_event("ClaimGranted", seq=40)]
    assert project_attempt(history).state is AttemptState.CLAIMED


@pytest.mark.parametrize("seqs", [(0, 0), (5, 3), (0, 1, 1)])
def test_a_seq_line_that_does_not_STRICTLY_increase_is_refused(seqs):
    events = ["Proposed", "ProposalVerified", "ClaimGranted"][: len(seqs)]
    history = [attempt_event(e, seq=s) for e, s in zip(events, seqs, strict=True)]
    with pytest.raises(IllegalTransition, match="authoritative order"):
        project_attempt(history)


def test_an_unsequenced_event_is_refused():
    # `seq` is stamped by the store inside the CAS, so a None here means the caller built
    # this history from something other than a committed, continuity-validated read.
    with pytest.raises(IllegalTransition, match="authoritative order"):
        project_attempt([attempt_event("Proposed", seq=None)])


def test_random_walks_never_violate_the_invariants():
    rng = random.Random(20260731)
    for trial in range(500):
        state, history = AttemptState.PROPOSED, [attempt_event("Proposed")]
        for _ in range(12):
            options = legal_events_from(state)
            if not options:
                break
            event = rng.choice(sorted(options))
            history.append(attempt_event(event))
            state = project_attempt(history).state
        result = project_attempt(history)
        assert result.state is state, f"trial {trial}: fold disagreed with the walk"
        assert result.is_terminal == (state in TERMINAL_STATES)
        assert result.counts_against_quality == (state in COUNTED_TERMINALS)
        # The two counters are separate ledgers (FR-034): an Attempt may feed at most one.
        assert result.counts_against_operational == (state in OPERATIONAL_TERMINALS)
        assert not (result.counts_against_quality and result.counts_against_operational)


def test_the_code_table_matches_the_spec_table():
    """Spec/code drift is a FAILING TEST, not a review finding.

    Compares COMPLETE ROWS in BOTH directions. An event-name-only comparison passes while
    the spec says `PromotionObserved` releases the claim and the code says it does not —
    which is precisely the defect this test exists to catch, so matching names is not
    enough. Every field the spec states is compared: from-states, to-state, idempotency
    key, and the effect markers († releases the claim, ◇ starts monitoring)."""
    from tests.helpers.lane_lifecycle import parse_spec_transitions

    spec_rows, spec_non_transitions = parse_spec_transitions()
    assert spec_rows, "the spec transition table did not parse — the test is vacuous"
    # Every Attempt-scoped row that is NOT a transition must be declared, or
    # `project_attempt` fails closed the first time one is written. Two directions, and
    # they are not symmetric:
    assert NON_TRANSITION_EVENTS <= spec_non_transitions, (
        f"declared but not in the spec table: "
        f"{sorted(NON_TRANSITION_EVENTS - spec_non_transitions)}")
    # ...and every spec row NOT declared must be EXPLICITLY excluded, so a future ‡ row
    # forces a decision here rather than surfacing as a fail-closed projection in
    # production. `PublishRequested→Published` is not a literal Attempt event type: it
    # names the publish SAGA, whose records are the `SideEffectRequested`/
    # `SideEffectObserved` pair in `intents.py` (Task 11 asserts neither is an Attempt
    # event). Nothing lands on the Attempt's own stream for it.
    _NOT_ATTEMPT_STREAM_EVENTS = {"PublishRequested→Published"}
    assert spec_non_transitions - NON_TRANSITION_EVENTS == _NOT_ATTEMPT_STREAM_EVENTS, (
        f"undecided ‡ rows keyed by attempt_id: "
        f"{sorted(spec_non_transitions - NON_TRANSITION_EVENTS - _NOT_ATTEMPT_STREAM_EVENTS)}")
    code_rows = {
        t.event: (frozenset(s.value for s in t.from_states), t.to_state.value,
                  t.key_suffix, t.coordinator_effects)
        for t in TRANSITIONS
    }
    assert set(spec_rows) == set(code_rows), (
        f"only in spec: {sorted(set(spec_rows) - set(code_rows))}; "
        f"only in code: {sorted(set(code_rows) - set(spec_rows))}")
    mismatched = {e: (spec_rows[e], code_rows[e]) for e in spec_rows
                  if spec_rows[e] != code_rows[e]}
    assert not mismatched, f"spec/code row mismatch: {mismatched}"


def _history(*event_types: str) -> list[Event]:
    """A committed-looking Attempt history: `attempt_event` per type, `seq` 0..n.

    The claim generation the beat rule compares against is stamped by `attempt_event`
    itself, for every event type that carries one — so a history built here is one the
    writers could actually have produced, and there is ONE place that knows which types
    those are. A helper that emitted beats or grants with no generation would make every
    claim-reaching test fail for the wrong reason."""
    return [attempt_event(t, seq=i, payload={"tick": i} if t == "ClaimHeartbeat" else None)
            for i, t in enumerate(event_types)]


def test_heartbeats_do_not_disturb_a_projection():
    """A `ClaimHeartbeat` is recorded on the Attempt's own stream and moves no state.

    `project_attempt` folds EVERY event on that stream and fails closed on any type it does
    not recognise. Correct for an unknown type; catastrophic for a heartbeat — the first
    beat would make every later projection of that Attempt raise, and
    `cas_attempt_transition` reads that as an untrustworthy history and refuses to add to
    it. A live claim would wedge itself by proving it was alive. So: the same history with
    beats interleaved projects identically to the one without."""
    quiet = _history("Proposed", "ProposalVerified", "ClaimGranted", "Implementing")
    beaten = _history("Proposed", "ProposalVerified", "ClaimGranted", "ClaimHeartbeat",
                      "Implementing", "ClaimHeartbeat")
    assert project_attempt(beaten).state == project_attempt(quiet).state
    assert project_attempt(beaten).claim_generation == \
        project_attempt(quiet).claim_generation


@pytest.mark.parametrize("history, why", [
    (_history("Proposed", "ClaimHeartbeat"), "before the grant"),
    (_history("Proposed", "ProposalVerified", "ClaimGranted", "ImplementationFailed",
              "ClaimHeartbeat"), "after the terminal released the claim"),
])
def test_a_heartbeat_outside_a_held_claim_is_refused(history, why):
    """`cas_heartbeat` writes a beat only while the claim it names is held, so these are
    histories no writer can produce — and an earlier draft of this plan asserted the second
    one was LEGAL, which is how a fold ends up blessing records its own writer forbids.
    `legal_states` is what makes the fold's rule the writer's rule."""
    with pytest.raises(IllegalTransition, match="legal only in"):
        project_attempt(history)


def test_a_heartbeat_at_a_stale_generation_is_refused():
    """A beat is evidence about ONE claim. Stamped with a generation the Attempt no longer
    holds, it is a crashed runner's beat arriving after a reclaim — exactly the record the
    fencing token exists to make detectable, so accepting it would defeat the token."""
    history = _history("Proposed", "ProposalVerified", "ClaimGranted")   # generation 1
    history.append(attempt_event("ClaimHeartbeat", seq=3,
                                 payload={"claim_generation": 2, "tick": 1}))
    with pytest.raises(IllegalTransition, match="no longer holds"):
        project_attempt(history)


@pytest.mark.parametrize("event_type", ["ClaimGranted", "ClaimHeartbeat"])
def test_a_MISSING_generation_is_refused_as_an_IllegalTransition(event_type):
    """`payload_field` raises a bare `ValueError`, and every caller of this fold catches
    `IllegalTransition`. A grant or beat with no `claim_generation` is a record the writers
    cannot produce, so it must be refused the SAME WAY every other impossible history is —
    not escape as a type `cas_attempt_transition` does not recognise as "untrustworthy
    history" and therefore does not handle."""
    history = _history("Proposed", "ProposalVerified", "ClaimGranted")
    if event_type == "ClaimHeartbeat":
        history.append(attempt_event("ClaimHeartbeat", seq=3, payload={"tick": 1}))
    # Stripped rather than never-stamped: `attempt_event` supplies the generation for every
    # type that carries one, which is exactly the property this test has to defeat.
    history[-1] = replace(history[-1], payload={"problem_id": "P1", "attempt_id": "A1"})
    with pytest.raises(IllegalTransition, match="lacks 'claim_generation'"):
        project_attempt(history)


def test_walk_attempt_yields_the_state_before_each_event():
    """The auditor's whole conditional-effects rule is defined over `state_before`, so the
    fold must hand it over rather than have each consumer recompute it."""
    steps = list(walk_attempt(_history("Proposed", "ProposalVerified", "ClaimGranted")))
    assert [(s.state_before, s.event.event_type, s.state_after) for s in steps] == [
        (None, "Proposed", AttemptState.PROPOSED),
        (AttemptState.PROPOSED, "ProposalVerified", AttemptState.PROPOSAL_VERIFIED),
        (AttemptState.PROPOSAL_VERIFIED, "ClaimGranted", AttemptState.CLAIMED),
    ]
    # The generation the beat rule compares against, carried by the same fold.
    assert [s.claim_generation for s in steps] == [None, None, 1]


def test_one_fold_means_one_verdict_on_an_illegal_history():
    """An illegal COMPLETED history must be rejected by every consumer, not just by the
    one that happens to validate. This is the test a second, weaker interpreter fails:
    an auditor that advanced `state = transition.to_state` without checking `from_states`
    would happily audit this history and report the lane healthy."""
    illegal = _history("Proposed", "Implementing")     # `Implementing` is claimed-only
    with pytest.raises(IllegalTransition, match="illegal transition"):
        project_attempt(illegal)
    with pytest.raises(IllegalTransition, match="illegal transition"):
        list(walk_attempt(illegal))


@pytest.mark.parametrize("history, message", [
    ([], "an Attempt projection needs at least its Proposed event"),
    (_history("Proposed", "Implementing"), "illegal transition"),
    (_history("Proposed", "Rejected", "ReviewAborted"), "already terminal"),
    ([*_history("Proposed"), attempt_event("NotAnEvent", seq=1)], "unknown Attempt event"),
])
def test_project_attempt_raises_the_MESSAGE_it_is_specified_to_raise(history, message):
    """Maintainer decision (2026-08-02, open question 12): `project_attempt`'s error
    messages are a compatibility requirement, so they are PINNED rather than left to
    whatever `walk_attempt` happens to say.

    The decision's premise needs one correction, recorded here because a future reader
    will otherwise look for something that does not exist: there are no pre-existing 1A
    projection tests to run — `grep -rn project_attempt src/ tests/` returns nothing
    before this task, because this slice introduces the function. So the requirement
    cannot be discharged by re-running an old suite; it is discharged by pinning the
    messages HERE, in the task that writes them, which is what makes a later change to the
    shared fold a failing test rather than a silent change in what every caller sees."""
    with pytest.raises(IllegalTransition, match=message):
        project_attempt(history)


def test_non_transition_events_are_declared_and_disjoint():
    """The set is a DECLARATION, not a skip-list that grew. Nothing may be in both: an
    event that both moves state and is skipped by the fold would be silently ignored.

    That every member is a known event type is already asserted by Task 6's
    `ATTEMPT_EVENT_TYPES - KNOWN_EVENT_TYPES_V1` check, which now covers this set because
    `ATTEMPT_EVENT_TYPES` includes it — so it is not re-asserted here."""
    assert not (NON_TRANSITION_EVENTS & set(_BY_EVENT))


def test_an_attempt_of_only_non_transition_events_is_refused():
    """Fail closed: a stream of beats and nothing else has no state, and returning some
    default state for it would invent a lifecycle that never happened.

    It is refused by the heartbeat's own `legal_states` rule (a beat is legal only in a
    claim-holding state, and a beats-only stream never reaches one), which is why
    `project_attempt`'s "no state to project" branch is unreachable through the current
    vocabulary. That branch is kept as a guard, not as a covered path — the honest claim
    this test makes is about the OUTCOME, not about which line produces it."""
    with pytest.raises(IllegalTransition):
        project_attempt(_history("ClaimHeartbeat"))


def test_claim_holding_states_are_what_the_table_says():
    """Pins the CURRENT answer, so an accidental table edit shows up in review."""
    assert CLAIM_HOLDING_STATES == {
        AttemptState.CLAIMED, AttemptState.IMPLEMENTING,
        AttemptState.PROMOTING, AttemptState.PROMOTION_REQUESTED,
    }


def test_holds_claim_is_the_ONE_reading_of_the_question():
    """Three callers ask "does this Attempt hold the lane?" and must never disagree, so the
    predicate is asserted against the set it is defined from — including the `None` case,
    which is the one a caller is most likely to get wrong: an Attempt with no events yet
    holds nothing, and `None in CLAIM_HOLDING_STATES` is the only reason that is already
    true rather than a crash."""
    assert holds_claim(None) is False
    for state in AttemptState:
        assert holds_claim(state) == (state in CLAIM_HOLDING_STATES), state


def test_no_claim_holding_state_is_TERMINAL():
    """Pins the PROPERTY, so a DELIBERATE table edit that breaks the machine still fails
    even when someone updates the test above to match.

    A terminal reachable from `claimed` without releasing would wedge the lane at it: the
    Attempt could never move again and nothing would ever free the claim. That is what the
    derivation is really asserting, and why the set is computed rather than trusted."""
    assert not (CLAIM_HOLDING_STATES & TERMINAL_STATES)


def test_terminal_and_release_are_independent_predicates():
    """Neither derived property may be quietly re-implemented as the other. The two rows
    that prove they are different are the ones a `terminal == releases` shortcut breaks."""
    promo = next(t for t in TRANSITIONS if t.event == "PromotionObserved")
    assert promo.releases_claim and not promo.terminal
    retained = next(t for t in TRANSITIONS if t.event == "Retained")
    assert retained.terminal and not retained.releases_claim
    for t in TRANSITIONS:
        assert t.terminal == (t.to_state in TERMINAL_STATES)
        assert t.releases_claim == ("ClaimReleased" in t.coordinator_effects)
