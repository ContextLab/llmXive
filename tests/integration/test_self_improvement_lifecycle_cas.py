"""The terminal-slot CAS (spec 025 slice 2, Task 7): `cas_attempt_transition`.

FR-035's "exactly one terminal per Attempt" cannot be enforced by the ref CAS alone — that
ORDERS two concurrent terminals, it does not reject either. The rejection happens in the
precondition, re-evaluated against the parent the commit is built on. And a row's declared
coordinator effects go in the SAME commit, so there is no interval in which an Attempt is
terminal while its claim is still held.

Real git repositories throughout — no mocks.
"""

from __future__ import annotations

import subprocess

import pytest

from llmxive.self_improvement.coordinator import project_coordinator
from llmxive.self_improvement.events import COORDINATOR_STREAM
from llmxive.self_improvement.lane_log import (
    LANE_REF,
    LaneLogConfig,
    LaneRevisionConflict,
    append,
    bootstrap_lane_log,
    read,
)
from llmxive.self_improvement.lifecycle import (
    _COORDINATOR_EFFECTS,
    TRANSITIONS,
    AttemptState,
    IllegalTransition,
    cas_attempt_transition,
    project_attempt,
)
from tests.helpers.lane_lifecycle import Clock, seed_claim


def _git(repo, *a) -> str:
    return subprocess.run(
        ["git", *a], cwd=str(repo), check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "local"
    subprocess.run(["git", "init", "-q", str(r)], check=True)
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    bootstrap_lane_log(r, config=LaneLogConfig())
    return r


@pytest.fixture
def clock():
    return Clock()


def _apply(repo, event_type, *, problem_id="P1", attempt_id="A1", payload=None,
           actor="runner-1", clock=None, **seams):
    return cas_attempt_transition(
        repo, problem_id=problem_id, attempt_id=attempt_id, event_type=event_type,
        payload=payload or {}, actor=actor, clock=clock or Clock(), **seams)


def _attempt(repo, problem_id="P1", attempt_id="A1"):
    return project_attempt([e for e in read(repo, problem_id) if e.attempt_id == attempt_id])


def _counts(repo, *problem_ids) -> dict[str, int]:
    return {s: len(read(repo, s)) for s in (COORDINATOR_STREAM, *problem_ids)}


def _paths_in_tip(repo) -> list[str]:
    """The blobs the ref's LAST commit added — how "one transaction" is checked from the
    outside rather than taken on the writer's word."""
    out = _git(repo, "show", "--name-only", "--format=", LANE_REF)
    return [line for line in out.splitlines() if line.strip()]


# --- 1-3: the ordinary contract ------------------------------------------------------

def test_a_legal_transition_appends_and_advances_the_projection(repo, clock):
    _apply(repo, "Proposed", clock=clock)
    outcome = _apply(repo, "ProposalVerified", clock=clock)
    assert outcome.created is True
    assert outcome.projection.state is AttemptState.PROPOSAL_VERIFIED
    assert _attempt(repo).state is AttemptState.PROPOSAL_VERIFIED


def test_an_illegal_transition_raises_and_appends_NOTHING(repo, clock):
    _apply(repo, "Proposed", clock=clock)
    before = _counts(repo, "P1")
    with pytest.raises(LaneRevisionConflict, match="illegal from 'proposed'"):
        _apply(repo, "Implementing", clock=clock)
    # A rejected CAS never writes. Asserting the exception alone would pass just as well
    # against a writer that appended and then complained.
    assert _counts(repo, "P1") == before


def test_an_Attempt_cannot_be_OPENED_by_a_transition_that_is_not_Proposed(repo, clock):
    """The empty-history branch. `from_states` is empty for exactly one row, and every
    other row reaching a stream with no events for this Attempt is a caller that invented
    an Attempt id — nothing may be written under it."""
    with pytest.raises(LaneRevisionConflict, match="cannot open with this event"):
        _apply(repo, "Implementing", clock=clock)
    assert _counts(repo, "P1") == {COORDINATOR_STREAM: 0, "P1": 0}


def test_re_invoking_the_same_transition_is_idempotent(repo, clock):
    _apply(repo, "Proposed", clock=clock)
    first = _apply(repo, "ProposalVerified", clock=clock)
    before = _counts(repo, "P1")
    second = _apply(repo, "ProposalVerified", clock=clock)
    assert first.created is True and second.created is False
    assert _counts(repo, "P1") == before
    assert second.projection == first.projection


# --- 4-6: exactly one terminal ---------------------------------------------------------

def test_two_DIFFERENT_terminals_racing_leave_exactly_one(repo, clock):
    """FR-035's core invariant. Ref-level CAS ORDERS two concurrent terminals; it rejects
    neither. The rejection has to happen in the precondition, or an Attempt ends twice."""
    _apply(repo, "Proposed", clock=clock)
    _apply(repo, "ReviewAborted", payload={"stage": "proposal", "cause": "wall_clock",
                                           "unresolved_dispatches": []}, clock=clock)
    with pytest.raises(LaneRevisionConflict, match="already terminal at 'review_aborted'"):
        _apply(repo, "ImplementationFailed", clock=clock)
    terminals = [e for e in read(repo, "P1")
                 if e.event_type in {"ReviewAborted", "ImplementationFailed"}]
    assert [e.event_type for e in terminals] == ["ReviewAborted"]
    assert _attempt(repo).state is AttemptState.REVIEW_ABORTED


def test_the_LOSERS_replay_after_losing_still_raises(repo, clock):
    """It did not land, so it must not come to look as though it had. The replay branch
    keys on the loser's OWN event id — absent — so this takes the fresh path and meets the
    terminal check again."""
    _apply(repo, "Proposed", clock=clock)
    _apply(repo, "ReviewAborted", payload={"stage": "proposal", "cause": "wall_clock",
                                           "unresolved_dispatches": []}, clock=clock)
    for _ in range(2):
        with pytest.raises(LaneRevisionConflict, match="already terminal"):
            _apply(repo, "ImplementationFailed", clock=clock)
    assert _attempt(repo).state is AttemptState.REVIEW_ABORTED


def test_a_transition_whose_from_states_no_longer_match_raises(repo, clock):
    """Another writer advanced the Attempt while this caller was deciding to reject it. The
    precondition is evaluated at the parent the commit is built on, so a decision taken at
    `proposal_verified` cannot overwrite an Attempt that has since started implementing."""
    seed_claim(repo, clock=clock)
    _apply(repo, "Implementing", clock=clock)
    with pytest.raises(LaneRevisionConflict, match="illegal from 'implementing'"):
        _apply(repo, "Rejected", clock=clock)


def test_the_seeded_claim_is_indistinguishable_from_one_written_through_this_path(repo, clock):
    """`seed_claim` hand-writes the grant at the id this path derives, so re-issuing it here
    is an ordinary idempotent replay rather than a second grant. That is the property that
    lets Task 8 replace the fixture with the real `cas_claim` and leave these tests green —
    if it were distinguishable, every claim-holding case would be asserting against the
    fixture instead of against the claim's shape."""
    grant = seed_claim(repo, clock=clock)
    before = _counts(repo, "P1")
    outcome = _apply(repo, "ClaimGranted", clock=clock, payload={
        # The grant's COMPLETE key, taken from the fixture's own record: re-deriving it here
        # from remembered values would test this test's memory, not the derivation.
        "claim_generation": grant.payload["claim_generation"],
        "lane_revision": grant.payload["lane_revision"]})
    assert outcome.created is False
    assert outcome.projection.state is AttemptState.CLAIMED
    assert outcome.projection.claim_generation == 1
    assert _counts(repo, "P1") == before


# --- 7-8d: the conditional coordinator effect -----------------------------------------

def test_a_terminal_by_the_claim_HOLDER_frees_the_lane_in_ONE_commit(repo, clock):
    """Matrix row 2. Not an optimization: two appends would leave a window in which the
    Attempt is terminal and its claim still held, and rev 23 declines to add the
    compensating transition that window would need."""
    seed_claim(repo, clock=clock)
    _apply(repo, "Implementing", clock=clock)
    _apply(repo, "ImplementationFailed", clock=clock)

    assert _attempt(repo).state is AttemptState.IMPL_FAILED
    assert project_coordinator(read(repo, COORDINATOR_STREAM)).active_problem_id is None
    paths = _paths_in_tip(repo)
    assert len(paths) == 2, paths
    assert any(f"/{COORDINATOR_STREAM}/" in p for p in paths)
    assert any("/P1/" in p for p in paths)


def test_a_PRE_CLAIM_terminal_by_a_non_holder_writes_no_coordinator_event(repo, clock):
    """A `†` row reachable from a state that holds nothing. The dagger marks "must not
    leave the lane occupied", not "always mutates the coordinator" — so a terminal here
    must never evict the Attempt that actually holds the claim."""
    seed_claim(repo, problem_id="P2", attempt_id="A2", clock=clock)
    before = read(repo, COORDINATOR_STREAM)

    _apply(repo, "Proposed", clock=clock)
    _apply(repo, "ReviewAborted", payload={"stage": "proposal", "cause": "wall_clock",
                                           "unresolved_dispatches": []}, clock=clock)

    assert _attempt(repo).state is AttemptState.REVIEW_ABORTED
    assert read(repo, COORDINATOR_STREAM) == before
    holder = project_coordinator(before)
    assert (holder.active_problem_id, holder.active_attempt_id) == ("P2", "A2")


def _drop_the_coordinators_claim(repo, clock, *, problem_id="P1", attempt_id="A1"):
    """Build the half-state no lane API will produce: the Attempt believes it holds the
    lane, the coordinator says otherwise. A direct `append` is the only way in."""
    from llmxive.self_improvement.events import coord_event
    events = read(repo, COORDINATOR_STREAM)
    append(repo, coord_event("ClaimReleased", problem_id=problem_id, attempt_id=attempt_id,
                             payload={"problem_id": problem_id, "attempt_id": attempt_id},
                             actor="intruder", timestamp=clock()),
           expected_revision=len(events))


def test_a_claim_holder_whose_coordinator_ownership_is_MISSING_is_refused_entirely(repo, clock):
    """The case a coordinator-derived `holds` gets wrong.

    Reading "does this transition owe a release?" from the COORDINATOR would answer "not
    held → nothing to release" and write the terminal ALONE — manufacturing exactly the
    half-state the matrix forbids: a terminal whose row declares a release, from a
    claim-holding state, with no release. Reading it from the ATTEMPT's own timeline turns
    that divergence into a refusal."""
    seed_claim(repo, clock=clock)
    _apply(repo, "Implementing", clock=clock)
    _drop_the_coordinators_claim(repo, clock)
    before = _counts(repo, "P1")

    with pytest.raises(LaneRevisionConflict, match="holds the lane, but the coordinator"):
        _apply(repo, "ImplementationFailed", clock=clock)

    assert _attempt(repo).state is AttemptState.IMPLEMENTING
    assert _counts(repo, "P1") == before


def test_the_same_refusal_when_coordinator_ownership_is_DIFFERENT(repo, clock):
    """Two distinct wrong outcomes are possible here — write the terminal alone, or release
    the WRONG claim — so both are asserted. A refusal must not become an eviction."""
    seed_claim(repo, clock=clock)
    _apply(repo, "Implementing", clock=clock)
    _drop_the_coordinators_claim(repo, clock)
    seed_claim(repo, problem_id="P2", attempt_id="A2", clock=clock)
    before = _counts(repo, "P1", "P2")

    with pytest.raises(LaneRevisionConflict, match="holds the lane, but the coordinator"):
        _apply(repo, "ImplementationFailed", clock=clock)

    assert _attempt(repo).state is AttemptState.IMPLEMENTING
    assert _counts(repo, "P1", "P2") == before
    holder = project_coordinator(read(repo, COORDINATOR_STREAM))
    assert (holder.active_problem_id, holder.active_attempt_id) == ("P2", "A2")


def test_a_claim_status_that_changes_while_the_writes_are_built_loses_the_CAS(repo, clock):
    """`ReviewAborted` is legal from `proposed` (holds nothing) AND from `implementing`
    (holds the lane), so a stale read builds a SINGLE-stream write that would still satisfy
    `from_states` at a parent where the Attempt is claimed — landing a terminal on a live
    claim.

    What rejects it here is the expected-revision pin on the Problem stream: the Attempt's
    state cannot change without its stream growing. The applicability re-check inside the
    precondition is defence in depth behind that pin, not what fires in this case — see the
    note in `cas_attempt_transition`. Losing is a rebuild-and-retry, not an error, so the
    retry is asserted too."""
    _apply(repo, "Proposed", clock=clock)
    before = _counts(repo, "P1")

    def _advance():
        seed_claim(repo, clock=clock, already_proposed=True)
        _apply(repo, "Implementing", clock=clock)

    with pytest.raises(LaneRevisionConflict):
        _apply(repo, "ReviewAborted",
               payload={"stage": "proposal", "cause": "wall_clock",
                        "unresolved_dispatches": []},
               clock=clock, _after_parent=_advance)

    assert _counts(repo, "P1") != before   # the seam's own writes landed
    assert not [e for e in read(repo, "P1") if e.event_type == "ReviewAborted"]

    retried = _apply(repo, "ReviewAborted",
                     payload={"stage": "patch", "cause": "wall_clock",
                              "unresolved_dispatches": []}, clock=clock)
    assert retried.projection.state is AttemptState.REVIEW_ABORTED
    assert project_coordinator(read(repo, COORDINATOR_STREAM)).active_problem_id is None
    assert len(_paths_in_tip(repo)) == 2   # BOTH events, one commit


# --- 9-12: atomicity, the registry, and the non-terminal release ------------------------

def test_a_crash_between_the_halves_is_impossible(repo, clock):
    """`_before_ref_update` is the last seam before the commit becomes visible. Neither
    half may survive it."""
    seed_claim(repo, clock=clock)
    _apply(repo, "Implementing", clock=clock)
    before = _counts(repo, "P1")

    def _boom():
        raise RuntimeError("crash before the ref moved")

    with pytest.raises(RuntimeError, match="crash before the ref moved"):
        _apply(repo, "ImplementationFailed", clock=clock, _before_ref_update=_boom)

    assert _attempt(repo).state is AttemptState.IMPLEMENTING
    assert _counts(repo, "P1") == before
    holder = project_coordinator(read(repo, COORDINATOR_STREAM))
    assert (holder.active_problem_id, holder.active_attempt_id) == ("P1", "A1")


def test_a_concurrent_coordinator_write_defeats_a_claim_holding_transition(repo, clock):
    """The coordinator stream's revision is PINNED whenever this transaction touches it, so
    the release half is built against a coordinator state the caller actually observed —
    "deciding against the exact parent its commit is built on", which is the property the
    spec's one-ref-many-subtrees paragraph rests on.

    Stricter than the ownership re-check alone: the write below (the promotion gate) does
    not change who holds the lane, so ownership still passes. Losing here is a
    rebuild-and-retry, not an error, and the retry is asserted."""
    from llmxive.self_improvement.events import Event

    seed_claim(repo, clock=clock)
    _apply(repo, "Implementing", clock=clock)

    def _unrelated_coordinator_write():
        events = read(repo, COORDINATOR_STREAM)
        append(repo, Event(event_id="breaker-flip", event_type="PromotionEnabledSet",
                           problem_id=COORDINATOR_STREAM, actor="operator",
                           payload={"promotion_enabled": False}, timestamp=clock(),
                           attempt_id=None),
               expected_revision=len(events))

    with pytest.raises(LaneRevisionConflict, match="stale revision"):
        _apply(repo, "ImplementationFailed", clock=clock,
               _after_parent=_unrelated_coordinator_write)

    assert _attempt(repo).state is AttemptState.IMPLEMENTING
    assert _apply(repo, "ImplementationFailed", clock=clock).created is True
    assert project_coordinator(read(repo, COORDINATOR_STREAM)).active_problem_id is None


def test_every_declared_effect_has_a_builder():
    """Two halves of one declaration. A row naming an effect nobody builds would raise
    `KeyError` in production at the moment it fired; a builder no row names is dead."""
    declared = {name for t in TRANSITIONS for name in t.coordinator_effects}
    assert declared == set(_COORDINATOR_EFFECTS)


def _to_promotion_requested(repo, clock):
    seed_claim(repo, clock=clock)
    _apply(repo, "Implementing", clock=clock)
    _apply(repo, "EvaluationPassed", payload={"head_sha": "a" * 40}, clock=clock)
    _apply(repo, "PromotionRequested", payload={"head_sha": "a" * 40}, clock=clock)


def test_a_NON_TERMINAL_transition_that_declares_effects_still_emits_them(repo, clock):
    """Matrix row 4. `PromotionObserved` releases WITHOUT being terminal — the merge landed
    and the monitoring window is unattended, so holding the singleton through it would
    block every other Problem. A `transition.terminal`-gated release skips this silently,
    which is the defect the matrix was written to prevent."""
    _to_promotion_requested(repo, clock)
    outcome = _apply(repo, "PromotionObserved", payload={"head_sha": "a" * 40}, clock=clock)

    assert outcome.projection.state is AttemptState.MONITORING
    assert not outcome.projection.is_terminal
    assert project_coordinator(read(repo, COORDINATOR_STREAM)).active_problem_id is None
    assert len(_paths_in_tip(repo)) == 3   # all THREE events, one commit


def test_effects_are_emitted_in_the_ROWS_declared_order(repo, clock):
    """Pins the WRITER against the table. Whether the fold REJECTS the reversal is Task
    12's case — until its ownership precondition exists, `project_coordinator` accepts
    either order, so asserting rejection here would be a test that cannot fail."""
    _to_promotion_requested(repo, clock)
    _apply(repo, "PromotionObserved", payload={"head_sha": "a" * 40}, clock=clock)

    row = next(t for t in TRANSITIONS if t.event == "PromotionObserved")
    written = [e for e in read(repo, COORDINATOR_STREAM) if e.attempt_id == "A1"
               and e.event_type in row.coordinator_effects]
    assert [e.event_type for e in written] == list(row.coordinator_effects)
    assert written[0].seq < written[1].seq


# --- the paths that are not this one ---------------------------------------------------

@pytest.mark.parametrize("event_type, why", [
    ("ClaimHeartbeat", "moves no state and is not written through this path"),
    ("ClaimExpired", "written by cas_reclaim, not by this path"),
    ("SomethingFromTheFuture", "unknown Attempt event"),
])
def test_events_this_path_must_refuse(repo, clock, event_type, why):
    """A heartbeat moves no state; a reclaim's preconditions ARE the reclaim and would be
    skipped here. Both are `IllegalTransition` (a caller bug), never a CAS conflict."""
    _apply(repo, "Proposed", clock=clock)
    with pytest.raises(IllegalTransition, match=why):
        _apply(repo, event_type, clock=clock)


# --- the COMPLETE idempotency key -------------------------------------------------------
#
# The spec keys several rows on a payload field as well as the suffix —
# `(attempt_id,"revert-req",reason)`, `(attempt_id,"eval",head_sha)`. Deriving the id from
# the suffix alone makes the key a PREFIX of itself, and these are the two ways that bites:
# a legal repeat silently replays the earlier operation, and a conflicting retry reports
# success for an operation nobody asked for.


def _to_monitoring(repo, clock, head_sha="a" * 40):
    _to_promotion_requested(repo, clock)
    _apply(repo, "PromotionObserved", payload={"head_sha": head_sha}, clock=clock)


def test_a_SECOND_revert_request_after_an_abort_is_a_NEW_request(repo, clock):
    """The row the incomplete key actually lost. `RevertAborted` returns the Attempt to
    `monitoring`, so a second `RevertRequested` under a different reason is an ordinary
    next operation — not a retry of the first. Keyed on the suffix alone it derived the
    FIRST request's id, was found in the history, and came back `created=False` with the
    Attempt still in `monitoring`: a revert nobody would ever issue, reported as done."""
    _to_monitoring(repo, clock)
    first = _apply(repo, "RevertRequested", payload={"reason": "regression-A"}, clock=clock)
    _apply(repo, "RevertAborted", clock=clock)
    assert _attempt(repo).state is AttemptState.MONITORING

    second = _apply(repo, "RevertRequested", payload={"reason": "regression-B"}, clock=clock)

    assert second.created is True
    assert second.projection.state is AttemptState.REVERT_REQUESTED
    requests = [e for e in read(repo, "P1") if e.event_type == "RevertRequested"]
    assert [e.payload["reason"] for e in requests] == ["regression-A", "regression-B"]
    assert first.projection != second.projection


def test_repeating_a_revert_request_under_the_SAME_reason_is_idempotent(repo, clock):
    """The other half of the same property: completing the key must not DEFEAT idempotency.
    Same complete key → same id → the ordinary lost-acknowledgement replay."""
    _to_monitoring(repo, clock)
    first = _apply(repo, "RevertRequested", payload={"reason": "regression-A"}, clock=clock)
    before = _counts(repo, "P1")

    second = _apply(repo, "RevertRequested", payload={"reason": "regression-A"}, clock=clock)

    assert first.created is True and second.created is False
    assert second.projection == first.projection
    assert _counts(repo, "P1") == before


def test_a_retry_under_a_CONFLICTING_head_sha_is_refused_not_replayed(repo, clock):
    """A one-shot row, where the incomplete key was quieter but no safer. `EvaluationPassed`
    cannot legally repeat, so the question is what a retry bearing a DIFFERENT `head_sha`
    means: it is a different operation — this commit passed evaluation, not that one — and
    the honest answer is refusal. The old key answered `created=False`, i.e. "your call
    landed", for a commit the lane never evaluated."""
    seed_claim(repo, clock=clock)
    _apply(repo, "Implementing", clock=clock)
    _apply(repo, "EvaluationPassed", payload={"head_sha": "a" * 40}, clock=clock)
    before = _counts(repo, "P1")

    with pytest.raises(LaneRevisionConflict, match="illegal from 'promoting'"):
        _apply(repo, "EvaluationPassed", payload={"head_sha": "b" * 40}, clock=clock)

    assert _counts(repo, "P1") == before
    passed = [e for e in read(repo, "P1") if e.event_type == "EvaluationPassed"]
    assert [e.payload["head_sha"] for e in passed] == ["a" * 40]


def test_a_payload_MISSING_a_declared_key_field_is_refused(repo, clock):
    """No key, no operation. Falling back to the shorter key is precisely the collision
    above, so this is `IllegalTransition` at the boundary — a caller bug, not a CAS race —
    and nothing is appended."""
    seed_claim(repo, clock=clock)
    _apply(repo, "Implementing", clock=clock)
    before = _counts(repo, "P1")

    with pytest.raises(IllegalTransition, match="keyed by 'head_sha'"):
        _apply(repo, "EvaluationPassed", clock=clock)

    assert _counts(repo, "P1") == before
    assert _attempt(repo).state is AttemptState.IMPLEMENTING
