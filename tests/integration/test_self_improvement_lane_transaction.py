"""Cross-stream lane transactions (spec 025 slice 2, Task 3).

`append_many` is what makes a coordinator/Problem mutation ONE commit under ONE ref
compare-and-swap. Every case here asks whether an observer can see half of one, or whether
a precondition that read one stream while writing another was BINDING.

Real git repositories throughout — no mocks.
"""

from __future__ import annotations

import subprocess

import pytest

from llmxive.git_event_log import GitLogError
from llmxive.self_improvement.events import COORDINATOR_STREAM, Event
from llmxive.self_improvement.lane_log import (
    LANE_REF,
    LaneLogConfig,
    LaneRevisionConflict,
    append,
    append_many,
    bootstrap_lane_log,
    read,
)


def _git(repo, *a) -> str:
    return subprocess.run(
        ["git", *a], cwd=str(repo), check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def bare_remote(tmp_path):
    r = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(r)], check=True)
    return r


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "local"
    subprocess.run(["git", "init", "-q", str(r)], check=True)
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    bootstrap_lane_log(r, config=LaneLogConfig())
    return r


@pytest.fixture
def clone(tmp_path, bare_remote):
    """A clone whose lane ref lives on the remote — the configuration in which the PUSH is
    the commit point, which is what the durability cases are about."""
    dst = tmp_path / "c"
    subprocess.run(["git", "clone", "-q", str(bare_remote), str(dst)], check=True)
    _git(dst, "config", "user.email", "t@t")
    _git(dst, "config", "user.name", "t")
    bootstrap_lane_log(dst, config=LaneLogConfig(remote="origin"))
    return dst


_REMOTE = LaneLogConfig(remote="origin")


#: A claim's generation + terms. These transport tests are about the COMMIT — one commit,
#: two streams, binding preconditions — but the record they move must still be one the write
#: boundary accepts, or they would be exercising the store with something it refuses.
_CLAIM_BODY = {"claim_generation": 1, "lane_revision": 0, "claim_expiry_s": 13200,
               "max_claim_hold_time_s": 13200, "max_clock_skew_s": 300, "policy_version": 1}


def _coord(eid: str, *, rev: int = 0, attempt_id: str = "A1") -> Event:
    return Event(event_id=eid, event_type="ClaimAcquired", problem_id=COORDINATOR_STREAM,
                 actor="a",
                 payload={"problem_id": "prob-1", "attempt_id": attempt_id, **_CLAIM_BODY},
                 timestamp=f"2026-07-31T00:00:{rev:02d}+00:00", attempt_id=attempt_id,
                 expected_lane_revision=rev)


def _prob(eid: str, *, rev: int = 0, problem_id: str = "prob-1",
          attempt_id: str = "A1") -> Event:
    return Event(event_id=eid, event_type="Proposed", problem_id=problem_id, actor="a",
                 payload={"problem_id": problem_id, "attempt_id": attempt_id},
                 timestamp=f"2026-07-31T00:00:{rev:02d}+00:00",
                 attempt_id=attempt_id, expected_problem_revision=rev)


def _commit_count(repo, ref: str = LANE_REF) -> int:
    return int(_git(repo, "rev-list", "--count", ref))


def _remote_ids(bare, stream: str) -> list[str]:
    """Event ids on a stream as the REMOTE has them — read without going through the
    local clone at all, so a local ref that never moved cannot mask the answer."""
    listing = _git(bare, "ls-tree", "--name-only",
                   f"{LANE_REF}:self-improvement/events/{stream}")
    return sorted(name.removesuffix(".json") for name in listing.splitlines() if name)


# ---- 1. one commit, two streams, correct anchors ----


