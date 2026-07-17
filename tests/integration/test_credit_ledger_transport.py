"""Slice 1B (spec 026 / FR-016) — strict per-record CAS ledger transport against
REAL git clones (Constitution III: real transport, not a mock).

Builds a bare shared remote + two working clones and drives the ACTUAL
``append_event`` CAS: concurrent reservers race, only one fast-forwards, the loser
re-fetches + recomputes onto the new tip, and NO event is lost. Also covers cold
start, the deterministic non-fast-forward rejection, and auth fail-closed.
"""

from __future__ import annotations

import subprocess
import threading
from pathlib import Path

import pytest

from llmxive.model_selection.ledger_transport import (
    LEDGER_REF,
    LedgerAuthError,
    LedgerConfig,
    _push_fast_forward,
    _rev,
    append_event,
    read_events,
)


def _git(args: list[str], cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.fixture
def remote_and_clones(tmp_path: Path):
    """A bare shared remote + two independent clones (the cross-runner topology)."""
    remote = tmp_path / "remote.git"
    _git(["init", "--bare", "-b", "main", str(remote)], tmp_path)
    clones = []
    for name in ("A", "B"):
        path = tmp_path / f"clone_{name}"
        _git(["clone", "--quiet", str(remote), str(path)], tmp_path)
        clones.append(path)
    from llmxive.model_selection.ledger_transport import bootstrap_ledger

    bootstrap_ledger(clones[0], remote="origin")  # #7: the ledger must be bootstrapped once
    return remote, clones[0], clones[1]


def _event(rid: str, credits: float) -> dict:
    # a COMPLETE open event (the ledger now strict-validates the full schema)
    return {"event_id": f"{rid}-open", "reservation_id": rid, "type": "open",
            "worst_case_credits": credits, "model": "m", "budget_epoch": "E",
            "settlement_baseline": 0.0, "created_at": "2026-07-16T12:00:00+00:00",
            "lease_expires_at": "2026-07-16T12:07:00+00:00", "ts": "2026-07-16T12:00:00+00:00"}


def test_cold_start_has_no_events(remote_and_clones):
    _remote, clone_a, _clone_b = remote_and_clones
    assert read_events(clone_a) == []


def test_single_append_round_trips_to_a_fresh_clone(remote_and_clones, tmp_path):
    remote, clone_a, _clone_b = remote_and_clones
    append_event(clone_a, _event("r1", 10.0), config=LedgerConfig(remote="origin"))
    # a THIRD, freshly-made clone must observe the event on the authoritative ref
    fresh = tmp_path / "clone_fresh"
    _git(["clone", "--quiet", str(remote), str(fresh)], tmp_path)
    subprocess.run(
        ["git", "fetch", "--quiet", "origin", f"+{LEDGER_REF}:{LEDGER_REF}"],
        cwd=str(fresh), check=True,
    )
    events = read_events(fresh)
    assert [e["reservation_id"] for e in events] == ["r1"]


def test_non_fast_forward_push_is_rejected_not_merged(remote_and_clones):
    """The deterministic CAS core: a commit built on a STALE tip is rejected
    (False), never merged — this is what makes it a compare-and-swap."""
    _remote, clone_a, clone_b = remote_and_clones
    append_event(clone_a, _event("r1", 10.0), config=LedgerConfig(remote="origin"))  # ref now has r1

    # B builds an event on the EMPTY tip (parent=None) — a stale base — and pushes.
    from llmxive.model_selection.ledger_transport import _append_commit

    stale_commit = _append_commit(clone_b, None, _event("r2", 20.0))
    assert _push_fast_forward(clone_b, "origin", stale_commit) is False  # rejected, not merged


def test_concurrent_reservers_no_event_lost(remote_and_clones):
    """Two clones append at the same time; the CAS loop makes both survive."""
    _remote, clone_a, clone_b = remote_and_clones
    barrier = threading.Barrier(2)
    errors: list[BaseException] = []

    def reserve(clone: Path, rid: str, credits: float) -> None:
        try:
            barrier.wait(timeout=10)
            append_event(clone, _event(rid, credits), config=LedgerConfig(remote="origin"), max_retries=16)
        except BaseException as exc:
            errors.append(exc)

    ta = threading.Thread(target=reserve, args=(clone_a, "rA", 10.0))
    tb = threading.Thread(target=reserve, args=(clone_b, "rB", 20.0))
    ta.start()
    tb.start()
    ta.join(20)
    tb.join(20)

    assert not errors, errors
    # Re-fetch each clone from the authoritative ref: BOTH reservations survive.
    for clone in (clone_a, clone_b):
        subprocess.run(
            ["git", "fetch", "--quiet", "origin", f"+{LEDGER_REF}:{LEDGER_REF}"],
            cwd=str(clone), check=True,
        )
        rids = {e["reservation_id"] for e in read_events(clone)}
        assert rids == {"rA", "rB"}, rids


def test_predicate_denial_appends_nothing(remote_and_clones):
    _remote, clone_a, _clone_b = remote_and_clones
    from llmxive.model_selection.ledger_transport import LedgerDenied

    def deny(_events):
        return False, "no headroom"

    tip_before = _rev(clone_a, LEDGER_REF)  # the bootstrap anchor
    with pytest.raises(LedgerDenied):
        append_event(clone_a, _event("r1", 10.0), config=LedgerConfig(remote="origin"), predicate=deny)
    assert read_events(clone_a) == []  # nothing appended
    assert _rev(clone_a, LEDGER_REF) == tip_before  # ref unchanged


def test_remote_write_requires_bootstrap(tmp_path):
    """#7: a remote append to a NON-bootstrapped ledger fails closed (never spawns a
    divergent ledger); after bootstrap it succeeds."""
    from llmxive.model_selection.ledger_transport import LedgerAuthError, bootstrap_ledger

    remote = tmp_path / "remote.git"
    _git(["init", "--bare", "-b", "main", str(remote)], tmp_path)
    clone = tmp_path / "clone"
    _git(["clone", "--quiet", str(remote), str(clone)], tmp_path)
    with pytest.raises(LedgerAuthError):
        append_event(clone, _event("r1", 10.0), config=LedgerConfig(remote="origin"))  # not bootstrapped
    bootstrap_ledger(clone, remote="origin")
    append_event(clone, _event("r1", 10.0), config=LedgerConfig(remote="origin"))  # now allowed
    assert [e["reservation_id"] for e in read_events(clone)] == ["r1"]


def test_bootstrap_refuses_divergent_local_vs_empty_remote(tmp_path):
    """R3-4: a LOCAL ledger + an EMPTY (wrong/misconfigured) remote must NOT produce
    a divergent ledger — bootstrap AND append both fail closed; the wrong remote
    never receives a ledger ref."""
    from llmxive.model_selection.ledger_transport import (
        LedgerAuthError,
        _remote_ledger_oid,
        bootstrap_ledger,
    )

    local = tmp_path / "local"
    _git(["init", "-b", "main", str(local)], tmp_path)
    append_event(local, _event("r1", 5.0))  # local-only ledger exists
    wrong = tmp_path / "wrong.git"
    _git(["init", "--bare", "-b", "main", str(wrong)], tmp_path)
    _git(["remote", "add", "origin", str(wrong)], local)

    with pytest.raises(LedgerAuthError):
        bootstrap_ledger(local, remote="origin")  # local exists, remote empty → refuse
    with pytest.raises(LedgerAuthError):
        append_event(local, _event("r2", 5.0), config=LedgerConfig(remote="origin"))  # not bootstrapped on remote
    assert _remote_ledger_oid(local, "origin") is None  # wrong remote stayed empty


def test_expected_anchor_gates_remote_identity(remote_and_clones):
    """R3-4: pinning the trusted anchor rejects a remote whose tip does not descend
    from it (an unrelated/divergent ledger)."""
    from llmxive.model_selection.ledger_transport import LEDGER_REF, LedgerAuthError, _rev

    _remote, clone_a, _clone_b = remote_and_clones
    anchor = _rev(clone_a, LEDGER_REF)  # the real bootstrap anchor
    append_event(clone_a, _event("r1", 5.0), config=LedgerConfig(remote="origin", expected_anchor=anchor))  # ok
    with pytest.raises(LedgerAuthError):
        append_event(clone_a, _event("r2", 5.0), config=LedgerConfig(remote="origin", expected_anchor="a" * 40))


def test_bootstrap_is_idempotent(tmp_path):
    from llmxive.model_selection.ledger_transport import bootstrap_ledger

    remote = tmp_path / "remote.git"
    _git(["init", "--bare", "-b", "main", str(remote)], tmp_path)
    clone = tmp_path / "clone"
    _git(["clone", "--quiet", str(remote), str(clone)], tmp_path)
    first = bootstrap_ledger(clone, remote="origin")
    again = bootstrap_ledger(clone, remote="origin")
    assert first == again  # no-op second time


def test_auth_failure_fails_closed(tmp_path):
    """An unreachable authoritative ref raises LedgerAuthError (never a silent
    unguarded append)."""
    clone = tmp_path / "lonely"
    _git(["init", "-b", "main", str(clone)], tmp_path)
    _git(["remote", "add", "origin", str(tmp_path / "does-not-exist.git")], clone)
    with pytest.raises(LedgerAuthError):
        append_event(clone, _event("r1", 10.0), config=LedgerConfig(remote="origin"))


def test_local_only_cas_serializes_same_clone(remote_and_clones):
    """With no remote, update-ref CAS still serializes same-clone appends."""
    _remote, clone_a, _clone_b = remote_and_clones
    append_event(clone_a, _event("r1", 10.0))  # local-only
    append_event(clone_a, _event("r2", 20.0))
    rids = [e["reservation_id"] for e in read_events(clone_a)]
    assert sorted(rids) == ["r1", "r2"]


def _commit_raw_event(repo: Path, filename: str, content: str) -> None:
    """Inject a RAW (possibly non-JSON) event blob onto the ledger ref via plumbing."""
    import os
    import tempfile

    from llmxive.model_selection.ledger_transport import _EVENT_DIR, _rev

    blob = subprocess.run(
        ["git", "hash-object", "-w", "--stdin"], cwd=str(repo),
        input=content, capture_output=True, text=True, check=True,
    ).stdout.strip()
    parent = _rev(repo, LEDGER_REF)
    ident = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    with tempfile.TemporaryDirectory() as td:
        env = {**os.environ, "GIT_INDEX_FILE": os.path.join(td, "index")}
        if parent:
            subprocess.run(["git", "read-tree", parent], cwd=str(repo), env=env, check=True)
        subprocess.run(
            ["git", "update-index", "--add", "--cacheinfo",
             f"100644,{blob},{_EVENT_DIR}/{filename}"], cwd=str(repo), env=env, check=True,
        )
        tree = subprocess.run(
            ["git", "write-tree"], cwd=str(repo), env=env, capture_output=True, text=True, check=True
        ).stdout.strip()
    args = ["git", "commit-tree", tree, "-m", "raw"] + (["-p", parent] if parent else [])
    commit = subprocess.run(
        args, cwd=str(repo), env={**os.environ, **ident}, capture_output=True, text=True, check=True
    ).stdout.strip()
    subprocess.run(["git", "update-ref", LEDGER_REF, commit], cwd=str(repo), check=True)


def test_corrupt_event_fails_closed(remote_and_clones):
    """C4: a corrupt event on the AUTHORITATIVE ledger must RAISE, not silently skip
    (a skipped counting event would under-count headroom → overspend)."""
    from llmxive.model_selection.ledger_transport import LedgerError

    _remote, clone_a, _clone_b = remote_and_clones
    append_event(clone_a, _event("r1", 10.0))
    _commit_raw_event(clone_a, "r2-open.json", "{ this is not json")
    with pytest.raises(LedgerError):
        read_events(clone_a)


def test_open_event_missing_worst_case_rejected_at_write(remote_and_clones):
    """R3-1: an `open` event without worst_case_credits must be REJECTED at write
    (it would otherwise project as a phantom 0-credit counting reservation)."""
    _remote, clone_a, _clone_b = remote_and_clones
    bad = {"event_id": "X-open", "reservation_id": "X", "type": "open", "model": "m",
           "budget_epoch": "E", "settlement_baseline": 0.0, "created_at": "2026-07-16T12:00:00+00:00",
           "lease_expires_at": "2026-07-16T12:07:00+00:00", "ts": "2026-07-16T12:00:00+00:00"}
    with pytest.raises(ValueError):
        append_event(clone_a, bad)
    assert read_events(clone_a) == []


def test_read_fails_closed_on_schema_invalid_event(remote_and_clones):
    """R3-1: a valid-JSON but schema-INVALID event on the ref fails closed on READ
    (not just at write) — a manually-corrupted/older malformed event can't slip in."""
    _remote, clone_a, _clone_b = remote_and_clones
    from llmxive.model_selection.ledger_transport import LedgerError

    # valid JSON, but an `open` missing worst_case_credits (bypasses write validation)
    _commit_raw_event(
        clone_a, "Z-open.json",
        '{"event_id":"Z-open","reservation_id":"Z","type":"open","budget_epoch":"E","ts":"2026-07-16T12:00:00+00:00"}',
    )
    with pytest.raises(LedgerError):
        read_events(clone_a)


def test_read_fails_closed_on_path_payload_id_mismatch(remote_and_clones):
    """R3-1: a renamed event file (path != payload event_id) is tampering → fail closed."""
    _remote, clone_a, _clone_b = remote_and_clones
    from llmxive.model_selection.ledger_transport import LedgerError

    _commit_raw_event(clone_a, "renamed.json", _canonical_full("r9"))
    with pytest.raises(LedgerError):
        read_events(clone_a)


def _canonical_full(rid: str) -> str:
    import json

    return json.dumps({
        "event_id": f"{rid}-open", "reservation_id": rid, "type": "open", "model": "m",
        "worst_case_credits": 1.0, "budget_epoch": "E", "settlement_baseline": 0.0,
        "created_at": "2026-07-16T12:00:00+00:00", "lease_expires_at": "2026-07-16T12:07:00+00:00",
        "ts": "2026-07-16T12:00:00+00:00",
    })


def test_append_event_rejects_unsafe_ids(remote_and_clones):
    """C9: ids that aren't a single safe path component are rejected (e.g. slice-3
    model-derived ids containing '/')."""
    _remote, clone_a, _clone_b = remote_and_clones
    ts = "2026-07-16T12:00:00+00:00"
    with pytest.raises(ValueError):  # unsafe event_id
        append_event(clone_a, {"event_id": "a/b", "reservation_id": "r", "type": "settling", "ts": ts})
    with pytest.raises(ValueError):  # unsafe reservation_id (e.g. a model-derived id)
        append_event(clone_a, {"event_id": "e", "reservation_id": "Qwen/Qwen2.5", "type": "settling", "ts": ts})
    assert read_events(clone_a) == []  # nothing was written
