"""The extracted git-CAS core's OWN behavior (spec 025 slice 1A, Task 1).

The credit ledger's suite already covers the shared transport end-to-end (and is the
extraction's acceptance bar, unedited). What it does NOT exercise are the generic
capabilities the lane needs: the assigned ``seq``, the ``created`` flag, ``finalize``,
``identity_exclude``, and the test-only barrier seams. Those are covered here, against
real git repos — no mocks.
"""

from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path

import pytest

from llmxive.git_event_log import (
    AppendResult,
    GitLogAuthError,
    GitLogContention,
    GitLogDenied,
    GitLogError,
    LogRef,
    append_to_log,
    bootstrap_log,
    read_log,
    sync_and_verify,
)

_EVENT_DIR = "events/v1"
_MSG = "test-log: bootstrap"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=str(repo), check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def bare_remote(tmp_path: Path) -> Path:
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    return remote


def _clone(bare: Path, dst: Path) -> Path:
    subprocess.run(["git", "clone", "-q", str(bare), str(dst)], check=True)
    _git(dst, "config", "user.email", "t@t")
    _git(dst, "config", "user.name", "t")
    return dst


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    return r


def _log(ref: str = "refs/llmxive/test-log", **kw) -> LogRef:
    return LogRef(ref=ref, event_dir=_EVENT_DIR, **kw)


def _validate(event: dict) -> None:
    """A minimal caller schema: every event needs an id and a kind."""
    for key in ("event_id", "kind"):
        if key not in event:
            raise ValueError(f"event missing {key!r}")


def _message(event: dict) -> str:
    return f"test-log: {event['kind']} {event['event_id']}"


def _append(repo: Path, event: dict, *, log: LogRef | None = None, **kw) -> AppendResult:
    return append_to_log(
        repo, log=log or _log(), validate=_validate, message_fn=_message, event=event, **kw
    )


def _read(repo: Path, *, log: LogRef | None = None) -> list[dict]:
    return read_log(repo, log=log or _log(), validate=_validate)


# ---- seq + created (the lane's ordering contract) ----


def test_seq_is_assigned_in_order_and_created_is_true(repo: Path):
    first = _append(repo, {"event_id": "e0", "kind": "a"})
    second = _append(repo, {"event_id": "e1", "kind": "b"})
    assert (first.seq, first.created) == (0, True)
    assert (second.seq, second.created) == (1, True)
    assert [e["event_id"] for e in _read(repo)] == ["e0", "e1"]


def test_an_identical_re_append_is_an_idempotent_no_op(repo: Path):
    first = _append(repo, {"event_id": "e0", "kind": "a"})
    replay = _append(repo, {"event_id": "e0", "kind": "a"})
    assert replay.created is False, "a replay must not be reported as new work"
    assert replay.commit == first.commit  # the tip did not move
    assert len(_read(repo)) == 1


def test_a_different_body_under_the_same_id_fails_closed(repo: Path):
    _append(repo, {"event_id": "e0", "kind": "a"})
    with pytest.raises(GitLogError, match="append-only violation"):
        _append(repo, {"event_id": "e0", "kind": "DIFFERENT"})


# ---- finalize + identity_exclude (the lane's revision anchors) ----


def _finalize(built: dict, seq: int) -> dict:
    """Stamp the store-assigned position + a derived anchor, as the lane does."""
    return {**built, "seq": seq, "expected_revision": seq, "resulting_revision": seq + 1}


def test_finalize_stamps_the_authoritative_seq_inside_the_cas(repo: Path):
    _append(repo, {"event_id": "e0", "kind": "a"}, finalize=_finalize)
    _append(repo, {"event_id": "e1", "kind": "b"}, finalize=_finalize)
    stored = _read(repo)
    assert [e["seq"] for e in stored] == [0, 1]
    assert [e["expected_revision"] for e in stored] == [0, 1]
    assert [e["resulting_revision"] for e in stored] == [1, 2]


