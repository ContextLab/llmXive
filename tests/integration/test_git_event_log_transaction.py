"""Multi-subtree transactions on one ref (spec 025 slice 2, Task 3).

Every case here is about ONE question: can an observer ever see half of a transaction?

Against real temp-git repos — no mocks. The lane's coordinator stream and its per-Problem
streams are SUBTREES OF ONE REF, so a cross-stream mutation is a single tree write and a
single ref compare-and-swap; these tests are what says so.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from llmxive.git_event_log import (
    GitLogContention,
    GitLogDenied,
    GitLogError,
    LogRef,
    append_transaction,
    bootstrap_log,
    read_log,
)

REF = "refs/llmxive/txn-test"
#: The genesis commit `bootstrap_log` writes, so a "the ref advanced once" assertion can
#: be stated as a delta rather than as a magic number.
_BOOTSTRAP_COMMITS = 1


def _git(repo: Path, *a: str) -> str:
    return subprocess.run(
        ["git", *a], cwd=str(repo), check=True, capture_output=True, text=True
    ).stdout.strip()


def _log(stream: str, **kw) -> LogRef:
    return LogRef(ref=REF, event_dir=f"events/{stream}", **kw)


def _validate(event: dict) -> None:
    if "event_id" not in event:
        raise ValueError("event_id required")


def _message(events: list[dict]) -> str:
    return f"txn of {len(events)}"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    bootstrap_log(r, log=_log("coordinator"), message="genesis")
    return r


@pytest.fixture
def bare_remote(tmp_path: Path) -> Path:
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    return remote


@pytest.fixture
def clone(tmp_path: Path, bare_remote: Path) -> Path:
    """A clone with the log bootstrapped on the REMOTE — the configuration in which the
    push is the commit point, which is what the durability cases are about."""
    dst = tmp_path / "c"
    subprocess.run(["git", "clone", "-q", str(bare_remote), str(dst)], check=True)
    _git(dst, "config", "user.email", "t@t")
    _git(dst, "config", "user.name", "t")
    bootstrap_log(dst, log=_log("coordinator", remote="origin"), message="genesis",
                  remote="origin")
    return dst


def _read(repo: Path, stream: str) -> list[dict]:
    return read_log(repo, log=_log(stream), validate=_validate)


def _read_remote(bare: Path, stream: str) -> list[str]:
    """Event ids on a stream as the REMOTE has them — the authoritative copy, read without
    going through the local clone at all."""
    listing = _git(bare, "ls-tree", "--name-only", f"{REF}:events/{stream}")
    return sorted(Path(name).stem for name in listing.splitlines() if name)


def _commit_count(repo: Path, ref: str = REF) -> int:
    return int(_git(repo, "rev-list", "--count", ref))


def _txn(repo: Path, pairs, *, prepare=None, streams=("coordinator", "P1"),
         remote: str | None = None, **kw):
    return append_transaction(
        repo,
        log=_log("coordinator", remote=remote) if remote else _log("coordinator"),
        streams=list(streams),
        event_dir_for=lambda s: f"events/{s}",
        validate=_validate,
        message_fn=_message,
        prepare=prepare or (lambda observed: pairs),
        **kw,
    )


def _seq(event: dict, seq: int) -> dict:
    return {**event, "seq": seq}


#: `_seq` and this belong together in every REPLAY case. A replay observes a longer stream,
#: so the rebuilt event carries a different `seq` than the stored one; without excluding it
#: from semantic identity the append-only guard fires on a legitimate retry and the replay
#: path is never reached. This is exactly the pairing `lane_log._IDENTITY_EXCLUDE` makes.
_EXCL = frozenset({"seq"})


# ---- one commit, many subtrees ----


def test_one_commit_carries_both_streams(repo: Path):
    result = _txn(repo, [("coordinator", {"event_id": "c1"}), ("P1", {"event_id": "p1"})])
    assert result.created is True
    assert [e["event_id"] for e in _read(repo, "coordinator")] == ["c1"]
    assert [e["event_id"] for e in _read(repo, "P1")] == ["p1"]
    # ONE commit, not two: the ref advanced by exactly one.
    assert _commit_count(repo) == _BOOTSTRAP_COMMITS + 1


def test_both_blobs_were_added_by_the_SAME_commit(repo: Path):
    """The atomicity claim, checked the way the auditor will check it: `--diff-filter=A`
    attributes each blob to the commit that introduced it, and both must name one."""
    result = _txn(repo, [("coordinator", {"event_id": "c1"}), ("P1", {"event_id": "p1"})])
    added = _git(repo, "show", "--name-only", "--format=", result.commit).splitlines()
    assert sorted(n for n in added if n) == [
        "events/P1/p1.json",
        "events/coordinator/c1.json",
    ]


def test_each_stream_gets_its_own_seq_line(repo: Path):
    _txn(repo, [("coordinator", {"event_id": "c1"}), ("P1", {"event_id": "p1"})],
         finalize=_seq)
    _txn(repo, [("coordinator", {"event_id": "c2"}), ("P1", {"event_id": "p2"})],
         finalize=_seq)
    # Independent 0,1 lines — NOT a shared counter across streams.
    assert [e["seq"] for e in _read(repo, "coordinator")] == [0, 1]
    assert [e["seq"] for e in _read(repo, "P1")] == [0, 1]


def test_two_events_on_the_SAME_stream_in_one_txn_get_consecutive_seqs(repo: Path):
    _txn(repo, [("P1", {"event_id": "a"}), ("P1", {"event_id": "b"})], finalize=_seq)
    assert [e["seq"] for e in _read(repo, "P1")] == [0, 1]


def test_seqs_are_keyed_by_stream_AND_id_so_a_shared_id_does_not_collapse(repo: Path):
    # Ids are derived per stream in the lane, but this module cannot assume that. Keyed by
    # id alone, one of these two entries would silently overwrite the other and the caller
    # would be told a position that belongs to the other stream.
    result = _txn(repo, [("coordinator", {"event_id": "same"}), ("P1", {"event_id": "same"})],
                  finalize=_seq)
    assert result.seqs == {("coordinator", "same"): 0, ("P1", "same"): 0}
    assert len(_read(repo, "coordinator")) == len(_read(repo, "P1")) == 1


def test_the_same_id_TWICE_on_one_stream_is_refused(repo: Path):
    # One blob path cannot hold two events: `update-index --cacheinfo` would keep the last
    # while both seqs were consumed, leaving a gap that only surfaces later, elsewhere.
    with pytest.raises(GitLogError, match="twice"):
        _txn(repo, [("P1", {"event_id": "dup"}), ("P1", {"event_id": "dup"})], finalize=_seq)
    assert _read(repo, "P1") == []


def test_an_undeclared_stream_is_refused(repo: Path):
    """Writing to a stream that was never observed would be deciding against state this
    transaction never read — the exact thing the one-parent observation exists to prevent."""
    with pytest.raises(GitLogError, match="not declared"):
        _txn(repo, [("P2", {"event_id": "x"})])
    assert _commit_count(repo) == _BOOTSTRAP_COMMITS


def test_an_unsafe_event_id_is_refused_before_anything_is_written(repo: Path):
    with pytest.raises(GitLogError, match="must match"):
        _txn(repo, [("P1", {"event_id": "../escape"})])
    assert _commit_count(repo) == _BOOTSTRAP_COMMITS


# ---- the cross-stream predicate ----


def test_the_predicate_sees_every_touched_stream_at_ONE_parent(repo: Path):
    _txn(repo, [("coordinator", {"event_id": "c1", "generation": 1})])
    seen: dict[str, list[str]] = {}

    def prepare(observed):
        seen.update({k: [e["event_id"] for e in v] for k, v in observed.items()})
        return [("P1", {"event_id": "p1"})]

    _txn(repo, None, prepare=prepare)
    # The Problem-stream write was decided while HOLDING an observation of the coordinator.
    # This is the capability the first draft of this plan wrongly believed impossible.
    assert seen == {"coordinator": ["c1"], "P1": []}


def test_a_prepare_that_denies_writes_nothing(repo: Path):
    def prepare(observed):
        raise GitLogDenied("stale generation")

    with pytest.raises(GitLogDenied, match="stale generation"):
        _txn(repo, None, prepare=prepare)
    assert _read(repo, "coordinator") == [] and _read(repo, "P1") == []


def test_prepare_returning_none_is_an_idempotent_no_op(repo: Path):
    result = _txn(repo, None, prepare=lambda observed: None)
    assert result.created is False and result.seqs == {}
    assert _commit_count(repo) == _BOOTSTRAP_COMMITS


# ---- crash seams: before the commit point ----


def test_a_crash_after_the_parent_is_fixed_leaves_NO_transition(repo: Path):
    def boom():
        raise RuntimeError("crash: parent fixed")

    with pytest.raises(RuntimeError, match="parent fixed"):
        _txn(repo, [("coordinator", {"event_id": "c1"}), ("P1", {"event_id": "p1"})],
             _after_parent=boom)
    assert _read(repo, "coordinator") == [] and _read(repo, "P1") == []


def test_a_crash_after_the_commit_is_built_leaves_NO_transition(repo: Path):
    # The commit OBJECT exists in the object store but is unreachable: the ref never moved,
    # so no reader can observe it. This is the seam a two-commit sequence could not survive.
    def boom():
        raise RuntimeError("crash: pre ref-update")

    with pytest.raises(RuntimeError, match="pre ref-update"):
        _txn(repo, [("coordinator", {"event_id": "c1"}), ("P1", {"event_id": "p1"})],
             _before_ref_update=boom)
    assert _read(repo, "coordinator") == [] and _read(repo, "P1") == []


# ---- crash seams: after the commit point (the push) ----


def test_a_crash_after_the_push_leaves_the_transaction_DURABLE(clone: Path,
                                                               bare_remote: Path):
    """The commit point is the push, so this crash is on the far side of it.

    The two crash tests above assert ABSENCE because they fire before the ref moves. This
    one must assert PRESENCE. An earlier draft of the matrix claimed a crash "at any seam"
    left nothing — false here, and false in the direction that matters: an implementer who
    believed it would go looking for a repair path for events that are already correctly
    durable."""
    def die():
        raise RuntimeError("runner killed between the push and its local ref update")

    with pytest.raises(RuntimeError, match="runner killed"):
        _txn(clone, [("coordinator", {"event_id": "c1"}), ("P1", {"event_id": "p1"})],
             remote="origin", _after_push=die)

    # Locally the ref never moved — the caller has no acknowledgement.
    assert _read(clone, "coordinator") == [] and _read(clone, "P1") == []
    # On the REMOTE, both events are durable, and BOTH of them: never a subset.
    assert _read_remote(bare_remote, "coordinator") == ["c1"]
    assert _read_remote(bare_remote, "P1") == ["p1"]


def test_a_retry_after_a_LOST_ACKNOWLEDGEMENT_is_a_no_op(clone: Path):
    """The recovery path for the test above — and it is the ORDINARY retry, not a
    reconciler. A durable transaction whose caller never learned it landed is, to that
    caller, indistinguishable from one that never ran, so the retry has to be safe."""
    def die():
        raise RuntimeError("killed")

    pairs = [("coordinator", {"event_id": "c1"}), ("P1", {"event_id": "p1"})]
    with pytest.raises(RuntimeError):
        _txn(clone, pairs, remote="origin", _after_push=die, finalize=_seq,
             identity_exclude=_EXCL)

    again = _txn(clone, pairs, remote="origin", finalize=_seq, identity_exclude=_EXCL)
    assert again.created is False, "the retry re-wrote a transaction that had landed"
    assert again.seqs == {("coordinator", "c1"): 0, ("P1", "p1"): 0}
    assert [e["event_id"] for e in _read(clone, "coordinator")] == ["c1"]
    assert [e["event_id"] for e in _read(clone, "P1")] == ["p1"]
    # And the ref advanced exactly once across BOTH calls.
    assert _commit_count(clone) == _BOOTSTRAP_COMMITS + 1


def test_a_successful_push_never_rewinds_a_local_ref_that_moved(clone: Path):
    """Task 2 fixed this for `append_to_log`; this is the same guarantee at the
    TRANSACTION writer's seam, because a shared helper is only shared while both callers
    use it.

    The window is between OUR push and OUR local update — before the push a competing
    writer simply loses the fast-forward and we retry. So the second writer completes its
    entire cycle inside `_after_push`."""
    ahead: dict[str, str] = {}

    def a_second_writer_finishes_first():
        ahead["commit"] = _txn(clone, [("P1", {"event_id": "other"})],
                               remote="origin").commit

    ours = _txn(clone, [("P1", {"event_id": "ours"})], remote="origin",
                _after_push=a_second_writer_finishes_first)

    tip = _git(clone, "rev-parse", REF)
    assert tip == ahead["commit"], "the local ref was rewound past a newer commit"
    assert _git(clone, "merge-base", "--is-ancestor", ours.commit, tip) == ""
    # A LOCAL read, with no intervening fetch, sees both events.
    assert {e["event_id"] for e in _read(clone, "P1")} == {"other", "ours"}


@pytest.mark.parametrize("writer", ["append_to_log", "append_transaction"])
def test_both_writers_sync_the_local_ref_through_the_same_helper(writer: str):
    """`_sync_local_ref` is the shared implementation, so this asserts neither writer kept
    its own bare `update-ref` — the state Task 2's fix removed."""
    import inspect

    from llmxive import git_event_log

    source = inspect.getsource(getattr(git_event_log, writer))
    assert "_sync_local_ref" in source
    assert '"update-ref", log.ref, new_commit]' not in source, "bare update-ref survives"