def test_a_coordinator_and_a_problem_event_land_in_ONE_transaction(repo):
    result = append_many(
        repo, [_coord("c1"), _prob("p1")],
        expected_revisions={COORDINATOR_STREAM: 0, "prob-1": 0},
    )
    assert result.created is True
    assert result.seqs == {(COORDINATOR_STREAM, "c1"): 0, ("prob-1", "p1"): 0}

    coord = read(repo, COORDINATOR_STREAM)
    prob = read(repo, "prob-1")
    assert [e.event_id for e in coord] == ["c1"]
    assert [e.event_id for e in prob] == ["p1"]
    assert (coord[0].seq, prob[0].seq) == (0, 0)
    # Each event carries its OWN scope's anchors and NULLs the other — `_finalize` is
    # reused unchanged, and widening it to fill both scopes would fail validation.
    assert (coord[0].expected_lane_revision, coord[0].resulting_lane_revision) == (0, 1)
    assert coord[0].expected_problem_revision is None
    assert (prob[0].expected_problem_revision, prob[0].resulting_problem_revision) == (0, 1)
    assert prob[0].expected_lane_revision is None


# ---- 2. both blobs, one commit ----


def test_both_blobs_were_added_by_the_SAME_commit(repo):
    result = append_many(
        repo, [_coord("c1"), _prob("p1")],
        expected_revisions={COORDINATOR_STREAM: 0, "prob-1": 0},
    )
    assert _git(repo, "rev-parse", LANE_REF) == result.commit
    added = _git(repo, "show", "--name-only", "--format=", result.commit).splitlines()
    assert sorted(n for n in added if n) == [
        "self-improvement/events/coordinator/c1.json",
        "self-improvement/events/prob-1/p1.json",
    ]
    assert _commit_count(repo) == 2  # genesis + this transaction


# ---- 3. a stale revision on EITHER stream defeats the whole transaction ----


@pytest.mark.parametrize("stale", [COORDINATOR_STREAM, "prob-1"])
def test_a_stale_expected_revision_on_either_stream_writes_NOTHING(repo, stale):
    revisions = {COORDINATOR_STREAM: 0, "prob-1": 0}
    revisions[stale] = 7  # a revision neither stream is at
    with pytest.raises(LaneRevisionConflict, match="stale revision"):
        append_many(repo, [_coord("c1"), _prob("p1")], expected_revisions=revisions)
    assert read(repo, COORDINATOR_STREAM) == [] and read(repo, "prob-1") == []
    assert _commit_count(repo) == 1


# ---- 4. a cross-stream precondition is BINDING ----


def test_a_precondition_reading_the_COORDINATOR_blocks_a_PROBLEM_write(repo):
    """The capability the first draft of this plan wrongly believed impossible: the
    predicate reads one stream and writes another, at the SAME parent the commit is built
    on, so the read is a precondition rather than an observation."""
    append_many(repo, [_coord("c1")], expected_revisions={COORDINATOR_STREAM: 0})
    seen: dict[str, list[str]] = {}

    def _refuse_if_lane_held(observed: dict[str, list[Event]]) -> tuple[bool, str]:
        seen.update({k: [e.event_id for e in v] for k, v in observed.items()})
        if observed[COORDINATOR_STREAM]:
            return (False, "lane already claimed")
        return (True, "")

    with pytest.raises(LaneRevisionConflict, match="lane already claimed"):
        append_many(repo, [_prob("p1")],
                    expected_revisions={COORDINATOR_STREAM: 1, "prob-1": 0},
                    precondition=_refuse_if_lane_held)
    # The refused write touched a stream the predicate never wrote to, and still lost.
    assert seen == {COORDINATOR_STREAM: ["c1"], "prob-1": []}
    assert read(repo, "prob-1") == []


def test_the_precondition_sees_streams_it_only_READS(repo):
    """`expected_revisions` may name a stream no event is written to; it is still observed
    and still revision-checked. That is how a claim decision reads the coordinator."""
    append(repo, _prob("p0"), expected_revision=0)
    observed_keys = {}

    def _capture(observed):
        observed_keys.update({k: len(v) for k, v in observed.items()})
        return (True, "")

    append_many(repo, [_coord("c1")],
                expected_revisions={COORDINATOR_STREAM: 0, "prob-1": 1},
                precondition=_capture)
    assert observed_keys == {COORDINATOR_STREAM: 0, "prob-1": 1}


