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
    return remote, clones[0], clones[1]


def _event(rid: str, credits: float) -> dict:
    return {"event_id": f"{rid}-open", "reservation_id": rid, "type": "open",
            "worst_case_credits": credits}


def test_cold_start_has_no_events(remote_and_clones):
    _remote, clone_a, _clone_b = remote_and_clones
    assert read_events(clone_a) == []


def test_single_append_round_trips_to_a_fresh_clone(remote_and_clones, tmp_path):
    remote, clone_a, _clone_b = remote_and_clones
    append_event(clone_a, _event("r1", 10.0), remote="origin")
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
    append_event(clone_a, _event("r1", 10.0), remote="origin")  # ref now has r1

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
            append_event(clone, _event(rid, credits), remote="origin", max_retries=16)
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

    with pytest.raises(LedgerDenied):
        append_event(clone_a, _event("r1", 10.0), remote="origin", predicate=deny)
    assert read_events(clone_a) == []  # nothing appended
    assert _rev(clone_a, LEDGER_REF) is None


def test_auth_failure_fails_closed(tmp_path):
    """An unreachable authoritative ref raises LedgerAuthError (never a silent
    unguarded append)."""
    clone = tmp_path / "lonely"
    _git(["init", "-b", "main", str(clone)], tmp_path)
    _git(["remote", "add", "origin", str(tmp_path / "does-not-exist.git")], clone)
    with pytest.raises(LedgerAuthError):
        append_event(clone, _event("r1", 10.0), remote="origin")


def test_local_only_cas_serializes_same_clone(remote_and_clones):
    """With no remote, update-ref CAS still serializes same-clone appends."""
    _remote, clone_a, _clone_b = remote_and_clones
    append_event(clone_a, _event("r1", 10.0))  # local-only
    append_event(clone_a, _event("r2", 20.0))
    rids = [e["reservation_id"] for e in read_events(clone_a)]
    assert sorted(rids) == ["r1", "r2"]
