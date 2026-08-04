"""Ownership-checked coordinator CAS (spec 025 slice 1A, Task 5).

Real git repositories: every claim and release goes through the lane log's CAS, so what
these tests exercise is the durable ownership record, not an in-memory lock.
"""

from __future__ import annotations

import subprocess

import pytest

from llmxive.self_improvement.claim import cas_claim
from llmxive.self_improvement.coordinator import cas_release, project_coordinator
from llmxive.self_improvement.events import COORDINATOR_STREAM
from llmxive.self_improvement.lane_log import (
    LaneLogConfig,
    LaneRevisionConflict,
    bootstrap_lane_log,
    read,
)
from llmxive.self_improvement.lifecycle import cas_attempt_transition
from tests.helpers.lane_lifecycle import TEST_CLAIM_TERMS

TS = "2026-07-24T00:00:00+00:00"


def _git(repo, *a):
    subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    bootstrap_lane_log(tmp_path, config=LaneLogConfig())
    return tmp_path


def _events(repo):
    return read(repo, COORDINATOR_STREAM)


def _claim(repo, *, problem_id, attempt_id, actor="d", timestamp=TS, **kw):
    """Claim through the real path, with the two transitions the table now requires.

    A claim is `proposal_verified → claimed`, so an Attempt with no events cannot be
    claimed at all — these 1A tests predate that and claimed from an empty Problem stream.
    The prelude is itself idempotent (each opening transition finds its own stored event),
    so a REPLAY of a claim can run it too and stay a replay.

    The prelude writes only to the PROBLEM stream, so every coordinator-stream count and
    revision assertion below still means what it meant."""
    for event_type in ("Proposed", "ProposalVerified"):
        cas_attempt_transition(repo, problem_id=problem_id, attempt_id=attempt_id,
                               event_type=event_type, payload={}, actor=actor,
                               clock=lambda: timestamp)
    return cas_claim(repo, problem_id=problem_id, attempt_id=attempt_id, actor=actor,
                     timestamp=timestamp, terms=TEST_CLAIM_TERMS, **kw)


def test_claim_when_idle_then_occupied_blocks_others(repo):
    c = _claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    assert c.acquired and (c.owner_problem_id, c.owner_attempt_id) == ("P1", "A1")
    assert c.coordinator.active_problem_id == "P1" and c.coordinator.lane_revision == 1
    with pytest.raises(LaneRevisionConflict, match="occupied"):
        _claim(repo, problem_id="P2", attempt_id="A2", actor="d", timestamp=TS)
    # the failed claim left NO record — a rejected CAS never appends
    assert len(_events(repo)) == 1


def test_claim_is_idempotent_on_reinvocation(repo):
    a = _claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    b = _claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)  # re-invoked
    assert b.coordinator.lane_revision == 1  # no duplicate event
    assert b.acquired  # the re-invoker DOES still hold it — idempotent, not superseded
    # Same claim, so the same generation — but NOT the same outcome record. `created`
    # separates "I took the lane" from "the lane was already mine", which a caller that
    # logs or meters claims needs and an equality assertion used to hide.
    assert a.created is True and b.created is False
    assert a.generation == b.generation == 1
    assert (a.acquired, a.owner_problem_id) == (b.acquired, b.owner_problem_id)
    assert len(_events(repo)) == 1


def test_a_replayed_claim_returns_successfully_while_someone_else_owns_the_lane(repo):
    """A ``cas_claim`` call that does not raise does NOT imply the caller owns the lane.

    The idempotency branch keys on "did THIS event already land", not "do I hold the claim
    now". So a replay that arrives after the claim was released and the lane re-granted
    short-circuits the precondition and returns NORMALLY — no ``LaneRevisionConflict`` —
    even though the caller owns nothing. That call is legitimately not an error (nothing
    was written, nothing is wrong), which is why the answer is REPORTED rather than raised:
    ``acquired`` is the ownership signal, and "it did not raise" is not. Pinned because the
    FR-035 reclaim (``ClaimExpired``) makes re-granting a routine event rather than a
    rarity, so this replay window stops being hypothetical.
    """
    _claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    cas_release(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    _claim(repo, problem_id="P2", attempt_id="A2", actor="d", timestamp=TS)

    # P1/A1's ORIGINAL claim call is retried (lost acknowledgement, crash-retry, replay).
    late = _claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)

    # It returned without raising -- and says so plainly: P1/A1 holds nothing.
    assert late.acquired is False
    assert (late.owner_problem_id, late.owner_attempt_id) == ("P2", "A2")
    # No duplicate claim record: the replay is inert, it just is not an ownership grant.
    assert len(_events(repo)) == 3
    assert sum(1 for e in _events(repo) if e.event_type == "ClaimAcquired") == 2


