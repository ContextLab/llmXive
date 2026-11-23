"""Funded (Hugging Face) execution over the REAL funded git ledger (spec 027 5.6 / 5.9.2 / 5.9.6).

A funded candidate is reserved (worst case x 1) on ``refs/llmxive/funded-ledger`` before
it is sent, dispatched exactly once, and reconciled with its real charge afterwards:
``usage`` x the catalog price, zero for a definitive pre-inference rejection (HTTP
401/402/403, or a request never sent), and the full reservation for anything else.
The ledger is a real ``git init`` repo; the backend is the ``backend_factory`` seam
FR-015 sanctions (scripted per model, counting calls).
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from llmxive.backends.base import (
    ChatMessage,
    ChatResponse,
    PermanentBackendError,
    TransientBackendError,
)
from llmxive.backends.hf_budget import FundedUnavailable
from llmxive.backends.huggingface import HFCredentialRejected, HFPaymentRequired
from llmxive.model_selection.attempt_hooks import RouteAuditError
from llmxive.model_selection.execute import ChainExhausted, execute
from llmxive.model_selection.ledger_transport import FUNDED_LEDGER_REF, LedgerConfig, read_events
from llmxive.model_selection.reservations import STATE_OPEN, CreditObservation, project
from llmxive.model_selection.route import route_chat
from llmxive.model_selection.types import ExecutionOptions, SnapshotProvenance
from tests.helpers.funded import NOW, B, E, policy_with, sel, snapshot
from tests.unit.test_model_selection_attempt_hooks import _FailingRecorder

CFG = LedgerConfig(remote=None, ref=FUNDED_LEDGER_REF)
MSG = [ChatMessage("user", "hi")]
B_COST = 1200 * 1e-7 + 300 * 4e-7       # usage x B's catalog rates
E_COST = 1200 * 2e-7 + 300 * 8e-7       # usage x E's catalog rates


def OBS(cap: float = 1.0):
    return lambda: CreditObservation(spend=0.0, effective_cap=cap, budget_epoch="2026-11")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    subprocess.run(["git", "init", "-b", "main", str(r)], capture_output=True, text=True, check=True)
    return r


class _HF:
    """Scripted per model; counts calls."""

    def __init__(self, script):
        self.script, self.calls = script, []

    def chat(self, messages, *, model=None, max_tokens=None, temperature=None, deadline_s=None):
        self.calls.append(model)
        r = self.script.get(model, "ok")
        if callable(r) and not isinstance(r, (BaseException, ChatResponse)):
            r = r()
        if isinstance(r, BaseException):
            raise r
        return r if isinstance(r, ChatResponse) else ChatResponse(
            "ok", model, "huggingface", input_tokens=1200, output_tokens=300
        )


class _Local(_HF):
    def chat(self, messages, **kw):
        self.calls.append(kw["model"])
        return ChatResponse("local", kw["model"], "local")


def _run(repo, be, chain, **kw):
    return execute(chain, MSG, options=ExecutionOptions(max_tokens=512), backend_factory=lambda name: be,
                   ledger_repo=repo, funded_ledger_config=CFG, funded_observer=kw.pop("obs", OBS()), now=NOW, **kw)


def events(repo):
    return read_events(repo, ref=FUNDED_LEDGER_REF)


def charged(repo):
    return {e["reservation_id"]: e["charged"] for e in events(repo) if e["type"] == "reconciled"}


def test_funded_reserve_call_settle_records_real_cost(repo):
    res = _run(repo, _HF({}), sel("cheap_structured", snapshot(local=False)))       # leader B
    opened = next(e for e in events(repo) if e["type"] == "open")
    done = next(e for e in events(repo) if e["type"] == "reconciled")
    assert opened["model"] == B and opened["worst_case_credits"] == pytest.approx(0.0018)
    assert opened["budget_epoch"] == "2026-11"
    assert done["charged"] == pytest.approx(B_COST)
    assert res.charged_usd == done["charged"] == res.response.cost_estimate_usd
    assert read_events(repo) == []                                                   # Dartmouth credit ledger untouched


def test_funded_dispatches_once_and_reserves_times_one(repo):                       # Review Focus 4
    be = _HF({B: TransientBackendError("503"), E: TransientBackendError("503")})
    with pytest.raises(ChainExhausted):
        _run(repo, be, sel("cheap_structured", snapshot(local=False)), retries=3)
    assert be.calls == [B, E]                                                        # one attempt each despite retries=3
    assert [e["worst_case_credits"] for e in events(repo) if e["type"] == "open"] == [
        pytest.approx(0.0018), pytest.approx(0.0036)
    ]


def test_missing_usage_charges_full_reservation(repo):                              # Review Focus 4
    _run(repo, _HF({B: ChatResponse("ok", B, "huggingface")}), sel("cheap_structured", snapshot(local=False)))
    assert list(charged(repo).values()) == [pytest.approx(0.0018)]


def test_partial_usage_charges_full_reservation(repo):
    res = _run(repo, _HF({B: ChatResponse("ok", B, "huggingface", input_tokens=1200)}),
               sel("cheap_structured", snapshot(local=False)))
    assert list(charged(repo).values()) == [pytest.approx(0.0018)] and res.charged_usd == pytest.approx(0.0018)


def test_usage_above_the_reservation_is_capped_and_the_discrepancy_recorded(repo, caplog):
    huge = ChatResponse("ok", B, "huggingface", input_tokens=1_000_000, output_tokens=1_000_000)
    res = _run(repo, _HF({B: huge}), sel("cheap_structured", snapshot(local=False)))
    assert list(charged(repo).values()) == [pytest.approx(0.0018)]
    assert res.charged_usd == pytest.approx(0.0018) == res.response.cost_estimate_usd
    assert any("exceeds its reservation" in n for n in res.notes)
    assert "exceeds its reservation" in caplog.text


def test_failed_call_is_charged_its_reservation_and_chain_advances(repo):
    res = _run(repo, _HF({B: TransientBackendError("503")}), sel("cheap_structured", snapshot(local=False)))
    assert res.model_ref.model_id == E
    assert sorted(charged(repo).values()) == [pytest.approx(E_COST), pytest.approx(0.0018)]


@pytest.mark.parametrize("exc", [
    HFPaymentRequired("402"),
    HFCredentialRejected("401", http_status=401),
    HFCredentialRejected("403", http_status=403),
    HFCredentialRejected("no bill-to", http_status=None),
])
def test_pre_inference_rejection_charges_zero(repo, exc):                           # spec 5.9.2 amended — Review Focus 4
    res = _run(repo, _HF({B: exc}), sel("cheap_structured", snapshot(local=False)))
    assert res.model_ref.model_id == E                                               # 402 advances, 401/403 skip — the chain goes on
    assert sorted(charged(repo).values()) == [0.0, pytest.approx(E_COST)]


def test_failure_before_any_request_is_sent_charges_zero(repo):
    def factory(name):
        raise PermanentBackendError("backend could not be built")

    with pytest.raises(PermanentBackendError):
        execute(sel("cheap_structured", snapshot(local=False)), MSG, options=ExecutionOptions(max_tokens=512),
                backend_factory=factory, ledger_repo=repo, funded_ledger_config=CFG, funded_observer=OBS(), now=NOW)
    assert list(charged(repo).values()) == [0.0]


def test_aborting_failure_after_send_charges_full_and_reraises(repo):
    be = _HF({B: PermanentBackendError("400 bad request")})
    with pytest.raises(PermanentBackendError):
        _run(repo, be, sel("cheap_structured", snapshot(local=False)))
    assert be.calls == [B] and list(charged(repo).values()) == [pytest.approx(0.0018)]


def test_denied_reservation_skips_to_the_next_class_without_a_call(repo):
    hf, local = _HF({}), _Local({})
    res = execute(sel("cheap_structured", snapshot()), MSG, options=ExecutionOptions(max_tokens=512), ledger_repo=repo,
                  backend_factory=lambda n: local if n == "local" else hf, funded_ledger_config=CFG,
                  funded_observer=OBS(cap=0.0), now=NOW)
    assert hf.calls == [] and res.model_ref.backend == "local" and events(repo) == []
    assert res.charged_usd is None


@pytest.mark.parametrize("boom", [RuntimeError("observer exploded"), FundedUnavailable("guard gone"), ValueError("bad")])
def test_unreserved_funded_dispatch_is_impossible_when_reserve_raises(repo, boom):
    """Security ruling: a reserve that RAISES for any reason (not just a denial) skips
    the funded candidate — nothing is sent, and no hold is left open."""
    def exploding():
        raise boom

    hf, local = _HF({}), _Local({})
    res = execute(sel("cheap_structured", snapshot()), MSG, options=ExecutionOptions(max_tokens=512), ledger_repo=repo,
                  backend_factory=lambda n: local if n == "local" else hf, funded_ledger_config=CFG,
                  funded_observer=exploding, now=NOW)
    assert hf.calls == [] and res.model_ref.backend == "local"
    assert not [r for r in project(events(repo)).values() if r.state == STATE_OPEN]


def test_unreserved_funded_dispatch_is_impossible_without_a_ledger(repo):
    hf, local = _HF({}), _Local({})
    res = execute(sel("cheap_structured", snapshot()), MSG, options=ExecutionOptions(max_tokens=512), ledger_repo=None,
                  backend_factory=lambda n: local if n == "local" else hf, funded_ledger_config=CFG,
                  funded_observer=OBS(), now=NOW)
    assert hf.calls == [] and res.model_ref.backend == "local"


def test_guard_path_refuses_a_guard_from_another_month(repo):
    """Without an injected observer the reservation goes through ``reserve_funded`` and
    the snapshot's guard; a guard priced in another epoch is refused → skip, no call."""
    snap = snapshot()
    hf, local = _HF({}), _Local({})
    res = execute(sel("cheap_structured", snap), MSG, options=ExecutionOptions(max_tokens=512), ledger_repo=repo,
                  backend_factory=lambda n: local if n == "local" else hf, funded_ledger_config=CFG,
                  funded_guard=snap.funded, now=NOW + timedelta(days=10))           # December
    assert hf.calls == [] and res.model_ref.backend == "local" and events(repo) == []


