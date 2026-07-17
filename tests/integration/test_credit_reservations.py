"""Slice 1B (spec 026 / FR-016) — credit-reservation lifecycle over the real
strict-CAS ledger: projection, headroom-gated reserve, settle-retains-hold, the
attribution-PREFIX reconciliation, the crash-conservative + daily-reset sweep, the
heartbeat lease owner, and the cross-runner no-overspend guarantee (SC-004).
"""

from __future__ import annotations

import subprocess
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from llmxive.model_selection.ledger_transport import LEDGER_REF, LedgerDenied, read_events
from llmxive.model_selection.reservations import (
    STATE_OPEN,
    STATE_RECONCILED,
    STATE_SETTLING,
    CreditObservation,
    LedgerConfig,
    ReservationLease,
    counting_total,
    project,
    reconcile_settled,
    reserve,
    settle,
    sweep,
)

T0 = datetime(2026, 7, 16, 12, 0, 0, tzinfo=UTC)
EPOCH = "2026-07-17T03:45:00Z"
LEASE = T0 + timedelta(seconds=420)


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    _git(["init", "-b", "main", str(r)], tmp_path)
    return r


@pytest.fixture
def remote_and_two_clones(tmp_path: Path):
    remote = tmp_path / "remote.git"
    _git(["init", "--bare", "-b", "main", str(remote)], tmp_path)
    a = tmp_path / "clone_A"
    b = tmp_path / "clone_B"
    _git(["clone", "--quiet", str(remote), str(a)], tmp_path)
    _git(["clone", "--quiet", str(remote), str(b)], tmp_path)
    from llmxive.model_selection.ledger_transport import bootstrap_ledger

    bootstrap_ledger(a, remote="origin")  # #7: bootstrap the shared ledger once
    return remote, a, b


def _reserve(repo: Path, rid: str, wc: float, *, cap: float, spend: float, remote=None,
             epoch: str = EPOCH, model: str = "anthropic.claude-haiku-4-5"):
    return reserve(
        repo,
        reservation_id=rid,
        worst_case_credits=wc,
        model=model,
        credit_observer=lambda: CreditObservation(spend=spend, effective_cap=cap, budget_epoch=epoch),
        lease_expires_at=LEASE,
        now=T0,
        config=LedgerConfig(remote=remote),
    )


# ------------------------------ projection --------------------------------- #


def test_project_duplicate_open_does_not_regress_settling():
    """C12: a duplicate `open` event (cross-runner stale-local retry) must NOT
    overwrite an already-`settling` reservation nor reset its baseline/created_at."""
    events = [
        {"type": "open", "reservation_id": "X", "event_id": "X-open", "model": "m",
         "ts": "2026-07-16T12:00:00", "worst_case_credits": 10, "budget_epoch": "E",
         "settlement_baseline": 0, "created_at": "2026-07-16T12:00:00", "lease_expires_at": "z"},
        {"type": "settling", "reservation_id": "X", "event_id": "X-settling",
         "ts": "2026-07-16T12:01:00"},
        {"type": "open", "reservation_id": "X", "event_id": "X-open2", "model": "m",
         "ts": "2026-07-16T12:02:00", "worst_case_credits": 10, "budget_epoch": "E",
         "settlement_baseline": 99, "created_at": "2026-07-16T12:02:00", "lease_expires_at": "z"},
    ]
    res = project(events)
    assert res["X"].state == STATE_SETTLING  # not regressed to open
    assert res["X"].settlement_baseline == 0.0  # original preserved, not the duplicate's 99
    assert res["X"].created_at == "2026-07-16T12:00:00"





def test_reserve_settle_reconcile_projection(repo):
    r = _reserve(repo, "r1", 10.0, cap=100.0, spend=0.0)
    assert r.state == STATE_OPEN and r.counts
    settle(repo, "r1", now=T0)
    assert project(read_events(repo))["r1"].state == STATE_SETTLING
    reconcile_settled(repo, observed_spend=10.0, epoch=EPOCH, now=T0)
    assert project(read_events(repo))["r1"].state == STATE_RECONCILED


def test_counting_total_excludes_reconciled_and_other_epochs(repo):
    _reserve(repo, "open1", 5.0, cap=100.0, spend=0.0)
    _reserve(repo, "settling1", 7.0, cap=100.0, spend=0.0)
    settle(repo, "settling1", now=T0)
    res = project(read_events(repo))
    assert counting_total(res.values(), epoch=EPOCH) == 12.0  # open + settling
    assert counting_total(res.values(), epoch="other-epoch") == 0.0  # different epoch → 0