def test_a_release_from_a_non_owner_cannot_clear_the_active_claim(repo):
    # The F6 guard: a caller that believes it holds the lane must not be able to evict the
    # Attempt that actually does.
    _claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    with pytest.raises(LaneRevisionConflict, match="owner mismatch"):
        cas_release(repo, problem_id="PX", attempt_id="AX", actor="d", timestamp=TS)
    assert project_coordinator(_events(repo)).active_problem_id == "P1"


def test_a_release_reports_that_the_releaser_no_longer_holds_the_lane(repo):
    # `acquired` means "does the pair I named hold the lane NOW", so a successful release
    # reports False. Same field, same question, both entry points.
    _claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    out = cas_release(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    assert out.acquired is False
    assert (out.owner_problem_id, out.owner_attempt_id) == (None, None)


def test_a_release_naming_the_right_problem_but_the_wrong_attempt_is_refused(repo):
    # Ownership is the PAIR: an earlier Attempt on the same Problem is still a non-owner.
    c = _claim(repo, problem_id="P1", attempt_id="A2", actor="d", timestamp=TS)
    assert c.acquired  # A2 holds it...
    with pytest.raises(LaneRevisionConflict, match="owner mismatch"):
        cas_release(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    assert project_coordinator(_events(repo)).active_attempt_id == "A2"


def test_a_delayed_duplicate_release_does_not_disturb_a_newer_claim(repo):
    # P1/A1 claims and releases, P2/A2 claims, and then a DELAYED retry of P1/A1's release
    # arrives. It is reporting a fact that is already durable, not requesting a change, so
    # it neither appends a second record nor evicts P2/A2.
    _claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    cas_release(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    _claim(repo, problem_id="P2", attempt_id="A2", actor="d", timestamp=TS)

    late = cas_release(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    assert (late.owner_problem_id, late.owner_attempt_id) == ("P2", "A2")
    assert late.coordinator.lane_revision == 3 and len(_events(repo)) == 3  # no fourth record

    # and the true owner can still release
    c = cas_release(repo, problem_id="P2", attempt_id="A2", actor="d", timestamp=TS)
    assert c.coordinator.active_problem_id is None


def test_release_is_idempotent_for_the_true_owner(repo):
    _claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    cas_release(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    c = cas_release(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)  # re-invoked
    assert c.coordinator.active_problem_id is None
    assert c.coordinator.lane_revision == 2  # no third event


def test_the_lane_cycles_through_several_attempts(repo):
    # The singleton is a lock, not a one-shot: the durable record must support handoff.
    for problem, attempt in (("P1", "A1"), ("P2", "A2"), ("P3", "A3")):
        held = _claim(repo, problem_id=problem, attempt_id=attempt)
        assert held.acquired
        c = cas_release(repo, problem_id=problem, attempt_id=attempt, actor="d", timestamp=TS)
        assert c.coordinator.active_problem_id is None
    assert project_coordinator(_events(repo)).lane_revision == 6


def test_the_claim_record_carries_its_attempt_on_the_envelope(repo):
    # The payload's attempt_id is cross-checked against the envelope's at the write
    # boundary, so a claim that omitted the envelope id could never be appended at all.
    _claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    event = _events(repo)[0]
    assert event.attempt_id == "A1" and event.payload["attempt_id"] == "A1"
    assert event.problem_id == COORDINATOR_STREAM and event.payload["problem_id"] == "P1"
    # the store owns the anchors: seq 0 transforms lane revision 0 → 1
    assert (event.seq, event.expected_lane_revision, event.resulting_lane_revision) == (0, 0, 1)