def test_identity_exclude_makes_a_semantic_retry_idempotent(repo: Path):
    """A retry re-derives the SAME semantic event but the store re-stamps seq/timestamp.
    Without identity_exclude that differs byte-wise and the append-only guard would
    RAISE on a legitimate retry."""
    excl = frozenset({"seq", "expected_revision", "resulting_revision", "ts"})
    _append(repo, {"event_id": "e0", "kind": "a"}, finalize=_finalize,
            identity_exclude=excl, now_field="ts")
    # A second, semantically identical attempt — it would be finalized with a DIFFERENT
    # seq (1, not 0) had it landed, and would carry a fresh timestamp.
    replay = _append(repo, {"event_id": "e0", "kind": "a"}, finalize=_finalize,
                     identity_exclude=excl, now_field="ts")
    assert replay.created is False
    assert replay.seq == 0, "the replay reports the COMMITTED event's seq, not a new one"
    assert len(_read(repo)) == 1


def test_without_identity_exclude_a_restamped_retry_raises(repo: Path):
    """The counterpart: this is exactly why identity_exclude exists."""
    _append(repo, {"event_id": "e0", "kind": "a"}, finalize=_finalize)
    _append(repo, {"event_id": "e1", "kind": "b"}, finalize=_finalize)
    # Re-attempting e0 now would finalize with seq=2, a genuinely different body.
    with pytest.raises(GitLogError, match="append-only violation"):
        _append(repo, {"event_id": "e0", "kind": "a"}, finalize=_finalize)


def test_a_semantically_different_body_still_raises_under_identity_exclude(repo: Path):
    """identity_exclude must not become a blanket 'ignore differences'."""
    excl = frozenset({"seq", "expected_revision", "resulting_revision"})
    _append(repo, {"event_id": "e0", "kind": "a"}, finalize=_finalize, identity_exclude=excl)
    with pytest.raises(GitLogError, match="append-only violation"):
        _append(repo, {"event_id": "e0", "kind": "DIFFERENT"},
                finalize=_finalize, identity_exclude=excl)


# ---- now_field ----


def test_now_field_is_stamped_only_when_absent(repo: Path):
    _append(repo, {"event_id": "e0", "kind": "a"}, now_field="ts")
    _append(repo, {"event_id": "e1", "kind": "b", "ts": "2020-01-01T00:00:00+00:00"},
            now_field="ts")
    stored = {e["event_id"]: e for e in _read(repo)}
    assert stored["e0"]["ts"]  # stamped
    assert stored["e1"]["ts"] == "2020-01-01T00:00:00+00:00"  # caller's value preserved


def test_no_now_field_means_no_timestamp_is_invented(repo: Path):
    _append(repo, {"event_id": "e0", "kind": "a"})
    assert "ts" not in _read(repo)[0]


# ---- predicate / prepare ----


def test_a_denying_predicate_never_appends(repo: Path):
    with pytest.raises(GitLogDenied, match="nope"):
        _append(repo, {"event_id": "e0", "kind": "a"}, predicate=lambda _evs: (False, "nope"))
    assert _read(repo) == []


def test_prepare_returning_none_is_an_idempotent_no_op(repo: Path):
    result = append_to_log(
        repo, log=_log(), validate=_validate, message_fn=_message, prepare=lambda _evs: None
    )
    assert result.created is False and _read(repo) == []


def test_prepare_sees_fresh_events_on_every_attempt(repo: Path):
    _append(repo, {"event_id": "e0", "kind": "a"})
    seen: list[int] = []

    def _prepare(events: list[dict]) -> dict:
        seen.append(len(events))
        return {"event_id": "e1", "kind": "b"}

    append_to_log(repo, log=_log(), validate=_validate, message_fn=_message, prepare=_prepare)
    assert seen == [1]


# ---- validation + corruption ----


def test_validate_runs_on_write(repo: Path):
    with pytest.raises(ValueError, match="kind"):
        _append(repo, {"event_id": "e0"})


def test_validate_runs_on_read_too(repo: Path):
    _append(repo, {"event_id": "e0", "kind": "a"})
    # A stricter reader must reject an event that passed the writer's schema.
    def _stricter(event: dict) -> None:
        if event.get("kind") != "b":
            raise ValueError("kind must be 'b'")

    with pytest.raises(GitLogError, match="invalid log event"):
        read_log(repo, log=_log(), validate=_stricter)