# ----------------------------- headroom gate ------------------------------- #


def test_reserve_denied_when_over_cap_appends_nothing(repo):
    with pytest.raises(LedgerDenied):
        _reserve(repo, "big", 30.0, cap=20.0, spend=0.0)  # 0 + 0 + 30 > 20
    assert read_events(repo) == []


def test_reserve_counts_against_a_second_reservation(repo):
    _reserve(repo, "r1", 8.0, cap=10.0, spend=0.0)  # counting = 8
    with pytest.raises(LedgerDenied):
        _reserve(repo, "r2", 5.0, cap=10.0, spend=0.0)  # 0 + 8 + 5 = 13 > 10
    assert set(project(read_events(repo))) == {"r1"}


def test_reserve_is_idempotent(repo):
    _reserve(repo, "r1", 8.0, cap=10.0, spend=0.0)
    # re-reserving the SAME id is admitted (idempotent) and does not double-count
    _reserve(repo, "r1", 8.0, cap=10.0, spend=0.0)
    res = project(read_events(repo))
    assert counting_total(res.values(), epoch=EPOCH) == 8.0


def test_fresh_spend_counts_against_headroom(repo):
    # cap 10, spend already 6, a 5-credit call: 6 + 0 + 5 = 11 > 10 → denied
    with pytest.raises(LedgerDenied):
        _reserve(repo, "r1", 5.0, cap=10.0, spend=6.0)


def test_reserve_epoch_and_baseline_come_from_observer(repo):
    """#2/C11: the reservation's epoch + settlement_baseline are derived from the
    FRESH credit observation (re-read each attempt), not fixed arguments."""
    calls = []

    def observer():
        calls.append(1)
        return CreditObservation(spend=42.0, effective_cap=1000.0, budget_epoch="EPOCH-X")

    r = reserve(repo, reservation_id="r1", worst_case_credits=10.0, model="m",
                credit_observer=observer, lease_expires_at=LEASE, now=T0)
    assert r.budget_epoch == "EPOCH-X"
    assert r.settlement_baseline == 42.0
    assert calls  # the observer was actually consulted inside the CAS attempt


def test_reserve_id_collision_fails_closed(repo):
    """#8: a re-reserve of the SAME id with a DIFFERENT identity must fail closed
    (else a bigger/other call could run under an older, smaller hold)."""
    _reserve(repo, "r1", 10.0, cap=1000.0, spend=0.0, model="modelA")
    with pytest.raises(LedgerDenied):  # different model
        _reserve(repo, "r1", 10.0, cap=1000.0, spend=0.0, model="modelB")
    with pytest.raises(LedgerDenied):  # different amount
        _reserve(repo, "r1", 20.0, cap=1000.0, spend=0.0, model="modelA")
    with pytest.raises(LedgerDenied):  # different epoch
        _reserve(repo, "r1", 10.0, cap=1000.0, spend=0.0, model="modelA", epoch="OTHER")
    # matching identity is an idempotent no-op (no double count, no error)
    r = _reserve(repo, "r1", 10.0, cap=1000.0, spend=0.0, model="modelA")
    assert r.model == "modelA"
    assert counting_total(project(read_events(repo)).values(), epoch=EPOCH) == 10.0


def test_settle_and_reconcile_are_idempotent(repo):
    """R4-2: a repeated transition (owner-returns vs sweeper-settles, or two
    reconcilers) is a no-op, NOT an append-only violation."""
    _reserve(repo, "r1", 10.0, cap=1000.0, spend=0.0)
    settle(repo, "r1", now=T0)
    settle(repo, "r1", now=T0 + timedelta(seconds=5))  # different ts — must not raise
    assert project(read_events(repo))["r1"].state == STATE_SETTLING
    reconcile_settled(repo, observed_spend=10.0, epoch=EPOCH, now=T0)
    # a second reconcile (e.g. daily-reset vs attribution race) is a no-op
    from llmxive.model_selection.reservations import _reconcile_one
    _reconcile_one(repo, "r1", now=T0 + timedelta(seconds=9), config=None)
    assert project(read_events(repo))["r1"].state == STATE_RECONCILED


