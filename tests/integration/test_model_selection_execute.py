"""Execution-adapter PAID path over the REAL strict-CAS credit ledger (spec 026,
slice 3, US3 / FR-011 / FR-016 / SC-004). Uses a real ``git init`` ledger repo
(local-only ``LedgerConfig(remote=None)``) + injected fresh-credit seams — no
mocks of the ledger or the reservation lifecycle (Constitution III): a paid call
reserves ``worst_case x retries`` up front, RETAINS the hold on return (success
OR failure), and fails closed (skip, never abort) when it cannot safely reserve.
"""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.backends.base import ChatMessage, ChatResponse, ModelDownError
from llmxive.model_selection.execute import ChainExhausted, execute
from llmxive.model_selection.ledger_transport import LedgerConfig, read_events
from llmxive.model_selection.reservations import (
    STATE_SETTLING,
    CreditObservation,
    project,
)
from llmxive.model_selection.types import (
    CallBudget,
    Candidate,
    ExecutionOptions,
    ModelChain,
    ModelPricing,
    ModelRef,
    SnapshotProvenance,
)

NOW = datetime(2026, 7, 16, 12, 0, 0, tzinfo=UTC)
EPOCH = "2026-07-17T03:45:00Z"
EP = "https://chat.dartmouth.edu"
CLAUDE = "anthropic.claude-haiku-4-5-20251001"
MSG = [ChatMessage(role="user", content="review this")]
LOCAL_CFG = LedgerConfig(remote=None)


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    _git(["init", "-b", "main", str(r)], tmp_path)
    return r


@pytest.fixture(autouse=True)
def _reset_credit_cache():
    from llmxive.backends.credits import reset_balance_cache

    reset_balance_cache()
    yield
    reset_balance_cache()


def _paid_ref(model_id: str = CLAUDE) -> ModelRef:
    return ModelRef("dartmouth", EP, model_id, "claude-haiku-4-5", "anthropic")


def _paid_chain(*, model_id: str = CLAUDE, worst_case: float = 2.5, credit_source: str = "live") -> ModelChain:
    cand = Candidate(_paid_ref(model_id), ModelPricing(1e-6, 5e-6), worst_case, 500.0)
    return ModelChain(
        candidates=(cand,),
        resolved_at=NOW,
        call_budget=CallBudget(100_000, 4096),
        snapshot_digest="D",
        snapshot_provenance={
            "catalog": SnapshotProvenance("live", NOW, 0.0),
            "credit": SnapshotProvenance(credit_source, NOW, 0.0),
        },
        selection_policy_version=1,
    )


def _observer(spend: float = 100.0, cap: float = 1500.0, epoch: str = EPOCH):
    return lambda: CreditObservation(spend=spend, effective_cap=cap, budget_epoch=epoch)


def _balance(spend: float = 100.0, max_budget: float = 2000.0):
    from llmxive.backends.credits import CreditBalance

    return lambda: CreditBalance(
        account="P", spend=spend, max_budget=max_budget, budget_duration="1d", budget_reset_at=EPOCH
    )


class _PaidBackend:
    """Fake backend for the paid candidate: ``behavior`` is ``"ok"`` (respond) or
    an ``Exception`` to raise. Records calls."""

    def __init__(self, behavior: object = "ok"):
        self.behavior = behavior
        self.calls: list[str] = []

    def chat(self, messages, *, model=None, max_tokens=None, temperature=None, deadline_s=None):
        self.calls.append(model)
        if isinstance(self.behavior, BaseException):
            raise self.behavior
        return ChatResponse(text=f"paid:{model}", model=model or "m", backend="fake")


def _exec(chain, repo, backend, *, retries=3, opt_in=True, monkeypatch, balance=None, observer=None):
    if opt_in:
        monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    else:
        monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False)
    return execute(
        chain, MSG,
        options=ExecutionOptions(max_tokens=512, deadline_s=30.0),
        backend_factory=lambda name: backend,
        retries=retries,
        ledger_repo=repo,
        ledger_config=LOCAL_CFG,
        credit_observer=observer or _observer(),
        balance_fetch=balance or _balance(),
        now=NOW,
        call_id="testcall01",
    )


# --------------------------------------------------------------------------- #


def test_paid_reserve_call_and_retain_hold(repo, monkeypatch):
    be = _PaidBackend("ok")
    res = _exec(_paid_chain(), repo, be, monkeypatch=monkeypatch)
    assert res.response.text == f"paid:{CLAUDE}"
    assert be.calls == [CLAUDE]
    # Retry envelope (#4): reserve worst_case (2.5) x retries (3) = 7.5.
    assert res.reserved_credits == pytest.approx(7.5)
    # The hold is RETAINED after return (settling), NEVER released at call-return.
    reservations = project(read_events(repo))
    assert len(reservations) == 1
    (r,) = reservations.values()
    assert r.state == STATE_SETTLING
    assert r.worst_case_credits == pytest.approx(7.5)