def test_funded_skipped_when_guard_was_not_live_at_selection(repo):
    chain = sel("cheap_structured", snapshot(local=False))
    stale = replace(chain, snapshot_provenance={**chain.snapshot_provenance,
                                                "funded": SnapshotProvenance("unavailable", NOW, 0.0)})
    be = _HF({})
    with pytest.raises(ChainExhausted):
        _run(repo, be, stale)
    assert be.calls == []


def test_unconfigured_production_ledger_fails_closed(repo, monkeypatch):
    monkeypatch.delenv("LLMXIVE_FUNDED_LEDGER_ANCHOR", raising=False)
    be = _HF({})
    with pytest.raises(ChainExhausted):
        execute(sel("cheap_structured", snapshot(local=False)), MSG, options=ExecutionOptions(max_tokens=512),
                backend_factory=lambda n: be, ledger_repo=repo, now=NOW)
    assert be.calls == []


def test_audit_failure_after_dispatch_still_settles_the_real_cost(repo):
    with pytest.raises(RouteAuditError):
        _run(repo, _HF({}), sel("cheap_structured", snapshot(local=False)),
             route_audit=_FailingRecorder({"DispatchCompleted"}))
    assert list(charged(repo).values()) == [pytest.approx(B_COST)]


def test_audit_failure_before_dispatch_releases_the_hold_at_zero(repo):
    be = _HF({})
    with pytest.raises(RouteAuditError):
        _run(repo, be, sel("cheap_structured", snapshot(local=False)),
             route_audit=_FailingRecorder({"DispatchStarted"}))
    assert be.calls == [] and list(charged(repo).values()) == [0.0]