def test_headroom_read_fails_closed_on_unbootstrapped_remote(remote_and_two_clones, tmp_path):
    """R4-3: a headroom read against a remote with NO ledger ref fails closed
    (never read as full headroom on a wrong/misconfigured remote)."""
    from llmxive.model_selection.ledger_transport import LedgerAuthError
    from llmxive.model_selection.reservations import outstanding_headroom_consumption

    empty_remote = tmp_path / "empty.git"
    _git(["init", "--bare", "-b", "main", str(empty_remote)], tmp_path)
    clone = tmp_path / "clone_empty"
    _git(["clone", "--quiet", str(empty_remote), str(clone)], tmp_path)
    with pytest.raises(LedgerAuthError):
        outstanding_headroom_consumption(clone, epoch=EPOCH, config=LedgerConfig(remote="origin"))


def test_reserve_rejects_bad_amount(repo):
    import math
    for bad in (-1.0, math.inf, math.nan):
        with pytest.raises(ValueError):
            _reserve(repo, "r1", bad, cap=1000.0, spend=0.0)


# --------------------- attribution-prefix reconciliation ------------------- #


def test_partial_spend_reconciles_only_covered_prefix(repo):
    """Two overlapping settling reservations + a PARTIAL spend increase → only the
    covered prefix reconciles; the rest keep counting (the rev-3 attribution rule)."""
    _reserve(repo, "r1", 5.0, cap=100.0, spend=0.0)
    _reserve(repo, "r2", 5.0, cap=100.0, spend=0.0)
    settle(repo, "r1", now=T0)
    settle(repo, "r2", now=T0)
    # only 5 of the 10 reserved credits have actually been charged so far
    reconciled = reconcile_settled(repo, observed_spend=5.0, epoch=EPOCH, now=T0)
    assert reconciled == ["r1"]  # prefix: r1 covered (cum 5 ≤ 5); r2 would be 10 > 5
    res = project(read_events(repo))
    assert res["r1"].state == STATE_RECONCILED
    assert res["r2"].state == STATE_SETTLING  # still counting
    assert counting_total(res.values(), epoch=EPOCH) == 5.0

    # once the rest of the charge lands, r2 reconciles too
    assert reconcile_settled(repo, observed_spend=10.0, epoch=EPOCH, now=T0) == ["r2"]
    assert counting_total(project(read_events(repo)).values(), epoch=EPOCH) == 0.0


def test_partial_spend_below_first_reconciles_nothing(repo):
    _reserve(repo, "r1", 5.0, cap=100.0, spend=0.0)
    settle(repo, "r1", now=T0)
    # only 3 credits charged — r1 (5) is NOT fully covered → never partially reconcile
    assert reconcile_settled(repo, observed_spend=3.0, epoch=EPOCH, now=T0) == []
    assert project(read_events(repo))["r1"].state == STATE_SETTLING


# --------------------------------- sweep ----------------------------------- #


def test_sweep_conservatively_settles_crashed_open(repo):
    _reserve(repo, "crashed", 10.0, cap=100.0, spend=0.0)  # lease = T0 + 420s
    later = LEASE + timedelta(seconds=10)  # lease expired, no heartbeat (owner crashed)
    out = sweep(repo, observed_spend=0.0, current_epoch=EPOCH, now=later)
    assert out["conservatively_settled"] == ["crashed"]
    r = project(read_events(repo))["crashed"]
    assert r.state == STATE_SETTLING and r.counts  # RETAINED, not released


def test_sweep_fetches_authoritative_ref_before_projecting(remote_and_two_clones):
    """#3: a fresh checkout that hasn't fetched refs/llmxive/credit-ledger has an
    EMPTY local projection; sweep MUST fetch first (not silently no-op)."""
    _remote, producer, fresh = remote_and_two_clones
    _reserve(producer, "r1", 5.0, cap=1000.0, spend=0.0, remote="origin")
    settle(producer, "r1", now=T0, config=LedgerConfig(remote="origin"))
    assert project(read_events(fresh)) == {}  # fresh clone is blind until it fetches
    out = sweep(fresh, observed_spend=5.0, current_epoch=EPOCH, now=T0, config=LedgerConfig(remote="origin"))
    assert out["reconciled"] == ["r1"]  # fetched, saw r1, reconciled it


