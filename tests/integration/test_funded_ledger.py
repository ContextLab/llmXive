"""Funded ledger (spec 027): the SAME CAS ledger mechanism on its own ref, USD amounts,
monthly epoch, and a recorded charge at reconcile. Real git repos and refs."""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from llmxive.model_selection.ledger_transport import (
    FUNDED_LEDGER_REF,
    LedgerConfig,
    bootstrap_ledger,
    read_events,
)
from llmxive.model_selection.reservations import (
    STATE_OPEN,
    STATE_RECONCILED,
    CreditObservation,
    project,
    reconcile,
    reconcile_settled,
    reserve,
    settle,
)

T0 = datetime(2026, 11, 23, 12, 0, 0, tzinfo=UTC)
CFG = LedgerConfig(remote=None, ref=FUNDED_LEDGER_REF)
EPOCH = "2026-11"


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    _git(["init", "-b", "main", str(r)], tmp_path)
    return r


@pytest.fixture
def remote_and_clone(tmp_path: Path):
    remote = tmp_path / "remote.git"
    _git(["init", "--bare", "-b", "main", str(remote)], tmp_path)
    a = tmp_path / "clone_A"
    _git(["clone", "--quiet", str(remote), str(a)], tmp_path)
    return remote, a


def _reserve(repo, rid, usd, *, cap, spend=0.0, config=CFG, now=T0):
    return reserve(
        repo, reservation_id=rid, worst_case_credits=usd, model="acme/alpha-large:prov-a",
        credit_observer=lambda: CreditObservation(spend=spend, effective_cap=cap, budget_epoch=EPOCH),
        lease_expires_at=now + timedelta(seconds=420), now=now, config=config,
    )


def test_funded_ref_is_separate_from_the_credit_ledger(repo):
    r = _reserve(repo, "f1", 0.25, cap=1.0)
    assert r.state == STATE_OPEN and r.worst_case_credits == 0.25
    assert read_events(repo) == []  # credit-ledger ref untouched
    assert [e["type"] for e in read_events(repo, ref=FUNDED_LEDGER_REF)] == ["open"]


def test_reconcile_records_the_charge_and_first_writer_wins(repo):
    _reserve(repo, "f1", 0.25, cap=1.0)
    reconcile(repo, "f1", charged=0.0024, now=T0, config=CFG)
    reconcile(repo, "f1", charged=0.25, now=T0, config=CFG)  # idempotent: no second event
    events = read_events(repo, ref=FUNDED_LEDGER_REF)
    assert [e["type"] for e in events].count("reconciled") == 1
    res = project(events)["f1"]
    assert res.state == STATE_RECONCILED and res.charged == 0.0024


def test_zero_charge_is_recorded_as_zero(repo):  # spec 5.9.2: 401/402/403 charge zero
    _reserve(repo, "f1", 0.25, cap=1.0)
    reconcile(repo, "f1", charged=0.0, now=T0, config=CFG)
    assert project(read_events(repo, ref=FUNDED_LEDGER_REF))["f1"].charged == 0.0


def test_negative_or_nan_charge_is_rejected(repo):
    _reserve(repo, "f1", 0.25, cap=1.0)
    for bad in (-0.01, float("nan")):
        with pytest.raises(ValueError):
            reconcile(repo, "f1", charged=bad, now=T0, config=CFG)


def test_existing_credit_ledger_reconcile_has_no_charge(repo):  # shared schema stays backward compatible
    _reserve(repo, "c1", 10.0, cap=100.0, config=LedgerConfig(remote=None))
    settle(repo, "c1", now=T0)
    reconcile_settled(repo, observed_spend=10.0, epoch=EPOCH, now=T0)
    assert project(read_events(repo))["c1"].charged is None


def test_bootstrap_funded_ref_on_a_remote(remote_and_clone):
    remote, a = remote_and_clone
    anchor = bootstrap_ledger(a, remote="origin", ref=FUNDED_LEDGER_REF)
    out = subprocess.run(
        ["git", "ls-remote", str(remote), FUNDED_LEDGER_REF], capture_output=True, text=True
    ).stdout
    assert out.split()[0] == anchor
    out2 = subprocess.run(
        ["git", "ls-remote", str(remote), "refs/llmxive/credit-ledger"], capture_output=True, text=True
    ).stdout
    assert out2.strip() == ""  # the credit ref was not created