# ---- replay ----


def test_a_replay_of_the_whole_transaction_is_an_idempotent_no_op(repo: Path):
    pairs = [("coordinator", {"event_id": "c1"}), ("P1", {"event_id": "p1"})]
    first = _txn(repo, pairs, finalize=_seq, identity_exclude=_EXCL)
    again = _txn(repo, pairs, finalize=_seq, identity_exclude=_EXCL)
    assert again.created is False and again.commit == first.commit
    assert len(_read(repo, "coordinator")) == 1 and len(_read(repo, "P1")) == 1


def test_a_replay_reports_the_STORED_seqs_not_recomputed_ones(repo: Path):
    _txn(repo, [("P1", {"event_id": "a"})], finalize=_seq, identity_exclude=_EXCL)
    _txn(repo, [("P1", {"event_id": "filler"})], finalize=_seq, identity_exclude=_EXCL)
    again = _txn(repo, [("P1", {"event_id": "a"})], finalize=_seq, identity_exclude=_EXCL)
    # The stream is two long now, so a recomputed position would claim seq 2 for an event
    # that has occupied seq 0 since the first call.
    assert again.created is False and again.seqs == {("P1", "a"): 0}


def test_a_PARTIALLY_present_transaction_fails_closed(repo: Path):
    # Half the ids already exist. Under the transaction that state is unreachable, so
    # encountering it means something outside the transaction wrote one of them — the log
    # is not what this caller thinks it is. Refuse; never "complete" the missing half.
    _txn(repo, [("coordinator", {"event_id": "c1"})], finalize=_seq, identity_exclude=_EXCL)
    with pytest.raises(GitLogError, match="partially present"):
        _txn(repo, [("coordinator", {"event_id": "c1"}), ("P1", {"event_id": "p1"})],
             finalize=_seq, identity_exclude=_EXCL)
    assert _read(repo, "P1") == []