def test_sweep_settlement_timeout_retains_hold_and_flags(repo):
    """R3-2: a settling hold past the timeout with NO observed spend is FLAGGED but
    RETAINED — releasing it would free headroom for an unobserved charge (overspend).
    It is only ever released by attribution or the daily reset."""
    _reserve(repo, "r1", 10.0, cap=1000.0, spend=0.0)  # created + settled at T0
    settle(repo, "r1", now=T0)
    # within the timeout: not flagged, still counting
    soon = T0 + timedelta(seconds=1800)
    out_early = sweep(repo, observed_spend=0.0, current_epoch=EPOCH, now=soon, settlement_timeout_s=3600.0)
    assert out_early["settlement_overdue"] == []
    assert project(read_events(repo))["r1"].counts
    # past the timeout, spend STILL 0: flagged for attention but the hold is RETAINED
    later = T0 + timedelta(seconds=7200)
    out = sweep(repo, observed_spend=0.0, current_epoch=EPOCH, now=later, settlement_timeout_s=3600.0)
    assert out["reconciled"] == [] and out["settlement_overdue"] == ["r1"]
    r = project(read_events(repo))["r1"]
    assert r.state == STATE_SETTLING and r.counts  # NOT released
    # once the charge finally lands, attribution releases it normally
    assert sweep(repo, observed_spend=10.0, current_epoch=EPOCH, now=later)["reconciled"] == ["r1"]
    assert not project(read_events(repo))["r1"].counts


def test_sweep_discards_prior_epoch_reservation(repo):
    reserve(
        repo, reservation_id="old", worst_case_credits=9.0, model="m",
        credit_observer=lambda: CreditObservation(
            spend=0.0, effective_cap=100.0, budget_epoch="2026-07-16T03:45:00Z"),  # yesterday
        lease_expires_at=LEASE, now=T0,
    )
    out = sweep(repo, observed_spend=0.0, current_epoch=EPOCH, now=T0 + timedelta(days=1))
    assert out["discarded_prior_epoch"] == ["old"]
    res = project(read_events(repo))
    assert res["old"].state == STATE_RECONCILED
    assert counting_total(res.values(), epoch=EPOCH) == 0.0  # no longer counts


# ------------------------------ heartbeat ---------------------------------- #


def test_reservation_lease_heartbeats_during_call(repo):
    _reserve(repo, "r1", 10.0, cap=100.0, spend=0.0)
    before = LEASE
    with ReservationLease(repo, "r1", interval_s=0.05, lease_duration_s=600.0):
        # let the daemon heartbeat at least once while the "call" runs
        deadline = datetime.now(UTC) + timedelta(seconds=3)
        while datetime.now(UTC) < deadline:
            if project(read_events(repo))["r1"].lease_expires_at > before.isoformat():
                break
    extended = project(read_events(repo))["r1"].lease_expires_at
    assert extended > before.isoformat()  # lease was refreshed by the owner


# --------------------- cross-runner no-overspend (SC-004) ------------------ #


def test_two_runners_cannot_collectively_overspend(remote_and_two_clones):
    """Cap fits ONE reservation; two runners race → exactly one is admitted, the
    other is denied once the CAS re-check sees the winner counting. This is the
    atomic-across-runners guarantee (no collective overspend)."""
    _remote, clone_a, clone_b = remote_and_two_clones
    barrier = threading.Barrier(2)
    results: dict[str, str] = {}

    def run(clone: Path, rid: str) -> None:
        try:
            barrier.wait(timeout=10)
            reserve(
                clone, reservation_id=rid, worst_case_credits=10.0, model="m",
                credit_observer=lambda: CreditObservation(
                    spend=0.0, effective_cap=10.0, budget_epoch=EPOCH),
                lease_expires_at=LEASE, now=T0, config=LedgerConfig(remote="origin"),
            )
            results[rid] = "admitted"
        except LedgerDenied:
            results[rid] = "denied"
        except BaseException as exc:
            results[rid] = f"error: {exc!r}"

    ta = threading.Thread(target=run, args=(clone_a, "rA"))
    tb = threading.Thread(target=run, args=(clone_b, "rB"))
    ta.start()
    tb.start()
    ta.join(20)
    tb.join(20)

    assert sorted(results.values()) == ["admitted", "denied"], results
    # exactly ONE reservation on the authoritative ref
    subprocess.run(
        ["git", "fetch", "--quiet", "origin", f"+{LEDGER_REF}:{LEDGER_REF}"],
        cwd=str(clone_a), check=True,
    )
    admitted = [r for r in project(read_events(clone_a)).values() if r.state == STATE_OPEN]
    assert len(admitted) == 1
