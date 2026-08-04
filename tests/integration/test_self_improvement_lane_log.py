"""The lane store on the shared CAS core (spec 025 slice 1A, Task 3).

Real git repositories throughout — bare remotes, ordinary clones, and two threads racing
the actual ``update-ref``/push. The barrier seams (``_after_probe``/``_after_parent``)
make those races deterministic instead of hopeful.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import threading

import pytest

from llmxive.git_event_log import GitLogError, LogRef, read_log
from llmxive.self_improvement.events import COORDINATOR_STREAM, Event, validate_lane_event
from llmxive.self_improvement.lane_log import (
    LANE_REF,
    LaneLogConfig,
    LaneRevisionConflict,
    append,
    bootstrap_lane_log,
    events_by_commit,
    read,
)


def _git(repo, *a):
    return subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)


@pytest.fixture
def bare_remote(tmp_path):
    r = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(r)], check=True)
    return r


def _clone(bare, dst):
    subprocess.run(["git", "clone", "-q", str(bare), str(dst)], check=True)
    _git(dst, "config", "user.email", "t@t")
    _git(dst, "config", "user.name", "t")
    return dst


@pytest.fixture
def local_repo(tmp_path):
    """A local-only lane log — no remote, so nothing re-fetches the ref out from under a
    test that deliberately corrupts it."""
    r = tmp_path / "local"
    subprocess.run(["git", "init", "-q", str(r)], check=True)
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    bootstrap_lane_log(r, config=LaneLogConfig())
    return r


def _ev(eid, rev, problem_id="prob-1", *, payload=None, timestamp=None):
    # A REAL event type with a WELL-FORMED payload: `Proposed` is validated at the write
    # boundary (it names its Problem and its Attempt), so a transport fixture carrying `{}`
    # would be exercising the store with a record the store is supposed to refuse.
    return Event(event_id=eid, event_type="Proposed", problem_id=problem_id, actor="a",
                 payload={"problem_id": problem_id, "attempt_id": "A1", **(payload or {})},
                 timestamp=timestamp or f"2026-07-24T00:00:{rev:02d}+00:00",
                 attempt_id="A1", expected_problem_revision=rev)


# ---- bootstrap contract ----


def test_append_before_bootstrap_fails_closed(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c")
    with pytest.raises(GitLogError):  # unbootstrapped remote ref → fail closed
        append(c, _ev("e0", 0), expected_revision=0, config=LaneLogConfig(remote="origin"))


def test_read_before_bootstrap_fails_closed(tmp_path, bare_remote):
    # An unbootstrapped remote must NOT read as an empty lane: "empty" is what every
    # projection reads as "no claim, no reservation, no spend".
    c = _clone(bare_remote, tmp_path / "c")
    with pytest.raises(GitLogError):
        read(c, "prob-1", config=LaneLogConfig(remote="origin"))


def test_bootstrap_then_append_pins_anchor(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c")
    anchor = bootstrap_lane_log(c, config=LaneLogConfig(remote="origin"))
    cfg = LaneLogConfig(remote="origin", expected_anchor=anchor)  # pin the history anchor
    assert append(c, _ev("e0", 0), expected_revision=0, config=cfg).seq == 0
    assert append(c, _ev("e1", 1), expected_revision=1, config=cfg).seq == 1
    assert [e.seq for e in read(c, "prob-1", config=cfg)] == [0, 1]


def test_bootstrap_is_idempotent(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c")
    a1 = bootstrap_lane_log(c, config=LaneLogConfig(remote="origin"))
    a2 = bootstrap_lane_log(c, config=LaneLogConfig(remote="origin"))  # repeat → no 2nd genesis
    assert a1 == a2


def test_second_clone_adopts_the_existing_genesis(tmp_path, bare_remote):
    # SEQUENTIAL: the later bootstrapper observes an already-bootstrapped remote and
    # adopts it. This is the adoption path, NOT the concurrent race (see below).
    c1 = _clone(bare_remote, tmp_path / "c1")
    c2 = _clone(bare_remote, tmp_path / "c2")
    a1 = bootstrap_lane_log(c1, config=LaneLogConfig(remote="origin"))
    a2 = bootstrap_lane_log(c2, config=LaneLogConfig(remote="origin"))
    assert a1 == a2  # exactly ONE genesis ref survives


def test_two_concurrent_bootstrappers_race_the_push_and_converge(tmp_path, bare_remote):
    # The REAL race. Both clones must get PAST the "is it bootstrapped?" probe before
    # either pushes — otherwise this only re-tests adoption. The `_after_probe` seam
    # releases both threads at exactly that point, so the loser genuinely executes the
    # non-fast-forward branch.
    c1 = _clone(bare_remote, tmp_path / "c1")
    c2 = _clone(bare_remote, tmp_path / "c2")
    barrier = threading.Barrier(2, timeout=30)
    out: dict[str, str] = {}
    errors: list[BaseException] = []

    def _boot(name, clone):
        try:
            out[name] = bootstrap_lane_log(
                clone, config=LaneLogConfig(remote="origin"), _after_probe=barrier.wait
            )
        except BaseException as exc:  # a raise here is a real failure, not a pass
            errors.append(exc)

    ts = [threading.Thread(target=_boot, args=(n, c)) for n, c in (("a", c1), ("b", c2))]
    for t in ts:
        t.start()
    for t in ts:
        t.join(timeout=60)

    assert not errors, f"concurrent bootstrap raised: {errors}"
    assert out["a"] == out["b"], "the two bootstrappers disagree on the genesis anchor"
    # and the bare remote holds exactly ONE genesis commit on the lane ref
    assert _git(bare_remote, "rev-parse", LANE_REF).stdout.strip() == out["a"]
    count = _git(bare_remote, "rev-list", "--count", LANE_REF).stdout.strip()
    assert count == "1", f"expected a single genesis commit, got {count}"


def test_wrong_expected_anchor_fails_closed(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c")
    bootstrap_lane_log(c, config=LaneLogConfig(remote="origin"))
    with pytest.raises(GitLogError):  # a pinned anchor that isn't the real ref → fail closed
        read(c, "prob-1", config=LaneLogConfig(remote="origin", expected_anchor="0" * 40))


def test_public_read_synchronizes_before_projecting(tmp_path, bare_remote):
    # read_log is LOCAL by design, and an ordinary clone does not fetch refs/llmxive/*.
    # A public read that skipped synchronization would therefore report a fully populated
    # lane as EMPTY — which every projection reads as "no claim, no reservation, no spend".
    c1 = _clone(bare_remote, tmp_path / "c1")
    anchor = bootstrap_lane_log(c1, config=LaneLogConfig(remote="origin"))
    cfg = LaneLogConfig(remote="origin", expected_anchor=anchor)
    append(c1, _ev("e0", 0), expected_revision=0, config=cfg)

    c2 = _clone(bare_remote, tmp_path / "c2")
    unsynced = read_log(
        c2, log=LogRef(ref=LANE_REF, event_dir="self-improvement/events/prob-1"),
        validate=validate_lane_event,
    )
    assert unsynced == [], "precondition: the raw local read sees nothing before a fetch"
    assert [e.event_id for e in read(c2, "prob-1", config=cfg)] == ["e0"]


# ---- FR-008: revision CAS on the bootstrapped ref ----


@pytest.fixture
def env(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c")
    anchor = bootstrap_lane_log(c, config=LaneLogConfig(remote="origin"))
    return c, LaneLogConfig(remote="origin", expected_anchor=anchor)


def test_stale_revision_loses(env):
    c, cfg = env
    append(c, _ev("e0", 0), expected_revision=0, config=cfg)
    with pytest.raises(LaneRevisionConflict):
        append(c, _ev("e1", 0), expected_revision=0, config=cfg)  # actual rev is 1


def test_a_failing_precondition_is_a_conflict_carrying_its_reason(env):
    c, cfg = env
    append(c, _ev("e0", 0), expected_revision=0, config=cfg)
    with pytest.raises(LaneRevisionConflict, match="no headroom"):
        append(c, _ev("e1", 1), expected_revision=1, config=cfg,
               precondition=lambda events: (False, f"no headroom after {len(events)}"))


def test_an_unconditional_append_needs_no_revision(env):
    # Audit events carry no revision precondition — just the ref-CAS + idempotency.
    c, cfg = env
    assert append(c, _ev("a0", 0), expected_revision=None, config=cfg).seq == 0
    assert append(c, _ev("a1", 1), expected_revision=None, config=cfg).seq == 1


def test_each_stream_keeps_its_own_seq_line_and_revision_scope(env):
    # The central design claim: ONE ref (so lane mutations serialize globally), per-stream
    # subtrees (so each Problem — and the coordinator — has its own revision line).
    c, cfg = env
    assert append(c, _ev("p1", 0, "prob-1"), expected_revision=0, config=cfg).seq == 0
    assert append(c, _ev("p2", 0, "prob-2"), expected_revision=0, config=cfg).seq == 0
    assert append(c, _ev("c1", 0, COORDINATOR_STREAM), expected_revision=0, config=cfg).seq == 0

    assert [e.event_id for e in read(c, "prob-1", config=cfg)] == ["p1"]
    assert [e.event_id for e in read(c, "prob-2", config=cfg)] == ["p2"]
    coord = read(c, COORDINATOR_STREAM, config=cfg)[0]
    # the coordinator event carries the LANE scope — and the problem anchors the caller
    # pre-filled were overwritten by the store, not carried into history
    assert (coord.expected_lane_revision, coord.resulting_lane_revision) == (0, 1)
    assert coord.expected_problem_revision is None and coord.resulting_problem_revision is None


def test_replaying_one_operation_is_idempotent_but_a_rewrite_fails_closed(env):
    c, cfg = env
    first = append(c, _ev("op-1", 0), expected_revision=0, config=cfg)
    assert (first.seq, first.created) == (0, True)

    # A replay differing ONLY in the store-owned fields (timestamp/seq/anchors) is the
    # same operation: idempotent no-op at the original seq, not a second record.
    replay = append(c, _ev("op-1", 0, timestamp="2026-07-25T09:15:00+00:00"),
                    expected_revision=None, config=cfg)
    assert (replay.seq, replay.created) == (0, False)
    assert len(read(c, "prob-1", config=cfg)) == 1

    # A DIFFERENT body under the same event_id is a mutation of committed state.
    with pytest.raises(GitLogError, match="append-only"):
        append(c, _ev("op-1", 0, payload={"changed": True}), expected_revision=None, config=cfg)


# ---- corruption of the authoritative sequence is fail-closed ----


def _force_commit_event(repo, raw: dict) -> None:
    """Commit ONE event blob straight onto the lane ref with plumbing, BYPASSING the store.
    The append path cannot produce a gapped sequence by construction, so this is the only
    honest way to present `read`/`append` with the corruption they must refuse."""
    body = json.dumps(raw, indent=2, sort_keys=True)
    blob = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=str(repo), input=body,
                          capture_output=True, text=True, check=True).stdout.strip()
    tip = _git(repo, "rev-parse", LANE_REF).stdout.strip()
    path = f"self-improvement/events/{raw['problem_id']}/{raw['event_id']}.json"
    with tempfile.TemporaryDirectory() as td:
        env = {**os.environ, "GIT_INDEX_FILE": os.path.join(td, "index")}
        subprocess.run(["git", "read-tree", tip], cwd=str(repo), env=env, check=True)
        subprocess.run(["git", "update-index", "--add", "--cacheinfo", f"100644,{blob},{path}"],
                       cwd=str(repo), env=env, check=True)
        tree = subprocess.run(["git", "write-tree"], cwd=str(repo), env=env,
                              capture_output=True, text=True, check=True).stdout.strip()
    commit = _git(repo, "commit-tree", tree, "-p", tip, "-m", "corrupt").stdout.strip()
    _git(repo, "update-ref", LANE_REF, commit)


def _gapped(seq: int) -> dict:
    return {"event_id": "gap", "event_type": "Proposed", "problem_id": "prob-1", "actor": "a",
            "payload": {"problem_id": "prob-1", "attempt_id": "A1"},
            "timestamp": "2026-07-24T00:00:09+00:00", "schema_version": 1,
            "attempt_id": "A1", "seq": seq,
            "expected_problem_revision": seq, "resulting_problem_revision": seq + 1,
            "expected_lane_revision": None, "resulting_lane_revision": None}


def test_a_gapped_sequence_fails_closed_on_read(local_repo):
    append(local_repo, _ev("e0", 0), expected_revision=0)
    _force_commit_event(local_repo, _gapped(2))  # seq 1 is MISSING
    with pytest.raises(GitLogError, match="corrupt sequence"):
        read(local_repo, "prob-1")


def test_append_checks_continuity_before_the_revision(local_repo):
    # Ordering matters: with two records present, expected_revision=2 MATCHES the count,
    # so a continuity check running second would let the append land on a corrupt stream.
    append(local_repo, _ev("e0", 0), expected_revision=0)
    _force_commit_event(local_repo, _gapped(2))
    with pytest.raises(GitLogError, match="corrupt sequence"):
        append(local_repo, _ev("e9", 2), expected_revision=2)


# ---- the same-commit traversal: absence vs failure ----


def test_events_by_commit_reports_an_UNBOOTSTRAPPED_lane_as_empty(tmp_path):
    """A ref that genuinely does not exist is a cold start, not a fault. Establishing that
    by asking about the REF is the whole point — `git log` exits non-zero for both."""
    r = tmp_path / "cold"
    subprocess.run(["git", "init", "-q", str(r)], check=True)
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    assert events_by_commit(r) == {}


def test_events_by_commit_FAILS_CLOSED_when_the_traversal_cannot_run(local_repo):
    """The ref exists and resolves, and the traversal still fails — a damaged object store.

    Deleting the tip's TREE leaves the commit object readable (so the ref resolves) while
    `git log --name-only --diff-filter=A` cannot diff it. Treating that as "no events" hands
    the same-commit proof an empty map, and its one consumer reads a missing entry as "no
    commit introduces this event" — a transport fault reported as log CORRUPTION, sending a
    reader after damage that is not where the message points."""
    append(local_repo, _ev("e0", 0), expected_revision=0)
    assert events_by_commit(local_repo), "the traversal found nothing to break"
    tree = subprocess.run(["git", "rev-parse", f"{LANE_REF}^{{tree}}"], cwd=str(local_repo),
                          capture_output=True, text=True, check=True).stdout.strip()
    (local_repo / ".git" / "objects" / tree[:2] / tree[2:]).unlink()

    with pytest.raises(GitLogError):
        events_by_commit(local_repo)


# ---- TRUE barrier-driven race on the append CAS ----


def test_barrier_seam_race_exactly_one_wins(tmp_path, bare_remote):
    c1 = _clone(bare_remote, tmp_path / "c1")
    bootstrap_lane_log(c1, config=LaneLogConfig(remote="origin"))
    c2 = _clone(bare_remote, tmp_path / "c2")
    cfg = LaneLogConfig(remote="origin")
    at_parent = threading.Barrier(2, timeout=30)  # both block AFTER fixing the same parent
    outcomes, lock = [], threading.Lock()

    def _worker(clone, tag):
        fired = {"once": False}

        def _seam():  # one-shot: block only on the FIRST attempt (a retry must not re-wait)
            if not fired["once"]:
                fired["once"] = True
                try:
                    at_parent.wait()
                except threading.BrokenBarrierError:
                    pass

        try:
            r = append(clone, _ev(f"from-{tag}", 0), expected_revision=0, config=cfg,
                       _after_parent=_seam)
            with lock:
                outcomes.append(("ok", r))
        except LaneRevisionConflict as exc:
            with lock:
                outcomes.append(("conflict", exc))

    ts = [threading.Thread(target=_worker, args=(c, t)) for c, t in ((c1, "c1"), (c2, "c2"))]
    for th in ts:
        th.start()
    for th in ts:
        th.join(timeout=60)
    oks = [o for k, o in outcomes if k == "ok"]
    conflicts = [o for k, o in outcomes if k == "conflict"]
    # both built from the SAME parent (barrier) then raced the ACTUAL update-ref/FF-push:
    # exactly one wins, the loser hits non-fast-forward → recompute → predicate fails.
    assert len(oks) == 1 and len(conflicts) == 1, f"outcomes: {outcomes}"


# ---- concurrent writers on ONE stream (found by the real convergence panel) ----


def test_many_concurrent_writers_get_contiguous_seqs_and_none_starve(local_repo):
    """N threads appending to ONE stream: every append lands, exactly once, with a
    contiguous seq line and no writer exhausting its retry budget.

    Both halves were REAL defects, surfaced by the 5-reviewer convergence panel:

    1. `seq` and the CAS parent were read SEPARATELY (`read_log`'s own `_rev`, then
       another in the append loop). A writer landing between the two left `seq` stale
       while `parent` was fresh, so `update-ref`'s compare-and-swap SUCCEEDED and two
       events durably shared a seq — which the reader then rejected as a corrupt
       sequence, after the damage was committed.
    2. The retry budget was 8, EQUAL to the panel's concurrency cap. Losing every race
       to every peer is a legal interleaving, not an anomaly, so a healthy panel raised
       `GitLogContention`.
    """
    writers, per_writer = 8, 4
    errors: list[BaseException] = []
    lock = threading.Lock()

    def _worker(w: int) -> None:
        for i in range(per_writer):
            try:
                append(local_repo, _ev(f"w{w}-e{i}", 0), expected_revision=None,
                       config=LaneLogConfig())
            except BaseException as exc:
                with lock:
                    errors.append(exc)
                return

    threads = [threading.Thread(target=_worker, args=(w,)) for w in range(writers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=300)

    assert not errors, f"{len(errors)} writer(s) failed: {errors[:3]}"
    events = read(local_repo, "prob-1", config=LaneLogConfig())
    assert len(events) == writers * per_writer
    # `read` already fails closed on a gap/dup, but assert it explicitly: a duplicate seq
    # is the exact corruption defect 1 produced.
    assert [e.seq for e in events] == list(range(writers * per_writer))
    assert len({e.event_id for e in events}) == writers * per_writer