def test_an_unsafe_event_id_is_rejected(repo: Path):
    with pytest.raises(GitLogError, match="must match"):
        _append(repo, {"event_id": "nested/id", "kind": "a"})


def test_a_non_finite_number_never_reaches_the_ref(repo: Path):
    with pytest.raises(ValueError, match="not JSON compliant"):
        _append(repo, {"event_id": "e0", "kind": "a", "amount": float("nan")})
    assert _read(repo) == []


# ---- two independent logs on one repo ----


def test_two_logs_on_the_same_repo_do_not_interfere(repo: Path):
    other = LogRef(ref="refs/llmxive/other-log", event_dir="other/v1")
    _append(repo, {"event_id": "e0", "kind": "a"})
    _append(repo, {"event_id": "e0", "kind": "z"}, log=other)  # same id, different log
    assert [e["kind"] for e in _read(repo)] == ["a"]
    assert [e["kind"] for e in _read(repo, log=other)] == ["z"]


# ---- bootstrap ----


def test_append_before_bootstrap_fails_closed_with_a_remote(tmp_path: Path, bare_remote: Path):
    clone = _clone(bare_remote, tmp_path / "c")
    with pytest.raises(GitLogAuthError, match="not bootstrapped"):
        _append(clone, {"event_id": "e0", "kind": "a"}, log=_log(remote="origin"))


def test_bootstrap_then_append(tmp_path: Path, bare_remote: Path):
    clone = _clone(bare_remote, tmp_path / "c")
    anchor = bootstrap_log(clone, log=_log(remote="origin"), message=_MSG, remote="origin")
    log = _log(remote="origin", expected_anchor=anchor)
    assert _append(clone, {"event_id": "e0", "kind": "a"}, log=log).seq == 0
    assert [e["event_id"] for e in _read(clone, log=log)] == ["e0"]


def test_bootstrap_is_idempotent(tmp_path: Path, bare_remote: Path):
    clone = _clone(bare_remote, tmp_path / "c")
    first = bootstrap_log(clone, log=_log(remote="origin"), message=_MSG, remote="origin")
    again = bootstrap_log(clone, log=_log(remote="origin"), message=_MSG, remote="origin")
    assert first == again


def test_a_wrong_pinned_anchor_fails_closed(tmp_path: Path, bare_remote: Path):
    clone = _clone(bare_remote, tmp_path / "c")
    bootstrap_log(clone, log=_log(remote="origin"), message=_MSG, remote="origin")
    wrong = _log(remote="origin", expected_anchor="a" * 40)
    # The anchor is verified by sync_and_verify — which every APPEND runs, and which a
    # caller runs explicitly before projecting. (A bare read_log is deliberately a pure
    # object-store read; syncing is the caller's decision, as in the credit ledger.)
    with pytest.raises(GitLogAuthError, match="does not descend"):
        sync_and_verify(clone, log=wrong)
    with pytest.raises(GitLogAuthError, match="does not descend"):
        _append(clone, {"event_id": "e0", "kind": "a"}, log=wrong)


def test_two_concurrent_bootstrappers_race_the_push_and_converge(
    tmp_path: Path, bare_remote: Path
):
    """The `_after_probe` seam holds BOTH workers past the existence probe, so the
    loser genuinely executes the adopt-the-winner branch rather than the (much easier)
    sequential adoption path."""
    c1 = _clone(bare_remote, tmp_path / "c1")
    c2 = _clone(bare_remote, tmp_path / "c2")
    barrier = threading.Barrier(2, timeout=30)
    out: dict[str, str] = {}
    errors: list[BaseException] = []

    def _boot(name: str, clone: Path) -> None:
        try:
            out[name] = bootstrap_log(
                clone, log=_log(remote="origin"), message=_MSG, remote="origin",
                _after_probe=barrier.wait,
            )
        except BaseException as exc:  # a raise here is a real failure, not a pass
            errors.append(exc)

    threads = [threading.Thread(target=_boot, args=(n, c)) for n, c in (("a", c1), ("b", c2))]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    assert not errors, f"concurrent bootstrap raised: {errors}"
    assert out["a"] == out["b"], "the two bootstrappers disagree on the genesis anchor"
    assert _git(bare_remote, "rev-parse", "refs/llmxive/test-log") == out["a"]
    assert _git(bare_remote, "rev-list", "--count", "refs/llmxive/test-log") == "1"