# ---- 5. the crash seams ----


def test_a_crash_before_the_ref_moves_leaves_NEITHER_stream(repo):
    """The atomicity case. Against a non-atomic implementation — two sequential appends —
    the coordinator event would be durable and the Problem event missing."""
    def boom():
        raise RuntimeError("crash: pre ref-update")

    with pytest.raises(RuntimeError, match="pre ref-update"):
        append_many(repo, [_coord("c1"), _prob("p1")],
                    expected_revisions={COORDINATOR_STREAM: 0, "prob-1": 0},
                    _before_ref_update=boom)
    assert read(repo, COORDINATOR_STREAM) == [] and read(repo, "prob-1") == []
    assert _commit_count(repo) == 1


def test_a_crash_after_the_parent_is_fixed_leaves_NEITHER_stream(repo):
    def boom():
        raise RuntimeError("crash: parent fixed")

    with pytest.raises(RuntimeError, match="parent fixed"):
        append_many(repo, [_coord("c1"), _prob("p1")],
                    expected_revisions={COORDINATOR_STREAM: 0, "prob-1": 0},
                    _after_parent=boom)
    assert read(repo, COORDINATOR_STREAM) == [] and read(repo, "prob-1") == []


def test_a_crash_after_the_PUSH_leaves_the_transaction_durable_on_the_remote(
    clone, bare_remote
):
    """The commit point is the push, so this crash is on its far side and must assert
    PRESENCE — and BOTH events, never a subset. The lane wrapper inherits this from the
    core; inheriting it silently is how a plan comes to state the opposite."""
    def die():
        raise RuntimeError("runner killed after the push")

    with pytest.raises(RuntimeError, match="runner killed"):
        append_many(clone, [_coord("c1"), _prob("p1")],
                    expected_revisions={COORDINATOR_STREAM: 0, "prob-1": 0},
                    config=_REMOTE, _after_push=die)

    assert _remote_ids(bare_remote, COORDINATOR_STREAM) == ["c1"]
    assert _remote_ids(bare_remote, "prob-1") == ["p1"]


def test_a_retry_after_a_lost_acknowledgement_is_a_no_op(clone):
    def die():
        raise RuntimeError("killed")

    events = [_coord("c1"), _prob("p1")]
    revisions = {COORDINATOR_STREAM: 0, "prob-1": 0}
    with pytest.raises(RuntimeError):
        append_many(clone, events, expected_revisions=revisions, config=_REMOTE,
                    _after_push=die)

    # The retry reads its revisions FRESH, as every `cas_*` caller does: the transaction
    # landed, so the streams have moved and the original numbers are no longer true. A
    # replay quoting them would be asserting something false about the log — see
    # `test_a_replay_quoting_STALE_revisions_is_refused`.
    again = append_many(clone, events, config=_REMOTE,
                        expected_revisions={COORDINATOR_STREAM: 1, "prob-1": 1})
    assert again.created is False, "the retry re-wrote a transaction that had landed"
    assert again.seqs == {(COORDINATOR_STREAM, "c1"): 0, ("prob-1", "p1"): 0}
    assert [e.event_id for e in read(clone, COORDINATOR_STREAM, config=_REMOTE)] == ["c1"]
    assert [e.event_id for e in read(clone, "prob-1", config=_REMOTE)] == ["p1"]
    assert _commit_count(clone) == 2  # genesis + one transaction, across BOTH calls


# ---- 6. replay ----


def test_a_full_replay_is_idempotent(repo):
    events = [_coord("c1"), _prob("p1")]
    revisions = {COORDINATOR_STREAM: 0, "prob-1": 0}
    first = append_many(repo, events, expected_revisions=revisions)
    again = append_many(repo, events,
                        expected_revisions={COORDINATOR_STREAM: 1, "prob-1": 1})
    assert again.created is False and again.commit == first.commit
    assert len(read(repo, COORDINATOR_STREAM)) == 1 and len(read(repo, "prob-1")) == 1