def test_reservation_id_is_sanitized(repo, monkeypatch):
    # A model id carrying ':' MUST be sanitized to the ledger charset (C9) — an
    # un-sanitized id would make append_event fail closed, so a clean reserve proves it.
    import re

    be = _PaidBackend("ok")
    res = _exec(_paid_chain(model_id="qwen.qwen3-vl:32b"), repo, be, monkeypatch=monkeypatch)
    assert res.reserved_credits > 0
    (rid,) = project(read_events(repo)).keys()
    assert re.fullmatch(r"[A-Za-z0-9._-]+", rid), rid
    assert ":" not in rid and "/" not in rid


def test_retries_one_sizes_reservation_to_single_call(repo, monkeypatch):
    be = _PaidBackend("ok")
    res = _exec(_paid_chain(worst_case=4.0), repo, be, retries=1, monkeypatch=monkeypatch)
    assert res.reserved_credits == pytest.approx(4.0)  # worst_case x 1


def test_failed_paid_call_retains_hold(repo, monkeypatch):
    # FR-016 no-leak: a paid call that FAILED after reaching the provider keeps its
    # worst-case hold (settling), NOT released — the sweeper reconciles it later.
    be = _PaidBackend(ModelDownError("provider hung"))
    with pytest.raises(ChainExhausted):
        _exec(_paid_chain(), repo, be, retries=1, monkeypatch=monkeypatch)
    (r,) = project(read_events(repo)).values()
    assert r.state == STATE_SETTLING  # hold RETAINED despite the failure
    assert r.worst_case_credits == pytest.approx(2.5)  # worst_case(2.5) x retries(1)


def test_paid_skipped_when_opt_in_off_no_reservation(repo, monkeypatch):
    be = _PaidBackend("ok")
    with pytest.raises(ChainExhausted) as ei:
        _exec(_paid_chain(), repo, be, opt_in=False, monkeypatch=monkeypatch)
    assert "skipped" in str(ei.value)
    assert be.calls == []  # never called
    assert read_events(repo) == []  # no reservation created (skipped before reserve)


def test_paid_skipped_when_headroom_insufficient(repo, monkeypatch):
    # Fresh spend near the cap → the twice-checked guard refuses BEFORE reserving.
    be = _PaidBackend("ok")
    with pytest.raises(ChainExhausted):
        _exec(
            _paid_chain(), repo, be, monkeypatch=monkeypatch,
            balance=_balance(spend=1499.0), observer=_observer(spend=1499.0),
        )
    assert be.calls == []
    assert read_events(repo) == []  # denied at the guard → nothing reserved


def test_paid_skipped_on_non_live_credit_snapshot(repo, monkeypatch):
    be = _PaidBackend("ok")
    with pytest.raises(ChainExhausted) as ei:
        _exec(_paid_chain(credit_source="last_known_good"), repo, be, monkeypatch=monkeypatch)
    assert "C6" in str(ei.value)
    assert be.calls == []
    assert read_events(repo) == []


def test_free_then_paid_reaches_paid_after_free_fails(repo, monkeypatch):
    # A free candidate that fails transiently advances to the paid candidate, which
    # reserves + runs. Proves the paid machinery engages only when reached.
    free = Candidate(
        ModelRef("dartmouth", EP, "qwen.qwen3.5-122b", "qwen3.5", "qwen"),
        ModelPricing(0.0, 0.0), 0.0, 0.0,
    )
    paid = _paid_chain().candidates[0]
    chain = ModelChain(
        candidates=(free, paid),
        resolved_at=NOW,
        call_budget=CallBudget(100_000, 4096),
        snapshot_digest="D",
        snapshot_provenance={
            "catalog": SnapshotProvenance("live", NOW, 0.0),
            "credit": SnapshotProvenance("live", NOW, 0.0),
        },
        selection_policy_version=1,
    )

    class _DispatchBackend:
        def __init__(self):
            self.calls = []

        def chat(self, messages, *, model=None, max_tokens=None, temperature=None, deadline_s=None):
            self.calls.append(model)
            if model == "qwen.qwen3.5-122b":
                raise ModelDownError("free model down")
            return ChatResponse(text=f"paid:{model}", model=model, backend="fake")

    be = _DispatchBackend()
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    res = execute(
        chain, MSG, options=ExecutionOptions(max_tokens=512, deadline_s=30.0),
        backend_factory=lambda name: be, retries=1,
        ledger_repo=repo, ledger_config=LOCAL_CFG,
        credit_observer=_observer(), balance_fetch=_balance(), now=NOW, call_id="c2",
    )
    assert res.model_ref.model_id == CLAUDE
    assert be.calls == ["qwen.qwen3.5-122b", CLAUDE]
    assert res.reserved_credits == pytest.approx(2.5)  # x retries(1)
    (r,) = project(read_events(repo)).values()
    assert r.state == STATE_SETTLING