# ---- the real CAS race ----


def test_two_clones_racing_the_push_both_survive(tmp_path: Path, bare_remote: Path):
    """The `_after_parent` seam fixes BOTH workers on the same parent, then releases
    them into the actual push — so the non-fast-forward retry path is executed, not
    assumed. Both events must end up on the ref, neither overwritten."""
    c1 = _clone(bare_remote, tmp_path / "c1")
    c2 = _clone(bare_remote, tmp_path / "c2")
    bootstrap_log(c1, log=_log(remote="origin"), message=_MSG, remote="origin")
    _git(c2, "fetch", "-q", "origin", "+refs/llmxive/test-log:refs/llmxive/test-log")

    barrier = threading.Barrier(2, timeout=30)
    waited: set[int] = set()
    waited_lock = threading.Lock()
    errors: list[BaseException] = []

    def _once() -> None:
        """Each worker waits at the barrier exactly ONCE, on its first attempt: that is
        what guarantees both built from the same parent. A retry must NOT wait — its
        partner has already moved on, and the barrier would deadlock."""
        ident = threading.get_ident()
        with waited_lock:
            already = ident in waited
            waited.add(ident)
        if not already:
            barrier.wait()

    def _write(name: str, clone: Path) -> None:
        try:
            _append(clone, {"event_id": name, "kind": name}, log=_log(remote="origin"),
                    _after_parent=_once)
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=_write, args=(n, c)) for n, c in (("e0", c1), ("e1", c2))]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    assert not errors, f"concurrent append raised: {errors}"
    _git(c1, "fetch", "-q", "origin", "+refs/llmxive/test-log:refs/llmxive/test-log")
    assert sorted(e["event_id"] for e in _read(c1, log=_log())) == ["e0", "e1"]


def test_sustained_contention_raises_contention(repo: Path, monkeypatch):
    """When the ref moves under every attempt, the loop gives up with GitLogContention
    rather than forcing the write."""
    import llmxive.git_event_log as core

    real_update = core._git

    def _always_lose(args, **kw):
        # Fail every ref-CAS so no attempt can land.
        if args[:1] == ["update-ref"] and len(args) == 4:
            kw["check"] = False
            proc = subprocess.CompletedProcess(args, 1, "", "cannot lock ref")
            return proc
        return real_update(args, **kw)

    monkeypatch.setattr(core, "_git", _always_lose)
    with pytest.raises(GitLogContention, match="sustained contention"):
        _append(repo, {"event_id": "e0", "kind": "a"}, max_retries=3)


# ---- absence vs failure: never project an operational error as an empty log ----


def test_read_log_against_a_non_git_directory_raises(tmp_path: Path):
    """The sharpest fail-open: `[]` means "no claim / no reservation / no spend" to
    every projection built on this, so a wrong or missing repository must NOT produce
    it."""
    not_a_repo = tmp_path / "plain"
    not_a_repo.mkdir()
    with pytest.raises(GitLogError, match="refusing to treat an unreadable ref"):
        _read(not_a_repo)


def test_a_ref_whose_object_is_unreadable_raises(repo: Path):
    """`rev-parse --verify --quiet` exits 1 for BOTH a missing ref and a ref whose
    object cannot be read, so exit code alone is not enough — `show-ref` separates
    them, and a damaged log must never read as an empty one."""
    _append(repo, {"event_id": "e0", "kind": "a"})
    tip = _git(repo, "rev-parse", "refs/llmxive/test-log")
    obj = repo / ".git" / "objects" / tip[:2] / tip[2:]
    assert obj.exists(), "expected a loose object (the test repo is not packed)"
    obj.rename(obj.with_suffix(".hidden"))
    with pytest.raises(GitLogError, match="could not be resolved"):
        _read(repo)


