"""Ownership-checked coordinator CAS (spec 025 slice 1A, Task 5).

Real git repositories: every claim and release goes through the lane log's CAS, so what
these tests exercise is the durable ownership record, not an in-memory lock.
"""

from __future__ import annotations

import subprocess

import pytest

from llmxive.self_improvement.coordinator import cas_claim, cas_release, project_coordinator
from llmxive.self_improvement.events import COORDINATOR_STREAM
from llmxive.self_improvement.lane_log import (
    LaneLogConfig,
    LaneRevisionConflict,
    bootstrap_lane_log,
    read,
)

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


def test_claim_when_idle_then_occupied_blocks_others(repo):
    c = cas_claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    assert c.active_problem_id == "P1" and c.lane_revision == 1
    with pytest.raises(LaneRevisionConflict, match="occupied"):
        cas_claim(repo, problem_id="P2", attempt_id="A2", actor="d", timestamp=TS)
    # the failed claim left NO record — a rejected CAS never appends
    assert len(_events(repo)) == 1


def test_claim_is_idempotent_on_reinvocation(repo):
    a = cas_claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    b = cas_claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)  # re-invoked
    assert a == b and b.lane_revision == 1  # no duplicate event, same projection
    assert len(_events(repo)) == 1


def test_a_replayed_claim_returns_successfully_while_someone_else_owns_the_lane(repo):
    """A successful ``cas_claim`` call does NOT imply the caller currently owns the lane.

    The idempotency branch keys on "did THIS event already land", not "do I hold the claim
    now". So a replay that arrives after the claim was released and the lane re-granted
    short-circuits the precondition and returns NORMALLY — no ``LaneRevisionConflict`` —
    even though the caller owns nothing. Callers MUST check the returned projection;
    "it did not raise" is not an ownership signal. Pinned because the FR-035 reclaim
    (``ClaimExpired``) makes re-granting a routine event rather than a rarity, so this
    replay window stops being hypothetical.
    """
    cas_claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    cas_release(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    cas_claim(repo, problem_id="P2", attempt_id="A2", actor="d", timestamp=TS)

    # P1/A1's ORIGINAL claim call is retried (lost acknowledgement, crash-retry, replay).
    late = cas_claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)

    # It returned without raising -- and P1/A1 does not own the lane.
    assert (late.active_problem_id, late.active_attempt_id) == ("P2", "A2")
    # The projection is NOT "the same projection" the original call saw, either.
    assert late.active_attempt_id != "A1"
    # No duplicate claim record: the replay is inert, it just is not an ownership grant.
    assert len(_events(repo)) == 3
    assert sum(1 for e in _events(repo) if e.event_type == "ClaimAcquired") == 2


def test_a_release_from_a_non_owner_cannot_clear_the_active_claim(repo):
    # The F6 guard: a caller that believes it holds the lane must not be able to evict the
    # Attempt that actually does.
    cas_claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    with pytest.raises(LaneRevisionConflict, match="owner mismatch"):
        cas_release(repo, problem_id="PX", attempt_id="AX", actor="d", timestamp=TS)
    assert project_coordinator(_events(repo)).active_problem_id == "P1"


def test_a_release_naming_the_right_problem_but_the_wrong_attempt_is_refused(repo):
    # Ownership is the PAIR: an earlier Attempt on the same Problem is still a non-owner.
    cas_claim(repo, problem_id="P1", attempt_id="A2", actor="d", timestamp=TS)
    with pytest.raises(LaneRevisionConflict, match="owner mismatch"):
        cas_release(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    assert project_coordinator(_events(repo)).active_attempt_id == "A2"


def test_a_delayed_duplicate_release_does_not_disturb_a_newer_claim(repo):
    # P1/A1 claims and releases, P2/A2 claims, and then a DELAYED retry of P1/A1's release
    # arrives. It is reporting a fact that is already durable, not requesting a change, so
    # it neither appends a second record nor evicts P2/A2.
    cas_claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    cas_release(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    cas_claim(repo, problem_id="P2", attempt_id="A2", actor="d", timestamp=TS)

    late = cas_release(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    assert (late.active_problem_id, late.active_attempt_id) == ("P2", "A2")
    assert late.lane_revision == 3 and len(_events(repo)) == 3  # no fourth record

    # and the true owner can still release
    c = cas_release(repo, problem_id="P2", attempt_id="A2", actor="d", timestamp=TS)
    assert c.active_problem_id is None


def test_release_is_idempotent_for_the_true_owner(repo):
    cas_claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    cas_release(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    c = cas_release(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)  # re-invoked
    assert c.active_problem_id is None and c.lane_revision == 2  # no third event


def test_the_lane_cycles_through_several_attempts(repo):
    # The singleton is a lock, not a one-shot: the durable record must support handoff.
    for problem, attempt in (("P1", "A1"), ("P2", "A2"), ("P3", "A3")):
        cas_claim(repo, problem_id=problem, attempt_id=attempt, actor="d", timestamp=TS)
        c = cas_release(repo, problem_id=problem, attempt_id=attempt, actor="d", timestamp=TS)
        assert c.active_problem_id is None
    assert project_coordinator(_events(repo)).lane_revision == 6


def test_the_claim_record_carries_its_attempt_on_the_envelope(repo):
    # The payload's attempt_id is cross-checked against the envelope's at the write
    # boundary, so a claim that omitted the envelope id could never be appended at all.
    cas_claim(repo, problem_id="P1", attempt_id="A1", actor="d", timestamp=TS)
    event = _events(repo)[0]
    assert event.attempt_id == "A1" and event.payload["attempt_id"] == "A1"
    assert event.problem_id == COORDINATOR_STREAM and event.payload["problem_id"] == "P1"
    # the store owns the anchors: seq 0 transforms lane revision 0 → 1
    assert (event.seq, event.expected_lane_revision, event.resulting_lane_revision) == (0, 0, 1)
