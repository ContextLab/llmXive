"""The Attempt machine as a MODEL, driven exhaustively rather than by hand-picked paths.

Exhaustive enumeration + seeded random walks rather than `hypothesis`: no new dependency,
fully deterministic, and the seed is printed on failure so any counterexample replays."""
from __future__ import annotations

import random
import re
from dataclasses import replace
from pathlib import Path

import pytest

from llmxive.self_improvement.events import KNOWN_EVENT_TYPES_V1, REVIEW_STAGES, Event
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
    StateWitness,
    Transition,
    _validate_declarations,
    holds_claim,
    legal_events_from,
    project_attempt,
    released_claim,
    walk_attempt,
)
from tests.helpers.lane_lifecycle import (
    attempt_event,
    build_history,
    drive,
    witness_payload,
)


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
            history.append(attempt_event(event, payload=witness_payload(state, event)))
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
    key, and the effect markers († releases the claim, ◇ starts monitoring).

    The key is compared COMPLETE — suffix and the payload fields that follow it. Comparing
    only the suffix is what let a code table that derived its ids without `head_sha` and
    `reason` match a spec that requires them, so a partial comparison here is the same class
    of hole as a names-only one."""
    from tests.helpers.lane_lifecycle import parse_spec_transitions

    spec_rows, spec_non_transitions, _lane_events = parse_spec_transitions()
    assert spec_rows, "the spec transition table did not parse — the test is vacuous"
    # A key parser that returned no fields for every row would compare `()` with `()` and
    # bless exactly the derivation defect this comparison was widened to catch.
    assert any(fields for _f, _t, (_s, fields), _e in spec_rows.values()), (
        "no spec row parsed with idempotency-key fields — the key comparison is vacuous")
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
                  (t.key_suffix, t.key_fields), t.coordinator_effects)
        for t in TRANSITIONS
    }
    assert set(spec_rows) == set(code_rows), (
        f"only in spec: {sorted(set(spec_rows) - set(code_rows))}; "
        f"only in code: {sorted(set(code_rows) - set(spec_rows))}")
    mismatched = {e: (spec_rows[e], code_rows[e]) for e in spec_rows
                  if spec_rows[e] != code_rows[e]}
    assert not mismatched, f"spec/code row mismatch: {mismatched}"


def test_every_non_attempt_row_names_a_record_something_can_WRITE():
    """The `‡` rows' blind spot. They are excluded from the row comparison above because
    they move no Attempt — but excluding the COLUMNS silently excluded the NAMES, and two
    rows drifted there: the spec declared an `OperationalCooldown` (the implementation
    unified it into `Cooldown(cause=...)`) and a `PromotionReenabled` (the record is slice
    1A's `PromotionEnabledSet`). Neither would ever have been written.

    A `‡` row is still a claim that some record exists, so the names are checkable even
    where the columns are not."""
    from tests.helpers.lane_lifecycle import parse_spec_transitions

    _rows, _non_transitions, lane_events = parse_spec_transitions()
    # `PublishRequested→Published` is the one cell that names no single event type: it names
    # the publish SAGA, whose records are the `SideEffectRequested`/`SideEffectObserved`
    # pair. Excluded explicitly, so a future non-literal cell forces a decision here rather
    # than being absorbed by a lenient parser.
    _NOT_A_SINGLE_EVENT = {"PublishRequested→Published"}
    undeclared = lane_events - KNOWN_EVENT_TYPES_V1 - _NOT_A_SINGLE_EVENT
    assert not undeclared, (
        f"‡ rows naming records no writer can produce: {sorted(undeclared)}")


def _history(*event_types: str) -> list[Event]:
    """A committed-looking Attempt history: `attempt_event` per type, `seq` 0..n.

    The claim generation the beat rule compares against is stamped by `attempt_event`
    itself, for every event type that carries one, and `build_history` adds whatever each
    step's SOURCE STATE obliges it to carry — so a history built here is one the writers
    could actually have produced, and there is ONE place that knows both rules. A helper
    that emitted beats or grants with no generation, or a `ReviewAborted` with no `stage`,
    would make every history that crosses one fail for the wrong reason."""
    return build_history(event_types, sequential=True)


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


def test_a_DECLARED_release_from_a_NON_HOLDING_state_emits_nothing():
    """The row's dagger marks "must not leave the lane occupied", NOT "always mutates the
    coordinator" — so a declared release from a state that holds nothing emits nothing.

    Derived from the table, never hand-listed, so a row that becomes reachable from a new
    non-holding state joins this test without anyone remembering to add it. The equality
    below is the CURRENT membership, which is what makes such a change show up in review
    rather than silently widen the exemption; the non-emptiness assert is what keeps the
    parameterization from quietly becoming vacuous."""
    pairs = {(t.event, s) for t in TRANSITIONS if t.releases_claim
             for s in t.from_states - CLAIM_HOLDING_STATES}
    assert pairs, "no declared-release row is reachable from a non-holding state — vacuous"
    assert pairs == {
        ("ReviewAborted", AttemptState.PROPOSED),
        ("ScopeUnsupported", AttemptState.PROPOSAL_VERIFIED),
        ("BreakerTripped", AttemptState.PROPOSED),
        ("BreakerTripped", AttemptState.PROPOSAL_VERIFIED),
    }
    for event, state in pairs:
        assert not released_claim(_BY_EVENT[event], state), (event, state)


def test_released_claim_needs_BOTH_the_declaration_and_the_hold():
    """The two halves are independent, so each must be able to veto on its own."""
    holding_but_undeclared = _BY_EVENT["Implementing"]   # claimed -> implementing, no effect
    assert not released_claim(holding_but_undeclared, AttemptState.CLAIMED)
    declared_and_holding = _BY_EVENT["ImplementationFailed"]
    assert released_claim(declared_and_holding, AttemptState.IMPLEMENTING)
    # `Proposed` opens the Attempt: no declaration, and no state at all to hold from.
    assert not released_claim(_BY_EVENT["Proposed"], None)


@pytest.mark.parametrize("history, expected, why", [
    (_history("Proposed", "ReviewAborted"), False,
     "pre-claim terminal: the row declares a release, the Attempt held nothing"),
    (_history("Proposed", "ProposalVerified", "ScopeUnsupported"), False,
     "the other pre-claim declared-release row"),
    (_history("Proposed", "ProposalVerified", "ClaimGranted", "Implementing",
              "ImplementationFailed"), True,
     "claim-holding terminal: declared and held, so a release was written"),
    (_history("Proposed", "ProposalVerified", "ClaimGranted", "Implementing",
              "EvaluationPassed", "PromotionRequested", "PromotionObserved"), True,
     "releases WITHOUT being terminal — matrix row 4"),
])
def test_the_projection_reports_the_release_that_HAPPENED(history, expected, why):
    """`AttemptProjection.released_claim` is the conditional reading, not the row's.

    Reporting the declaration would send a consumer reconciling the coordinator against
    this projection looking for a `ClaimReleased` that correctly does not exist — the same
    false positive `assert_lane_consistent` case 12j catches at the audit layer."""
    assert project_attempt(history).released_claim is expected, why


@pytest.mark.parametrize("reached, stage, why", [
    (AttemptState.PROPOSED, "proposal", "the proposal review is what runs at `proposed`"),
    (AttemptState.IMPLEMENTING, "patch", "the patch review is what runs at `implementing`"),
])
def test_a_review_abort_naming_the_review_that_ran_is_accepted(reached, stage, why):
    history = [*drive(reached), attempt_event("ReviewAborted", payload={"stage": stage})]
    assert project_attempt(history).state is AttemptState.REVIEW_ABORTED, why


@pytest.mark.parametrize("reached, stage, why", [
    (AttemptState.PROPOSED, "patch",
     "no patch exists at `proposed` — the claim is not merely unlikely, it is impossible"),
    (AttemptState.IMPLEMENTING, "proposal",
     "the proposal review finished two transitions ago; it cannot be what aborted"),
])
def test_a_review_abort_naming_a_review_that_did_not_run_is_refused(reached, stage, why):
    """The write boundary cannot catch this and never will: `_one_of` sees a term from the
    legal vocabulary, and the state it contradicts is not in the record. Left unchecked, a
    durable `ReviewAborted` asserts an operational failure in a review that provably never
    ran — and FR-034's operational streak, which decides whether a Problem cools down, is
    read straight off these records."""
    history = [*drive(reached), attempt_event("ReviewAborted", payload={"stage": stage})]
    with pytest.raises(IllegalTransition, match="its own history denies"):
        project_attempt(history)


def test_a_witnessed_transition_with_NO_witness_term_is_refused():
    """Missing, not merely wrong. `_required_field` is what makes the refusal an
    `IllegalTransition` rather than the bare `ValueError` `payload_field` raises."""
    history = [*drive(AttemptState.PROPOSED), attempt_event("ReviewAborted")]
    with pytest.raises(IllegalTransition, match="payload lacks 'stage'"):
        project_attempt(history)


def test_every_multi_source_transition_has_DECIDED_about_a_state_witness():
    """The class, not the instance. A payload term that names its own source state is
    checkable only on rows legal from more than one state, so every such row must have been
    considered — a new one added without a decision fails here rather than shipping an
    unchecked claim.

    The unwitnessed rows are unwitnessed for a reason, and it is the same reason each time:
    their payloads carry no term that names a state. `ClaimExpired.reason` is the near miss
    — it looks like a discriminator, but `heartbeat_lapsed` and `hold_time_exceeded` are
    both possible from all four claim-holding states, so it describes the CAUSE, not the
    source."""
    unwitnessed = {"Rejected", "ImplementationFailed", "ScopeUnsupported", "FreshnessStale",
                   "BreakerTripped", "ClaimExpired"}
    multi_source = {t.event for t in TRANSITIONS if len(t.from_states) > 1}
    witnessed = {t.event for t in TRANSITIONS if t.witness is not None}
    assert witnessed <= multi_source, (
        f"a witness on a single-source row witnesses nothing: {sorted(witnessed - multi_source)}")
    assert multi_source - witnessed == unwitnessed, (
        f"multi-source rows with no witness decision: "
        f"{sorted(multi_source - witnessed - unwitnessed)}")


@pytest.mark.parametrize("witness, from_states, message", [
    (StateWitness("stage", ((AttemptState.PROPOSED, "proposal"),)),
     (AttemptState.PROPOSED, AttemptState.IMPLEMENTING), "but the row is legal from"),
    (StateWitness("stage", ((AttemptState.PROPOSED, "proposal"),
                            (AttemptState.IMPLEMENTING, "patch"))),
     (), "witnesses nothing"),
    (StateWitness("outcome", ((AttemptState.PROPOSED, "proposal"),
                              (AttemptState.IMPLEMENTING, "patch"))),
     (AttemptState.PROPOSED, AttemptState.IMPLEMENTING), "no write-boundary vocabulary"),
    (StateWitness("stage", ((AttemptState.PROPOSED, "proposal"),
                            (AttemptState.IMPLEMENTING, "implementation"))),
     (AttemptState.PROPOSED, AttemptState.IMPLEMENTING), "disagree with the"),
])
def test_a_MALFORMED_witness_declaration_is_refused_at_import(witness, from_states, message):
    """The declaration check gets its own table, because a rule exercised only against the
    one table that already satisfies it has no evidence it does anything. Each case is a
    real drift path: adding a source state to a witnessed row, witnessing an opening
    transition, witnessing a field the write boundary does not constrain, and letting the
    two vocabularies diverge."""
    bad = Transition("X", frozenset(from_states), AttemptState.REJECTED, "x",
                     witness=witness)
    with pytest.raises(ValueError, match=message):
        _validate_declarations((bad,))


def test_NOBODY_rebuilds_a_transition_id_from_its_suffix():
    """One derivation, statically enforced — because the copies were the actual bug.

    Three sites had hand-written `derive_event_id(problem_id, f"{suffix}\\x00{attempt_id}")`:
    the writer, the claim fixture, and the lost-acknowledgement damage builder. When the key
    gained its variable components the writer was updated and the other two silently kept
    deriving the OLD id — one fixture then stood in for a claim the real path can no longer
    produce, and one planted damage at an id the replay path never reads. Neither is a
    failure the copy itself reports.

    `Transition.event_id` is the only derivation. Mentioning `key_suffix` is fine (the drift
    test compares it); FEEDING it to `derive_event_id` is what nothing but the row may do."""
    root = Path(__file__).resolve().parents[2]
    rebuilt = re.compile(r"derive_event_id\([^)]*key_suffix")
    offenders = [
        str(path.relative_to(root))
        for path in (*(root / "src/llmxive").rglob("*.py"), *(root / "tests").rglob("*.py"))
        if rebuilt.search(path.read_text())
    ]
    assert not offenders, (
        f"an idempotency key rebuilt outside `Transition.event_id`: {sorted(offenders)}")


def test_two_rows_sharing_an_idempotency_SUFFIX_are_refused_at_import():
    """The suffix is what DISCRIMINATES rows. Two rows sharing one derive the same id for
    the same Attempt when neither declares key fields — so a caller invoking the second
    would be told the first had already landed. Exercised against a bad table, because the
    real one satisfies the rule and would prove nothing about it."""
    rows = (Transition("X", frozenset(), AttemptState.PROPOSED, "dup"),
            Transition("Y", frozenset({AttemptState.PROPOSED}), AttemptState.REJECTED,
                       "dup"))
    with pytest.raises(ValueError, match="share the idempotency suffix"):
        _validate_declarations(rows)


def test_a_key_field_that_is_not_a_field_NAME_is_refused_at_import():
    """A key field is looked up in a payload, so anything that cannot BE a payload key is a
    declaration that can only fail at write time — where it would read as a caller error."""
    bad = Transition("X", frozenset(), AttemptState.PROPOSED, "x",
                     key_fields=("head sha",))
    with pytest.raises(ValueError, match="not a payload field name"):
        _validate_declarations((bad,))


def test_the_witness_and_the_write_boundary_share_ONE_stage_vocabulary():
    """Two hand-written copies would drift into a `stage` the validator accepts and the fold
    refuses — which does not reject the append, it WEDGES every later projection of the
    Attempt it landed on. `_validate_declarations` asserts this at import; asserting it here
    too pins that the check is wired to the real vocabulary and not to a local copy."""
    witness = _BY_EVENT["ReviewAborted"].witness
    assert witness is not None and witness.terms == REVIEW_STAGES


def test_release_and_terminality_stay_independent_at_the_PROJECTION_level():
    """The property `Transition` pins per row must survive the fold, or a consumer reading
    only the projection gets the shortcut back."""
    monitoring = project_attempt(_history(
        "Proposed", "ProposalVerified", "ClaimGranted", "Implementing",
        "EvaluationPassed", "PromotionRequested", "PromotionObserved"))
    assert monitoring.released_claim and not monitoring.is_terminal
    retained = project_attempt(_history(
        "Proposed", "ProposalVerified", "ClaimGranted", "Implementing",
        "EvaluationPassed", "PromotionRequested", "PromotionObserved", "Retained"))
    assert retained.is_terminal and not retained.released_claim