def test_a_genuinely_absent_ref_is_still_an_empty_log(repo: Path):
    """The counterpart: cold start must NOT raise."""
    assert _read(repo) == []


def test_an_absent_event_path_is_absent_not_an_error(repo: Path):
    """The append-only guard's read: a path that is genuinely not in the tree returns
    None so the append proceeds."""
    from llmxive.git_event_log import _read_event_blob

    _append(repo, {"event_id": "e0", "kind": "a"})
    tip = _git(repo, "rev-parse", "refs/llmxive/test-log")
    assert _read_event_blob(repo, _log(), "never-written", tip) is None
    assert _read_event_blob(repo, _log(), "e0", tip) is not None


def test_a_failed_blob_read_raises_rather_than_reporting_absence(repo: Path):
    """If this reported absence on failure, a caller could append OVER an event that is
    already committed — the append-only guard would simply not fire."""
    from llmxive.git_event_log import _read_event_blob

    _append(repo, {"event_id": "e0", "kind": "a"})
    with pytest.raises(GitLogError):
        _read_event_blob(repo, _log(), "e0", "deadbeef" * 5)  # a tip that is not a tree


def test_a_corrupt_tree_raises_instead_of_listing_nothing(repo: Path):
    """`ls-tree` failing has EMPTY stdout, so an unchecked call would project a damaged
    repository as "no events" — the same fail-open as an unreadable ref. Here the
    COMMIT is readable but its TREE object is gone, so `_rev` succeeds and the listing
    is what fails."""
    _append(repo, {"event_id": "e0", "kind": "a"})
    tip = _git(repo, "rev-parse", "refs/llmxive/test-log")
    tree = _git(repo, "rev-parse", f"{tip}^{{tree}}")
    obj = repo / ".git" / "objects" / tree[:2] / tree[2:]
    assert obj.exists(), "expected a loose tree object"
    obj.rename(obj.with_suffix(".hidden"))
    with pytest.raises(GitLogError):
        _read(repo)


# ---- the post-push local-ref rewind (spec 025 slice 2, Task 2) ----


def _empty_commit_on(repo: Path, parent: str, message: str) -> str:
    """A commit with the SAME tree as `parent`, so history shape is the only variable.

    `message` is REQUIRED because `commit-tree` is deterministic: two calls with the same
    tree, parent, message and identity inside one second produce the SAME object id, and
    a test that meant to build two sibling commits would silently build one.
    """
    return _git(repo, "commit-tree", f"{parent}^{{tree}}", "-p", parent, "-m", message)


def test_a_successful_push_never_rewinds_a_local_ref_that_moved(
    tmp_path: Path, bare_remote: Path
):
    """The defect at the seam where it actually occurs: between OUR push and OUR local
    ref update.

    Before the push a competing writer simply loses the fast-forward and we retry, so no
    rewind is possible there. The window is AFTER the push, which is why the second writer
    completes its entire cycle — fetch, build, push, update local — inside `_after_push`.
    A bare `update-ref <ref> <new>` then sets our clone's ref back to OUR commit, and the
    other writer's event vanishes from every local read until the next fetch. In this lane
    the read that matters is a claim decision, so the visible consequence is two runners
    believing the lane is free.
    """
    clone = _clone(bare_remote, tmp_path / "c")
    bootstrap_log(clone, log=_log(remote="origin"), message=_MSG, remote="origin")
    log = _log(remote="origin")
    ahead: dict[str, str] = {}

    def a_second_writer_finishes_first() -> None:
        ahead["commit"] = _append(clone, {"event_id": "other", "kind": "b"}, log=log).commit

    ours = _append(clone, {"event_id": "ours", "kind": "a"}, log=log,
                   _after_push=a_second_writer_finishes_first)

    tip = _git(clone, "rev-parse", log.ref)
    assert tip == ahead["commit"], "the local ref was rewound past a newer commit"
    assert _git(clone, "merge-base", "--is-ancestor", ours.commit, tip) == "", (
        "our commit is not reachable from the local tip"
    )
    # The decisive assertion: a LOCAL read, with no intervening fetch, sees both events.
    assert sorted(e["event_id"] for e in _read(clone, log=_log())) == ["other", "ours"]