def test_a_replay_after_the_streams_MOVED_ON_still_reports_the_stored_seqs(repo):
    """A delayed retry observes longer streams. The stored positions are what the events
    actually occupy, so a recomputed one would be a lie about durable history — and the
    revision anchors are excluded from identity, so the retry is a no-op rather than an
    append-only violation."""
    events = [_coord("c1"), _prob("p1")]
    append_many(repo, events, expected_revisions={COORDINATOR_STREAM: 0, "prob-1": 0})
    append(repo, _prob("p2", rev=1), expected_revision=1)

    again = append_many(repo, events,
                        expected_revisions={COORDINATOR_STREAM: 1, "prob-1": 2})
    assert again.created is False
    assert again.seqs == {(COORDINATOR_STREAM, "c1"): 0, ("prob-1", "p1"): 0}
    assert [e.event_id for e in read(repo, "prob-1")] == ["p1", "p2"]


def test_a_replay_quoting_STALE_revisions_is_refused(repo):
    """The complement of the two replays above, and the reason they re-read.

    `expected_revisions` is an assertion about the log's CURRENT shape, checked before
    anything else. After the transaction landed the streams are one longer, so quoting the
    original numbers asserts something false — and the answer is a conflict, telling the
    caller to recompute, not a silent success. Accepting them would mean the revision
    check could be satisfied by state that no longer exists."""
    events = [_coord("c1"), _prob("p1")]
    original = {COORDINATOR_STREAM: 0, "prob-1": 0}
    append_many(repo, events, expected_revisions=original)
    with pytest.raises(LaneRevisionConflict, match="stale revision"):
        append_many(repo, events, expected_revisions=original)
    assert _commit_count(repo) == 2  # and nothing was written by the refused call


def test_a_PARTIALLY_present_transaction_fails_closed(repo):
    """Under the transaction this state is unreachable, so encountering it means something
    outside the transaction wrote one of the ids. Refuse; never complete the missing half."""
    append(repo, _coord("c1"), expected_revision=0)
    with pytest.raises(GitLogError, match="partially present"):
        append_many(repo, [_coord("c1"), _prob("p1")],
                    expected_revisions={COORDINATOR_STREAM: 1, "prob-1": 0})
    assert read(repo, "prob-1") == []


# ---- 7. corruption fails closed, and is NOT a revision conflict ----


def test_a_corrupt_sequence_on_a_touched_stream_raises_GitLogError(repo):
    """`append`'s split, preserved: a gap in the authoritative sequence is corruption
    (fail closed, never retry), not a lost CAS (recompute and try again). Collapsing the
    two would make a damaged log look like ordinary contention."""
    append(repo, _prob("p0"), expected_revision=0)
    append(repo, _prob("p1", rev=1), expected_revision=1)
    # Remove the FIRST record, leaving a stream whose seq line starts at 1.
    tip = _git(repo, "rev-parse", LANE_REF)
    _git(repo, "read-tree", tip)
    _git(repo, "rm", "--cached", "-q", "self-improvement/events/prob-1/p0.json")
    tree = _git(repo, "write-tree")
    corrupt = _git(repo, "commit-tree", tree, "-p", tip, "-m", "drop p0")
    _git(repo, "update-ref", LANE_REF, corrupt)

    with pytest.raises(GitLogError) as excinfo:
        append_many(repo, [_coord("c1"), _prob("p9", rev=9)],
                    expected_revisions={COORDINATOR_STREAM: 0, "prob-1": 1})
    assert not isinstance(excinfo.value, LaneRevisionConflict)
    assert "corrupt sequence" in str(excinfo.value)


# ---- 8. argument contract ----


def test_an_empty_event_list_is_a_caller_error(repo):
    with pytest.raises(ValueError, match="at least one event"):
        append_many(repo, [], expected_revisions={COORDINATOR_STREAM: 0})