def test_settle_failure_keeps_the_reply_and_is_visible(repo, tmp_path, caplog):
    """The ledger becomes unreachable during the call: the reply still returns, the
    failure is logged and noted, and the hold stays open for the ledger's own sweep."""
    git_dir, parked = repo / ".git", tmp_path / "parked-git"

    def break_ledger():
        shutil.move(str(git_dir), str(parked))
        return "ok"

    res = _run(repo, _HF({B: break_ledger}), sel("cheap_structured", snapshot(local=False)))
    shutil.move(str(parked), str(git_dir))
    assert res.response.text == "ok" and res.model_ref.model_id == B
    assert res.charged_usd == pytest.approx(B_COST)
    assert any("settle" in n and "failed" in n for n in res.notes)
    assert "settle_funded" in caplog.text
    assert [r.state for r in project(events(repo)).values()] == [STATE_OPEN]


def test_route_chat_serves_funded_through_the_policy_seam(repo):
    be = _HF({})
    r = route_chat(MSG, profile="deep_review", max_tokens=512, snapshot=snapshot(local=False),
                   backend_factory=lambda n: be, ledger_repo=repo, funded_ledger_config=CFG,
                   funded_policy=policy_with(max_chain_slots=1))
    assert r.backend == "huggingface" and r.model == E and r.cost_estimate_usd > 0 and be.calls == [E]