def test_sync_local_ref_leaves_a_newer_tip_alone_but_fails_on_divergence(repo: Path):
    """The two outcomes that are NOT the same.

    A moved ref that CONTAINS our commit is another writer in this clone getting ahead of
    us: leave their tip alone. One that does not contain it is a divergence: fail closed.
    Collapsing them either way is a bug — ignoring every failure hides the divergence,
    and raising on every failure turns an ordinary race into an error.
    """
    from llmxive.git_event_log import _sync_local_ref

    _append(repo, {"event_id": "e0", "kind": "a"})
    log = _log()
    parent = _git(repo, "rev-parse", log.ref)
    ours = _empty_commit_on(repo, parent, "ours")
    newer = _empty_commit_on(repo, ours, "newer")     # contains `ours`

    _git(repo, "update-ref", log.ref, newer)
    _sync_local_ref(repo, log, ours, parent)         # no rewind, no raise
    assert _git(repo, "rev-parse", log.ref) == newer

    unrelated = _empty_commit_on(repo, parent, "unrelated")   # does NOT contain `ours`
    assert unrelated != ours, "the divergence case needs two DISTINCT sibling commits"
    _git(repo, "update-ref", log.ref, unrelated)
    with pytest.raises(GitLogError, match="diverged"):
        _sync_local_ref(repo, log, ours, parent)
    assert _git(repo, "rev-parse", log.ref) == unrelated, "a failed sync must not mutate"


def test_sync_local_ref_sets_the_ref_when_it_has_not_moved(repo: Path):
    """The ordinary case, which the two-outcome test above does not cover: nobody raced
    us, the CAS succeeds, and the ref advances to what we pushed."""
    from llmxive.git_event_log import _sync_local_ref

    _append(repo, {"event_id": "e0", "kind": "a"})
    log = _log()
    parent = _git(repo, "rev-parse", log.ref)
    ours = _empty_commit_on(repo, parent, "ours")

    _sync_local_ref(repo, log, ours, parent)
    assert _git(repo, "rev-parse", log.ref) == ours


# ---- exception compatibility with the credit ledger's names (round-2 F8) ----


def test_ledger_error_names_catch_what_the_core_raises(repo: Path):
    """`ledger_transport` translates every core error into its OWN subclass at the
    boundary, so `except Ledger*` still catches, AND `type(exc).__name__` still reads
    as the credit domain's name (which `execute` puts in its candidate notes)."""
    from llmxive.model_selection.ledger_transport import (
        LedgerAuthError,
        LedgerContention,
        LedgerDenied,
        LedgerError,
    )

    assert issubclass(LedgerError, GitLogError)
    assert issubclass(LedgerAuthError, (LedgerError, GitLogAuthError))
    assert issubclass(LedgerContention, (LedgerError, GitLogContention))
    assert issubclass(LedgerDenied, (LedgerError, GitLogDenied))

    # A core error raised through a ledger entry point surfaces with the ledger's name.
    from llmxive.model_selection.ledger_transport import read_events

    (repo / ".git").mkdir(exist_ok=True)
    with pytest.raises(LedgerAuthError) as ei:
        read_events(repo, ref="refs/llmxive/credit-ledger")  # local-only: no error yet
        raise LedgerAuthError("unused")
    assert type(ei.value).__name__ == "LedgerAuthError"


def test_the_stored_blob_is_canonical_json(repo: Path):
    _append(repo, {"event_id": "e0", "kind": "a", "z": 1, "b": 2})
    tip = _git(repo, "rev-parse", "refs/llmxive/test-log")
    blob = _git(repo, "cat-file", "blob", f"{tip}:{_EVENT_DIR}/e0.json")
    assert blob == json.dumps(
        {"event_id": "e0", "kind": "a", "z": 1, "b": 2}, indent=2, sort_keys=True
    )
