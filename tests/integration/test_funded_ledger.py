"""Funded ledger (spec 027): the SAME CAS ledger mechanism on its own ref, USD amounts,
monthly epoch, and a recorded charge at reconcile. Real git repos and refs."""

from __future__ import annotations

import subprocess
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from llmxive.backends.hf_budget import (
    FundedSpend,
    FundedUnavailable,
    funded_guard,
    funded_observer,
    funded_spend,
    reserve_funded,
    settle_funded,
)
from llmxive.model_selection.ledger_transport import (
    FUNDED_LEDGER_ANCHOR_ENV,
    FUNDED_LEDGER_REF,
    LedgerConfig,
    LedgerDenied,
    bootstrap_ledger,
    fetch_ledger,
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


def test_two_clones_race_to_reconcile_exactly_one_charge_wins(tmp_path: Path):
    remote = tmp_path / "remote.git"
    _git(["init", "--bare", "-b", "main", str(remote)], tmp_path)
    clones = []
    for name in ("A", "B"):
        path = tmp_path / f"clone_{name}"
        _git(["clone", "--quiet", str(remote), str(path)], tmp_path)
        clones.append(path)
    anchor = bootstrap_ledger(clones[0], remote="origin", ref=FUNDED_LEDGER_REF)
    cfg = LedgerConfig(remote="origin", expected_anchor=anchor, ref=FUNDED_LEDGER_REF)
    _reserve(clones[0], "f1", 0.25, cap=1.0, config=cfg)

    gate = threading.Event()
    errors: list[BaseException] = []

    def go(clone: Path, charge: float) -> None:
        try:
            gate.wait()
            reconcile(clone, "f1", charged=charge, now=T0, config=cfg)
        except BaseException as exc:
            errors.append(exc)

    threads = [
        threading.Thread(target=go, args=(clones[0], 0.01)),
        threading.Thread(target=go, args=(clones[1], 0.02)),
    ]
    for t in threads:
        t.start()
    gate.set()
    for t in threads:
        t.join()
    assert errors == []

    fetch_ledger(clones[0], cfg)
    events = read_events(clones[0], ref=FUNDED_LEDGER_REF)
    reconciled = [e for e in events if e["type"] == "reconciled"]
    assert len(reconciled) == 1  # the loser became a no-op
    res = project(events)["f1"]
    assert res.state == STATE_RECONCILED and res.charged in (0.01, 0.02)
    assert res.charged == reconciled[0]["charged"]


def test_funded_ledger_bootstrap_cli_prints_the_anchor_of_the_ref_it_created(repo, monkeypatch, capsys):
    from llmxive.cli import main

    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(repo))
    assert main(["funded-ledger-bootstrap", "--no-remote"]) == 0
    out = capsys.readouterr().out
    tip = subprocess.run(
        ["git", "rev-parse", FUNDED_LEDGER_REF], cwd=str(repo), capture_output=True, text=True, check=True
    ).stdout.strip()
    assert f"LLMXIVE_FUNDED_LEDGER_ANCHOR={tip}" in out
    assert FUNDED_LEDGER_REF in out
    # idempotent re-run reports the same anchor; credit ref untouched
    assert main(["funded-ledger-bootstrap", "--no-remote"]) == 0
    assert tip in capsys.readouterr().out
    missing = subprocess.run(
        ["git", "rev-parse", "--verify", "-q", "refs/llmxive/credit-ledger"], cwd=str(repo), capture_output=True
    )
    assert missing.returncode != 0


# --------------------------------------------------------------------------- #
# Allowance guard (backends/hf_budget.py, spec 027 section 5.6) over real refs.
# --------------------------------------------------------------------------- #