def test_a_same_id_replay_with_DIFFERENT_content_is_an_append_only_violation(repo: Path):
    _txn(repo, [("coordinator", {"event_id": "c1", "v": 1})])
    with pytest.raises(GitLogError, match="append-only"):
        _txn(repo, [("coordinator", {"event_id": "c1", "v": 2})])


def test_identity_exclude_makes_a_restamped_replay_idempotent(repo: Path):
    """A replay re-derives the same semantic events but would be finalized with DIFFERENT
    seqs. Without `identity_exclude` the append-only guard fires on a legitimate retry —
    the same contract `append_to_log` has, and it must not be weaker here."""
    pairs = [("coordinator", {"event_id": "c1"}), ("P1", {"event_id": "p1"})]
    _txn(repo, pairs, finalize=_seq, identity_exclude=_EXCL)
    _txn(repo, [("P1", {"event_id": "filler"})], finalize=_seq, identity_exclude=_EXCL)
    again = _txn(repo, pairs, finalize=_seq, identity_exclude=_EXCL)
    assert again.created is False
    assert again.seqs == {("coordinator", "c1"): 0, ("P1", "p1"): 0}


# ---- contention ----


def test_a_concurrent_writer_forces_a_retry_and_the_predicate_re_runs(repo: Path):
    # A barrier at the parent-fixed point lets a foreign event land underneath, so the
    # update-ref CAS must fail and prepare must be re-invoked against the NEW tip.
    calls: list[int] = []

    def prepare(observed):
        calls.append(len(observed["coordinator"]))
        return [("coordinator", {"event_id": "mine"}), ("P1", {"event_id": "p1"})]

    fired: list[bool] = []

    def interlope():
        if fired:
            return
        fired.append(True)
        _txn(repo, [("coordinator", {"event_id": "foreign"})], streams=("coordinator",))

    _txn(repo, None, prepare=prepare, _after_parent=interlope)
    assert calls == [0, 1]  # re-decided against the foreign event, not layered over it
    assert {e["event_id"] for e in _read(repo, "coordinator")} == {"foreign", "mine"}


def test_sustained_contention_raises_contention(repo: Path):
    """When the ref moves under EVERY attempt, the loop gives up rather than forcing.

    `_steal` runs at the parent-fixed seam on each attempt, so every commit this
    transaction builds is already stale by the time it reaches the CAS."""

    def _steal():
        tip = _git(repo, "rev-parse", REF)
        new = _git(repo, "commit-tree", f"{tip}^{{tree}}", "-p", tip, "-m", "steal")
        _git(repo, "update-ref", REF, new)

    with pytest.raises(GitLogContention):
        _txn(repo, [("P1", {"event_id": "never"})], _after_parent=_steal, max_retries=3)
    assert _read(repo, "P1") == []


def test_the_stored_blob_is_canonical_json(repo: Path):
    _txn(repo, [("P1", {"event_id": "e0", "z": 1, "b": 2})])
    tip = _git(repo, "rev-parse", REF)
    blob = _git(repo, "cat-file", "blob", f"{tip}:events/P1/e0.json")
    assert blob == json.dumps({"event_id": "e0", "z": 1, "b": 2}, indent=2, sort_keys=True)