def U(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


@pytest.fixture
def remote_and_two_clones(tmp_path: Path):
    remote = tmp_path / "remote.git"
    _git(["init", "--bare", "-b", "main", str(remote)], tmp_path)
    a = tmp_path / "clone_A"
    b = tmp_path / "clone_B"
    _git(["clone", "--quiet", str(remote), str(a)], tmp_path)
    _git(["clone", "--quiet", str(remote), str(b)], tmp_path)
    bootstrap_ledger(a, remote="origin", ref=FUNDED_LEDGER_REF)
    return remote, a, b


def test_funded_spend_and_guard_from_real_events(repo, monkeypatch):
    monkeypatch.delenv("LLMXIVE_HF_MONTHLY_USD", raising=False)
    for rid, usd, day, charged in [("a", 4.0, "2026-11-20", 4.0), ("b", 2.0, "2026-11-23", 1.5),
                                   ("c", 0.5, "2026-11-23", None), ("d", 0.25, "2026-11-21", None)]:
        _reserve(repo, rid, usd, cap=1e9, now=U(day + "T09:00:00"))
        if charged is not None:
            reconcile(repo, rid, charged=charged, now=U(day + "T09:01:00"), config=CFG)
    now = U("2026-11-23T12:00:00")
    assert funded_spend(project(read_events(repo, ref=FUNDED_LEDGER_REF)).values(), now=now) == FundedSpend(5.5, 4.25, 0.75)
    monkeypatch.setenv("LLMXIVE_HF_BILL_TO", "grp123")
    monkeypatch.setenv("HF_TOKEN", "hf_t")
    g = funded_guard(repo, now=now, config=CFG, org_balance_fetch=lambda: None)
    assert g.effective_cap_usd == pytest.approx(27.125) and g.available_usd == pytest.approx(20.875)
    assert (g.epoch, g.source, g.monthly_usd) == ("2026-11", "live", 50.0)
    assert g.org_balance_usd is None  # cross-check unavailable is recorded, never "unlimited"
    # a reported org balance below the remaining allowance wins
    g2 = funded_guard(repo, now=now, config=CFG, org_balance_fetch=lambda: 2.0)
    assert g2.org_balance_usd == 2.0
    assert g2.effective_cap_usd == pytest.approx(7.5) and g2.available_usd == pytest.approx(1.25)


def test_guard_fails_closed_without_bill_to(repo, monkeypatch):
    monkeypatch.delenv("LLMXIVE_HF_BILL_TO", raising=False)
    monkeypatch.setenv("HF_TOKEN", "hf_t")
    with pytest.raises(FundedUnavailable, match="LLMXIVE_HF_BILL_TO"):
        funded_guard(repo, now=T0, config=CFG, org_balance_fetch=lambda: None)


def test_guard_fails_closed_without_token(repo, monkeypatch):
    monkeypatch.setenv("LLMXIVE_HF_BILL_TO", "grp123")
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.setenv("PATH", "/nonexistent")  # no Keychain CLI either; the guard stops before git
    with pytest.raises(FundedUnavailable, match="HF_TOKEN"):
        funded_guard(repo, now=T0, config=CFG, org_balance_fetch=lambda: None)


def test_guard_fails_closed_without_anchor(repo, monkeypatch):
    monkeypatch.setenv("LLMXIVE_HF_BILL_TO", "grp123")
    monkeypatch.setenv("HF_TOKEN", "hf_t")
    monkeypatch.delenv(FUNDED_LEDGER_ANCHOR_ENV, raising=False)
    with pytest.raises(FundedUnavailable, match=FUNDED_LEDGER_ANCHOR_ENV):
        funded_guard(repo, now=T0, org_balance_fetch=lambda: None)  # config from env


def test_guard_fails_closed_when_ledger_sync_fails(remote_and_clone, monkeypatch):
    _remote, a = remote_and_clone  # remote exists but the funded ref was never bootstrapped
    monkeypatch.setenv("LLMXIVE_HF_BILL_TO", "grp123")
    monkeypatch.setenv("HF_TOKEN", "hf_t")
    with pytest.raises(FundedUnavailable, match="ledger"):
        funded_guard(a, now=T0, config=LedgerConfig(remote="origin", ref=FUNDED_LEDGER_REF),
                     org_balance_fetch=lambda: None)


def test_guard_syncs_the_authoritative_ref_before_projecting(remote_and_two_clones, monkeypatch):
    _remote, a, b = remote_and_two_clones
    cfg = LedgerConfig(remote="origin", ref=FUNDED_LEDGER_REF)
    _reserve(a, "ra", 5.0, cap=1e9, config=cfg)
    monkeypatch.delenv("LLMXIVE_HF_MONTHLY_USD", raising=False)
    monkeypatch.setenv("LLMXIVE_HF_BILL_TO", "grp123")
    monkeypatch.setenv("HF_TOKEN", "hf_t")
    g = funded_guard(b, now=T0, config=cfg, org_balance_fetch=lambda: None)  # b never saw "ra" locally
    assert g.outstanding_usd == 5.0


def test_guard_rejects_the_credit_ledger_config(repo, monkeypatch):
    monkeypatch.setenv("LLMXIVE_HF_BILL_TO", "grp123")
    monkeypatch.setenv("HF_TOKEN", "hf_t")
    with pytest.raises(ValueError, match="funded"):
        funded_guard(repo, now=T0, config=LedgerConfig(remote=None), org_balance_fetch=lambda: None)


def test_prior_month_hold_does_not_count(repo):
    _reserve(repo, "old", 30.0, cap=1e9, now=U("2026-11-30T23:59:00"))          # epoch 2026-11, never settled
    obs = funded_observer(repo, config=CFG, now_fn=lambda: U("2026-12-01T00:01:00"))()
    assert (obs.budget_epoch, obs.spend) == ("2026-12", 0.0)
    assert funded_spend(project(read_events(repo, ref=FUNDED_LEDGER_REF)).values(), now=U("2026-12-01T00:01:00")).outstanding_usd == 0.0


def test_two_runners_cannot_overspend_the_allowance(remote_and_two_clones, monkeypatch):
    monkeypatch.delenv("LLMXIVE_HF_MONTHLY_USD", raising=False)
    _remote, a, b = remote_and_two_clones
    cfg = LedgerConfig(remote="origin", ref=FUNDED_LEDGER_REF)
    now = U("2026-11-30T12:00:00")  # last day: cap = the whole $50 month
    # Both clones start from the SAME authoritative tip.
    for clone in (a, b):
        fetch_ledger(clone, cfg)
    tips = {subprocess.run(["git", "rev-parse", FUNDED_LEDGER_REF], cwd=str(c), capture_output=True,
                           text=True, check=True).stdout.strip() for c in (a, b)}
    assert len(tips) == 1
    # Each runner's FIRST pricing waits until the other has priced too, so both price
    # against that same tip; one CAS push must then lose and re-price.
    priced = threading.Barrier(2)
    calls: dict[str, int] = {"ra": 0, "rb": 0}
    results: dict[str, str] = {}

    def observer_for(clone, rid):
        inner = funded_observer(clone, config=cfg, now_fn=lambda: now)

        def observe():
            obs = inner()
            calls[rid] += 1
            if calls[rid] == 1:
                priced.wait(timeout=20)
            return obs
        return observe

    def run(clone, rid):
        try:
            reserve(clone, reservation_id=rid, worst_case_credits=30.0, model="m",
                    lease_expires_at=now + timedelta(seconds=420),
                    credit_observer=observer_for(clone, rid), now=now, config=cfg)
            results[rid] = "ok"
        except LedgerDenied:
            results[rid] = "denied"
        except BaseException as exc:  # surfaced in the assertion
            results[rid] = f"error: {exc!r}"

    ts = [threading.Thread(target=run, args=(a, "ra")), threading.Thread(target=run, args=(b, "rb"))]
    for t in ts:
        t.start()
    for t in ts:
        t.join(60)
    assert sorted(results.values()) == ["denied", "ok"], results               # $50 month, two $30 holds
    loser = next(rid for rid, r in results.items() if r == "denied")
    assert calls[loser] >= 2, calls  # the loser re-priced after its CAS push was rejected
    fetch_ledger(a, cfg)
    held = sum(r.worst_case_credits for r in project(read_events(a, ref=FUNDED_LEDGER_REF)).values())
    assert held <= 50.0


def test_december_hold_does_not_count_against_january(repo, monkeypatch):
    monkeypatch.delenv("LLMXIVE_HF_MONTHLY_USD", raising=False)
    dec31 = U("2026-12-31T23:59:30")
    r = reserve_funded(repo, reservation_id="dec", worst_case_usd=45.0, model="m",
                       lease_expires_at=dec31 + timedelta(seconds=420), now=dec31, config=CFG)
    assert r.budget_epoch == "2026-12" and r.created_at.startswith("2026-12-31")  # one clock
    with pytest.raises(LedgerDenied):  # December has only $5 left
        reserve_funded(repo, reservation_id="dec2", worst_case_usd=6.0, model="m",
                       lease_expires_at=dec31 + timedelta(seconds=420), now=dec31, config=CFG)
    jan1 = U("2027-01-01T00:00:30")
    obs = funded_observer(repo, config=CFG, now_fn=lambda: jan1)()
    assert (obs.budget_epoch, obs.spend) == ("2027-01", 0.0)
    assert obs.effective_cap == pytest.approx(4 * 50.0 / 31)  # allowance reset for January
    j = reserve_funded(repo, reservation_id="jan", worst_case_usd=6.0, model="m",
                       lease_expires_at=jan1 + timedelta(seconds=420), now=jan1, config=CFG)
    assert j.budget_epoch == "2027-01"
    spend = funded_spend(project(read_events(repo, ref=FUNDED_LEDGER_REF)).values(), now=jan1)
    assert spend == FundedSpend(0.0, 0.0, 6.0)  # December's open $45 hold is not January's


def test_settle_funded_charges_full_reservation_when_usage_is_missing(repo):
    _reserve(repo, "f1", 0.25, cap=1.0)
    assert settle_funded(repo, "f1", charged_usd=None, now=T0, config=CFG) == 0.25
    assert project(read_events(repo, ref=FUNDED_LEDGER_REF))["f1"].charged == 0.25


def test_settle_funded_records_the_usage_charge_and_first_writer_wins(repo):
    _reserve(repo, "f1", 0.25, cap=1.0)
    assert settle_funded(repo, "f1", charged_usd=0.0031, now=T0, config=CFG) == 0.0031
    assert settle_funded(repo, "f1", charged_usd=None, now=T0, config=CFG) == 0.0031  # recorded value


def test_settle_funded_unknown_reservation_fails(repo):
    from llmxive.model_selection.ledger_transport import LedgerError

    _reserve(repo, "f1", 0.25, cap=1.0)
    with pytest.raises(LedgerError, match="nope"):
        settle_funded(repo, "nope", charged_usd=None, now=T0, config=CFG)
