"""Funded (Hugging Face) execution over the REAL funded git ledger (spec 027 5.6 / 5.9.2 / 5.9.6).

A funded candidate is reserved (worst case x 1) on ``refs/llmxive/funded-ledger`` before
it is sent, dispatched exactly once, and reconciled with its real charge afterwards:
``usage`` x the catalog price, zero for a definitive pre-inference rejection (HTTP
401/402/403, or a request never sent), and the full reservation for anything else.
The ledger is a real ``git init`` repo; the backend is the ``backend_factory`` seam
FR-015 sanctions (scripted per model, counting calls).
"""

from __future__ import annotations

import importlib
import shutil
import subprocess
import time
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from llmxive.backends.base import (
    ChatMessage,
    ChatResponse,
    PermanentBackendError,
    TransientBackendError,
)
from llmxive.backends.hf_budget import FundedUnavailable
from llmxive.backends.huggingface import HFCredentialRejected, HFPaymentRequired, HuggingFaceBackend
from llmxive.model_selection.attempt_hooks import (
    ReservationOpened,
    RouteAuditError,
    RouteReplayError,
)
from llmxive.model_selection.execute import ChainExhausted, _release_unsent_hold_if_created, execute
from llmxive.model_selection.ledger_transport import FUNDED_LEDGER_REF, LedgerConfig, read_events
from llmxive.model_selection.reservations import STATE_OPEN, CreditObservation, project, reserve
from llmxive.model_selection.route import route_chat
from llmxive.model_selection.types import ExecutionOptions, SnapshotProvenance
from llmxive.self_improvement.audit_sink import EventStoreRouteAudit
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log
from tests.helpers.audit_sinks import ClaimOnceRecorder, FailingRecorder
from tests.helpers.funded import NOW, B, E, policy_with, sel, snapshot
from tests.helpers.replay_server import ReplayServer

# The modules themselves (the package re-exports a function named ``execute``).
execute_mod = importlib.import_module("llmxive.model_selection.execute")
reservations_mod = importlib.import_module("llmxive.model_selection.reservations")

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
             route_audit=FailingRecorder({"DispatchCompleted"}))
    assert list(charged(repo).values()) == [pytest.approx(B_COST)]


def test_audit_failure_before_dispatch_releases_the_hold_at_zero(repo):
    be = _HF({})
    with pytest.raises(RouteAuditError):
        _run(repo, be, sel("cheap_structured", snapshot(local=False)),
             route_audit=FailingRecorder({"DispatchStarted"}))
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


class _FrozenWallClock(datetime):
    """A ``datetime`` whose wall clock reads :data:`WALL` — the clock every module on
    the funded path would read if a ``now`` were not threaded through."""

    @classmethod
    def now(cls, tz=None):
        return WALL if tz is None else WALL.astimezone(tz)


WALL = datetime(2027, 3, 15, 9, tzinfo=UTC)      # another month AND another year than NOW


@pytest.mark.parametrize("wall_clock", ["real", "2027-03"])
def test_route_chat_serves_funded_through_the_policy_seam(repo, monkeypatch, wall_clock):
    """``route_chat(now=)`` prices and stamps the hold on the snapshot's clock, so the
    result does not depend on the wall clock: the same call passes with the wall clock
    read as 2027-03 by every module on the path (execute, the reservation ledger)."""
    if wall_clock != "real":
        monkeypatch.setattr(execute_mod, "datetime", _FrozenWallClock)
        monkeypatch.setattr(reservations_mod, "_utcnow", lambda: WALL)
    be = _HF({})
    r = route_chat(MSG, profile="deep_review", max_tokens=512, snapshot=snapshot(local=False),
                   backend_factory=lambda n: be, ledger_repo=repo, funded_ledger_config=CFG,
                   funded_policy=policy_with(max_chain_slots=1), now=NOW)
    assert r.backend == "huggingface" and r.model == E and r.cost_estimate_usd > 0 and be.calls == [E]
    opened = next(e for e in events(repo) if e["type"] == "open")
    assert opened["created_at"] == NOW.isoformat() and opened["budget_epoch"] == "2026-11"


# --- a request provably never sent is charged zero; one that may have left is charged in full ---

def _chat_ok(model):
    return {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1200, "completion_tokens": 300}, "model": model}


def _hf(srv):  # placeholder credentials for a loopback server, not real secrets
    return HuggingFaceBackend(token="hf_test_token", bill_to="test-group", base_url=srv.base_url)


def test_breaker_open_is_charged_zero_and_sends_nothing(repo):
    def route(req):
        return (503, {"error": "down"}) if req["json"]["model"] == B else (200, _chat_ok(req["json"]["model"]))

    with ReplayServer({("POST", "/chat/completions"): route}) as srv:
        be = _hf(srv)
        for _ in range(3):                                   # trip B's breaker (3 consecutive 503s)
            with pytest.raises(TransientBackendError):
                be.chat(MSG, model=B)
        sent_to_b = sum(1 for r in srv.requests if r["json"]["model"] == B)
        res = _run(repo, be, sel("cheap_structured", snapshot(local=False)))
        assert sum(1 for r in srv.requests if r["json"]["model"] == B) == sent_to_b == 3   # no new request
    assert res.model_ref.model_id == E
    assert sorted(charged(repo).values()) == [0.0, pytest.approx(E_COST)]


def test_timeout_after_send_is_charged_the_full_reservation(repo):
    def route(req):
        if req["json"]["model"] == B:
            time.sleep(1.5)                                  # longer than the 0.5 s deadline
        return (200, _chat_ok(req["json"]["model"]))

    with ReplayServer({("POST", "/chat/completions"): route}) as srv:
        res = execute(sel("cheap_structured", snapshot(local=False)), MSG,
                      options=ExecutionOptions(max_tokens=512, deadline_s=0.5), backend_factory=lambda n: _hf(srv),
                      ledger_repo=repo, funded_ledger_config=CFG, funded_observer=OBS(), now=NOW)
        assert srv.requests[0]["json"]["model"] == B           # the request did go out
    assert res.model_ref.model_id == E
    assert sorted(charged(repo).values()) == [pytest.approx(E_COST), pytest.approx(0.0018)]


def test_missing_credentials_are_charged_zero_and_send_nothing(repo):
    with ReplayServer({("POST", "/chat/completions"): lambda req: (200, _chat_ok(req["json"]["model"]))}) as srv:
        no_bill_to = HuggingFaceBackend(token="hf_test_token", bill_to="", base_url=srv.base_url)
        with pytest.raises(ChainExhausted):
            _run(repo, no_bill_to, sel("cheap_structured", snapshot(local=False)))
        assert srv.requests == []
    assert list(charged(repo).values()) == [0.0, 0.0]


# --- a hold this call did not create is never released or dispatched under by it ---

def _rid(model: str, call_id: str) -> str:
    return execute_mod._sanitize_reservation_id(model, call_id)


def test_audit_failure_never_zeroes_another_calls_in_flight_hold(repo):
    """Two calls share a call id. While the first is mid-dispatch, the second (audited)
    finds the SAME hold for B — another call's — so it skips B without touching it, then
    its audit sink fails on E: B's hold is unchanged, and the first call's real charge
    is what the ledger records for it."""
    seen: dict = {}

    def second_call():
        with pytest.raises(RouteAuditError):
            execute(sel("cheap_structured", snapshot(local=False)), MSG, options=ExecutionOptions(max_tokens=512),
                    backend_factory=lambda n: _HF({}), ledger_repo=repo, funded_ledger_config=CFG,
                    funded_observer=OBS(), now=NOW, call_id="shared",
                    route_audit=FailingRecorder({"DispatchStarted"}))
        hold = project(events(repo))[_rid(B, "shared")]
        seen["b"] = (hold.state, hold.charged)
        return "ok"

    res = _run(repo, _HF({B: second_call}), sel("cheap_structured", snapshot(local=False)), call_id="shared")
    assert seen["b"] == (STATE_OPEN, None)                                      # untouched by the second call
    assert charged(repo)[_rid(B, "shared")] == pytest.approx(B_COST) and res.charged_usd == pytest.approx(B_COST)


class _NestOnce:
    """A real backend that, the first time it is asked for ``model``, runs ``inner()``
    (a second, concurrent call) before sending its own request."""

    def __init__(self, real, model, inner):
        self.real, self.model, self.inner, self.done = real, model, inner, False

    def chat(self, messages, **kw):
        if kw.get("model") == self.model and not self.done:
            self.done = True
            self.inner()
        return self.real.chat(messages, **kw)


def _gated(repo, backend, *, route_id):
    return execute(sel("cheap_structured", snapshot(local=False)), MSG, options=ExecutionOptions(max_tokens=512),
                   backend_factory=lambda n: backend, ledger_repo=repo, funded_ledger_config=CFG,
                   funded_observer=OBS(), now=NOW, call_id="shared", route_id=route_id,
                   route_audit=FailingRecorder(set()))


def test_two_gated_calls_on_one_hold_send_once_and_settle_once(repo):
    """(i)+(iii) Same call id, different route ids, both behind a dispatch-claim gate
    (whose key is the route, not the hold): only the hold's creator reaches the provider
    for B, and B's hold is settled exactly once, at the creator's real cost."""
    def route(req):
        return (200, _chat_ok(req["json"]["model"]))

    with ReplayServer({("POST", "/chat/completions"): route}) as srv:
        inner: dict = {}
        first = _NestOnce(_hf(srv), B, lambda: inner.setdefault("res", _gated(repo, _hf(srv), route_id="route-2")))
        res = _gated(repo, first, route_id="route-1")
        assert [r["json"]["model"] for r in srv.requests].count(B) == 1
    assert res.model_ref.model_id == B and inner["res"].model_ref.model_id == E
    b_hold = _rid(B, "shared")
    assert sum(1 for e in events(repo) if e["type"] == "reconciled" and e["reservation_id"] == b_hold) == 1
    assert charged(repo)[b_hold] == pytest.approx(B_COST)


def test_second_call_raising_cannot_change_the_first_calls_hold(repo):
    """(ii) The second call (gated, another route) finds B's hold, skips it, then fails on
    its own E candidate and raises: B's hold is untouched while the first call is
    mid-dispatch, and afterwards carries the first call's real cost."""
    def route(req):
        return (503, {"error": "down"}) if req["json"]["model"] == E else (200, _chat_ok(req["json"]["model"]))

    with ReplayServer({("POST", "/chat/completions"): route}) as srv:
        seen: dict = {}

        def second():
            with pytest.raises(ChainExhausted):
                _gated(repo, _hf(srv), route_id="route-2")
            hold = project(events(repo))[_rid(B, "shared")]
            seen["b"] = (hold.state, hold.charged)

        res = _gated(repo, _NestOnce(_hf(srv), B, second), route_id="route-1")
        assert [r["json"]["model"] for r in srv.requests].count(B) == 1
    assert seen["b"] == (STATE_OPEN, None)
    assert res.model_ref.model_id == B and charged(repo)[_rid(B, "shared")] == pytest.approx(B_COST)


def test_ungated_call_never_dispatches_under_another_calls_hold(repo):
    inner: dict = {}

    def second_call():
        hf = _HF({})
        inner["res"] = _run(repo, hf, sel("cheap_structured", snapshot(local=False)), call_id="shared")
        inner["calls"] = hf.calls
        return "ok"

    _run(repo, _HF({B: second_call}), sel("cheap_structured", snapshot(local=False)), call_id="shared")
    assert inner["calls"] == [E] and inner["res"].model_ref.model_id == E     # B's hold is the first call's
    assert any("already exists for another call" in n for n in inner["res"].notes)
    assert sorted(charged(repo).values()) == [pytest.approx(B_COST), pytest.approx(E_COST)]


def test_unsent_hold_is_released_only_by_the_call_that_created_it(repo):
    """The decision behind both the audit-abort release and a reserve that raised after
    its open event landed: ownership comes from the hold's own ``owner`` token."""
    reserve(repo, reservation_id="h1", worst_case_credits=0.0018, model=B, credit_observer=OBS(),
            lease_expires_at=NOW + timedelta(minutes=7), now=NOW, config=CFG, owner="call-1")
    notes: list[str] = []
    _release_unsent_hold_if_created(repo, "h1", owner="call-2", now=NOW, config=CFG, notes=notes)
    assert project(events(repo))["h1"].state == STATE_OPEN
    _release_unsent_hold_if_created(repo, "h1", owner="call-1", now=NOW, config=CFG, notes=notes)
    assert charged(repo) == {"h1": 0.0}


def test_reservation_opened_states_both_units(repo):
    sink = FailingRecorder(set())
    res = _run(repo, _HF({}), sel("cheap_structured", snapshot(local=False)), route_audit=sink)
    opened = next(e for e in sink.events if isinstance(e, ReservationOpened))
    assert opened.reserved_usd == pytest.approx(0.0018) and opened.reserved_credits == pytest.approx(1.8)
    assert res.reserved_usd == pytest.approx(0.0018) and res.reserved_credits == pytest.approx(1.8)


# --- replay on the audited path (fix round 3) ---

@pytest.fixture
def lane_repo(repo):
    """The same real git repo, also carrying the spec-025 lane log the real sink writes."""
    for args in (["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", *args], cwd=str(repo), check=True, capture_output=True, text=True)
    bootstrap_lane_log(repo, config=LaneLogConfig())
    return repo


def _sink(repo):
    return EventStoreRouteAudit(repo=repo, problem_id="P1", attempt_id="A1", actor="exec",
                                clock=lambda: "2026-11-23T12:00:00+00:00")


def test_replayed_route_raises_replay_and_tries_no_later_candidate(lane_repo):
    """(i) Same audited route replayed after a completed funded dispatch: the replay finds
    the original's hold, sees the dispatch already claimed, and raises RouteReplayError —
    no request reaches the provider, the local model after it is never called, and the
    original settlement is unchanged."""
    local = _Local({})
    with ReplayServer({("POST", "/chat/completions"): lambda req: (200, _chat_ok(req["json"]["model"]))}) as srv:
        def run():
            return execute(sel("cheap_structured", snapshot()), MSG, options=ExecutionOptions(max_tokens=512),
                           backend_factory=lambda n: local if n == "local" else _hf(srv), ledger_repo=lane_repo,
                           funded_ledger_config=CFG, funded_observer=OBS(), now=NOW, route_id="route-R",
                           route_audit=_sink(lane_repo))

        first = run()
        assert first.model_ref.model_id == B and len(srv.requests) == 1
        before = list(events(lane_repo))
        with pytest.raises(RouteReplayError):
            run()
        assert len(srv.requests) == 1                                           # nothing sent on the replay
    assert local.calls == []                                                    # no fall-through
    assert events(lane_repo) == before                                          # ledger untouched
    assert list(charged(lane_repo).values()) == [pytest.approx(B_COST)]


def test_replay_meeting_its_own_fresh_hold_releases_it_at_zero(repo):
    """(ii) Audited, explicit call ids, the same route id twice: the second call opens
    its OWN hold, the sink reports the dispatch boundary already claimed, and the hold it
    created is settled at zero before RouteReplayError — none is left open."""
    sink, hf = ClaimOnceRecorder(), _HF({})
    _run(repo, hf, sel("cheap_structured", snapshot(local=False)), route_audit=sink, route_id="R",
         call_id="c1")
    with pytest.raises(RouteReplayError):
        _run(repo, hf, sel("cheap_structured", snapshot(local=False)), route_audit=sink, route_id="R",
             call_id="c2")
    assert hf.calls == [B]
    assert charged(repo) == {_rid(B, "c1"): pytest.approx(B_COST), _rid(B, "c2"): 0.0}
    assert not [r for r in project(events(repo)).values() if r.state == STATE_OPEN]


def test_different_audited_call_meeting_a_hold_just_skips(repo):
    """(iii) A different route (same call id) meets the first call's completed hold: the
    dispatch is not claimed for ITS route, so the funded candidate is skipped and the
    chain goes on; the first hold is unchanged."""
    sink = ClaimOnceRecorder()
    _run(repo, _HF({}), sel("cheap_structured", snapshot(local=False)), route_audit=sink, route_id="R1",
         call_id="shared")
    before = charged(repo)
    hf = _HF({})
    res = _run(repo, hf, sel("cheap_structured", snapshot(local=False)), route_audit=sink, route_id="R2",
               call_id="shared")
    assert hf.calls == [E] and res.model_ref.model_id == E
    assert charged(repo)[_rid(B, "shared")] == before[_rid(B, "shared")] == pytest.approx(B_COST)


class _NoLookupSink:
    """A real sink that cannot answer ``dispatch_claimed``."""

    def __init__(self):
        self.events: list = []

    def record(self, event) -> None:
        self.events.append(event)

    def claim_dispatch(self, event) -> bool:
        self.events.append(event)
        return True


def test_sink_that_cannot_tell_a_replay_fails_closed(repo):
    _run(repo, _HF({}), sel("cheap_structured", snapshot(local=False)), call_id="shared")
    hf = _HF({})
    with pytest.raises(RouteAuditError):
        _run(repo, hf, sel("cheap_structured", snapshot(local=False)), route_audit=_NoLookupSink(),
             call_id="shared")
    assert hf.calls == []
    assert list(charged(repo).values()) == [pytest.approx(B_COST)]


# --- fix round 4: one decision function, every (state) -> (action) row covered ---

_Hold, _Act, _funded_action = execute_mod._Hold, execute_mod._FundedAction, execute_mod._funded_action
_D, _S, _R = _Act.DISPATCH, _Act.SKIP, _Act.REPLAY

#: The whole table, literally: (audited, call id derived from the route, hold) ->
#: (action with no dispatch claim, action with the boundary already claimed). "Derived"
#: on the unaudited path is the fresh random id an unaudited call mints.
_DECISIONS = {
    (False, True, _Hold.ABSENT): (_S, _R),
    (False, True, _Hold.OWN): (_D, _R),
    (False, True, _Hold.OWN_RELEASED): (_S, _R),
    (False, True, _Hold.FOREIGN_LIVE): (_S, _R),
    (False, True, _Hold.FOREIGN_ENDED): (_S, _R),
    (False, True, _Hold.UNKNOWN): (_S, _R),
    (False, False, _Hold.ABSENT): (_S, _R),
    (False, False, _Hold.OWN): (_D, _R),
    (False, False, _Hold.OWN_RELEASED): (_S, _R),
    (False, False, _Hold.FOREIGN_LIVE): (_S, _R),
    (False, False, _Hold.FOREIGN_ENDED): (_S, _R),
    (False, False, _Hold.UNKNOWN): (_S, _R),
    (True, True, _Hold.ABSENT): (_S, _R),
    (True, True, _Hold.OWN): (_D, _R),
    (True, True, _Hold.OWN_RELEASED): (_S, _R),
    (True, True, _Hold.FOREIGN_LIVE): (_R, _R),      # ruling A: the original is between reserve and claim
    (True, True, _Hold.FOREIGN_ENDED): (_S, _R),
    (True, True, _Hold.UNKNOWN): (_S, _R),
    (True, False, _Hold.ABSENT): (_S, _R),
    (True, False, _Hold.OWN): (_D, _R),
    (True, False, _Hold.OWN_RELEASED): (_S, _R),
    (True, False, _Hold.FOREIGN_LIVE): (_S, _R),
    (True, False, _Hold.FOREIGN_ENDED): (_S, _R),
    (True, False, _Hold.UNKNOWN): (_S, _R),
}


def test_funded_decision_table():
    """Every combination has exactly one action, and it is the one the table states."""
    assert set(_DECISIONS) == {(a, d, h) for a in (False, True) for d in (False, True) for h in _Hold}
    for (audited, derived, hold), (unclaimed, claimed) in _DECISIONS.items():
        assert _funded_action(audited=audited, derived_id=derived, hold=hold, claimed=False) is unclaimed
        assert _funded_action(audited=audited, derived_id=derived, hold=hold, claimed=True) is claimed


def _derived(route_id: str) -> str:
    """The call id ``execute`` derives from a route id on the audited path."""
    import hashlib

    return hashlib.sha256(route_id.encode()).hexdigest()[:12]


def _lane(repo):
    from llmxive.self_improvement.lane_log import read

    return read(repo, "P1", config=LaneLogConfig())


def _outcomes(repo):
    return [(e.payload["candidate_index"], e.payload["outcome"]) for e in _lane(repo)
            if e.event_type == "CandidateOutcome"]


@pytest.fixture
def audit_repo(tmp_path):
    """A second real git repo holding ONLY the lane log, so the funded ledger's repo can
    become unreadable while the production audit sink keeps working."""
    r = tmp_path / "audit"
    subprocess.run(["git", "init", "-b", "main", str(r)], capture_output=True, text=True, check=True)
    for args in (["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", *args], cwd=str(r), check=True, capture_output=True, text=True)
    bootstrap_lane_log(r, config=LaneLogConfig())
    return r


def _audited(ledger, sink, hf, local, **kw):
    """One audited call over funded B, funded E, then a local model."""
    return execute(kw.pop("chain", None) or sel("cheap_structured", snapshot()), MSG,
                   options=ExecutionOptions(max_tokens=512),
                   backend_factory=lambda n: local if n == "local" else hf,
                   ledger_repo=kw.pop("ledger_repo", ledger), funded_ledger_config=CFG,
                   funded_observer=kw.pop("obs", OBS()), now=NOW, route_audit=sink,
                   route_id=kw.pop("route_id", "route-R"), **kw)


def _foreign(repo, rid, *, lease=timedelta(minutes=7)):
    """Another call's hold for B under ``rid``, really on the funded ledger."""
    return reserve(repo, reservation_id=rid, worst_case_credits=0.0018, model=B, credit_observer=OBS(),
                   lease_expires_at=NOW + lease, now=NOW, config=CFG, owner="the-original-call")


def _exploding():
    raise RuntimeError("hf_SECRET-in-an-exception-message")


class _ReplayBeforeClaim(EventStoreRouteAudit):
    """The production sink; the first time it is handed a ``ReservationOpened`` — after
    the original's reserve, before its dispatch claim — it first runs ``inner``."""

    def __init__(self, inner, **kw):
        super().__init__(**kw)
        self._inner, self._ran = inner, False

    def record(self, event) -> None:
        if isinstance(event, ReservationOpened) and not self._ran:
            self._ran = True
            self._inner()
        super().record(event)


# A. audited, derived call id, the original's hold open and its dispatch not yet claimed

def test_replay_in_the_gap_before_the_originals_claim_aborts_and_the_route_sends_once(lane_repo):
    """A same-route replay arrives between the original's reserve and its dispatch claim
    (real ledger, production sink): it raises RouteReplayError — no request, no later
    candidate, no skip record — and the original then dispatches once and settles once."""
    hf, local, seen = _HF({}), _Local({}), {}

    def replay():
        with pytest.raises(RouteReplayError) as err:
            _audited(lane_repo, _sink(lane_repo), hf, local)
        seen["msg"], seen["calls"], seen["outcomes"] = str(err.value), list(hf.calls + local.calls), _outcomes(lane_repo)

    original = _ReplayBeforeClaim(replay, repo=lane_repo, problem_id="P1", attempt_id="A1", actor="exec",
                                  clock=lambda: "2026-11-23T12:00:00+00:00")
    res = _audited(lane_repo, original, hf, local)
    assert seen["calls"] == [] and seen["outcomes"] == [] and "not yet claimed" in seen["msg"]
    assert res.model_ref.model_id == B and hf.calls == [B] and local.calls == []    # one route, one dispatch
    rid = _rid(B, _derived("route-R"))
    assert charged(lane_repo) == {rid: pytest.approx(B_COST)}
    assert sum(1 for e in events(lane_repo) if e["type"] == "reconciled") == 1
    assert _outcomes(lane_repo) == [(0, "success")]


def test_replay_meeting_the_originals_open_unclaimed_hold_touches_nothing(lane_repo):
    rid = _rid(B, _derived("route-R"))
    _foreign(lane_repo, rid)
    before, hf, local = list(events(lane_repo)), _HF({}), _Local({})
    with pytest.raises(RouteReplayError):
        _audited(lane_repo, _sink(lane_repo), hf, local)
    assert hf.calls == [] and local.calls == [] and events(lane_repo) == before and _outcomes(lane_repo) == []


@pytest.mark.parametrize("ended", ["lease-expired", "settling", "reconciled"])
def test_route_whose_original_crashed_before_claiming_recovers_once_the_hold_ended(lane_repo, ended):
    """The original reserved and died before its claim. Once its hold's lease expired,
    or the sweep settled / reconciled it, the same route skips that candidate and goes
    on; the dead call's hold is left exactly as it was."""
    rid = _rid(B, _derived("route-R"))
    _foreign(lane_repo, rid, lease=timedelta(seconds=-1) if ended == "lease-expired" else timedelta(minutes=7))
    if ended == "settling":
        reservations_mod.settle(lane_repo, rid, now=NOW, config=CFG)
    elif ended == "reconciled":
        reservations_mod.reconcile(lane_repo, rid, charged=0.0018, now=NOW, config=CFG)
    before = [e for e in events(lane_repo) if e["reservation_id"] == rid]
    hf, local = _HF({}), _Local({})
    res = _audited(lane_repo, _sink(lane_repo), hf, local)
    assert res.model_ref.model_id == E and hf.calls == [E]
    assert [e for e in events(lane_repo) if e["reservation_id"] == rid] == before
    assert _outcomes(lane_repo) == [(0, "skip"), (1, "success")]


@pytest.mark.parametrize("ended", [False, True])
def test_explicit_call_id_meeting_another_calls_unclaimed_hold_skips(lane_repo, ended):
    """An EXPLICIT call id says nothing about the route, so another call's hold with no
    claim for this route — open or ended — is only a candidate to skip (production sink)."""
    rid = _rid(B, "shared")
    _foreign(lane_repo, rid)
    if ended:
        reservations_mod.reconcile(lane_repo, rid, charged=0.0018, now=NOW, config=CFG)
    before = [e for e in events(lane_repo) if e["reservation_id"] == rid]
    hf, local = _HF({}), _Local({})
    res = _audited(lane_repo, _sink(lane_repo), hf, local, call_id="shared")
    assert res.model_ref.model_id == E and hf.calls == [E]
    assert [e for e in events(lane_repo) if e["reservation_id"] == rid] == before


def test_explicit_call_id_replay_of_a_claimed_route_raises_replay(lane_repo):
    hf, local = _HF({}), _Local({})
    _audited(lane_repo, _sink(lane_repo), hf, local, call_id="shared")
    before = list(events(lane_repo))
    with pytest.raises(RouteReplayError):
        _audited(lane_repo, _sink(lane_repo), hf, local, call_id="shared")
    assert hf.calls == [B] and local.calls == [] and events(lane_repo) == before


@pytest.mark.parametrize("call_id", [None, "explicit"])
def test_replay_while_the_original_is_mid_dispatch_raises_replay(lane_repo, call_id):
    """The original has claimed the boundary and is waiting on the provider (its hold is
    still open) when the same route is replayed: RouteReplayError, nothing more is sent,
    the open hold is untouched and ends at the original's real cost."""
    local, seen = _Local({}), {}

    def replay():
        inner = _HF({})
        with pytest.raises(RouteReplayError):
            _audited(lane_repo, _sink(lane_repo), inner, local, call_id=call_id)
        hold = project(events(lane_repo))[_rid(B, call_id or _derived("route-R"))]
        seen["calls"], seen["hold"] = inner.calls + local.calls, (hold.state, hold.charged)
        return "ok"

    hf = _HF({B: replay})
    res = _audited(lane_repo, _sink(lane_repo), hf, local, call_id=call_id)
    assert seen == {"calls": [], "hold": (STATE_OPEN, None)}
    assert res.model_ref.model_id == B and hf.calls == [B] and local.calls == []
    assert list(charged(lane_repo).values()) == [pytest.approx(B_COST)]
    assert _outcomes(lane_repo) == [(0, "success")]


# B. audited: a claimed boundary is a replay whatever stopped the reserve

@pytest.mark.parametrize("call_id", [None, "explicit"])
def test_replay_that_cannot_read_the_ledger_raises_replay(repo, audit_repo, tmp_path, call_id):
    """The replay's reserve raises and the ledger cannot be read (ownership unknown):
    the boundary is claimed, so it is a replay — not a skip to the local model."""
    hf, local = _HF({}), _Local({})
    _audited(repo, _sink(audit_repo), hf, local, call_id=call_id)
    before, parked = list(events(repo)), tmp_path / "parked-git"
    shutil.move(str(repo / ".git"), str(parked))
    try:
        with pytest.raises(RouteReplayError):
            _audited(repo, _sink(audit_repo), hf, local, call_id=call_id)
    finally:
        shutil.move(str(parked), str(repo / ".git"))
    assert hf.calls == [B] and local.calls == [] and events(repo) == before


@pytest.mark.parametrize("failure", ["denied", "observer-raises"])
@pytest.mark.parametrize("call_id", [None, "explicit"])
def test_replay_whose_hold_is_not_on_the_local_ref_raises_replay(lane_repo, failure, call_id):
    """The original's hold is not on the local funded ref and the replay's reserve fails
    (denied: nothing under the id; raising: ownership unknown). Claimed -> replay."""
    hf, local = _HF({}), _Local({})
    _audited(lane_repo, _sink(lane_repo), hf, local, call_id=call_id)
    subprocess.run(["git", "update-ref", "-d", FUNDED_LEDGER_REF], cwd=str(lane_repo), check=True)
    with pytest.raises(RouteReplayError):
        _audited(lane_repo, _sink(lane_repo), hf, local, call_id=call_id,
                 obs=OBS(cap=0.0) if failure == "denied" else _exploding)
    assert hf.calls == [B] and local.calls == []
    assert not [r for r in project(events(lane_repo)).values() if r.state == STATE_OPEN]


@pytest.mark.parametrize("precondition", ["guard-not-live", "no-ledger"])
def test_replay_that_fails_a_funded_precondition_raises_replay(lane_repo, precondition):
    hf, local = _HF({}), _Local({})
    _audited(lane_repo, _sink(lane_repo), hf, local)
    before, kw = list(events(lane_repo)), {}
    if precondition == "guard-not-live":
        chain = sel("cheap_structured", snapshot())
        kw["chain"] = replace(chain, snapshot_provenance={**chain.snapshot_provenance,
                                                          "funded": SnapshotProvenance("unavailable", NOW, 0.0)})
    with pytest.raises(RouteReplayError):
        if precondition == "no-ledger":
            execute(sel("cheap_structured", snapshot()), MSG, options=ExecutionOptions(max_tokens=512),
                    backend_factory=lambda n: local if n == "local" else hf, ledger_repo=None,
                    funded_ledger_config=CFG, funded_observer=OBS(), now=NOW, route_audit=_sink(lane_repo),
                    route_id="route-R")
        else:
            _audited(lane_repo, _sink(lane_repo), hf, local, **kw)
    assert hf.calls == [B] and local.calls == [] and events(lane_repo) == before


@pytest.mark.parametrize("failure", ["denied", "observer-raises", "ledger-unreadable"])
@pytest.mark.parametrize("call_id", [None, "explicit"])
def test_genuine_reserve_failure_with_no_claim_still_skips_to_the_next_candidate(
    repo, audit_repo, tmp_path, failure, call_id
):
    """Not a replay (nothing claimed): an exhausted allowance, a failing reserve or an
    unreachable ledger skips the funded candidates and the local model serves — on the
    audited path, with the production sink."""
    hf, local, parked = _HF({}), _Local({}), tmp_path / "parked-git"
    if failure == "ledger-unreadable":
        subprocess.run(["git", "update-ref", "-d", "HEAD"], cwd=str(repo), capture_output=True)
        shutil.move(str(repo / ".git"), str(parked))
    try:
        res = _audited(repo, _sink(audit_repo), hf, local, call_id=call_id,
                       obs={"denied": OBS(cap=0.0), "observer-raises": _exploding}.get(failure, OBS()))
    finally:
        if parked.exists():
            shutil.move(str(parked), str(repo / ".git"))
    assert res.model_ref.backend == "local" and hf.calls == []
    assert _outcomes(audit_repo) == [(0, "skip"), (1, "skip"), (2, "success")]
    assert not [r for r in project(events(repo)).values() if r.state == STATE_OPEN]


def test_sink_that_cannot_tell_a_replay_fails_closed_on_any_funded_skip(repo):
    """Without ``dispatch_claimed`` a skipped funded candidate cannot be told from a
    replay, so even a plain denial is route-fatal — nothing is sent anywhere."""
    hf, local = _HF({}), _Local({})
    with pytest.raises(RouteAuditError):
        _audited(repo, _NoLookupSink(), hf, local, obs=OBS(cap=0.0))
    assert hf.calls == [] and local.calls == [] and events(repo) == []


# C. audited: a hold this call created meets a boundary that is already claimed (production sink)

@pytest.mark.parametrize("call_id", [None, "explicit"])
def test_replay_with_its_own_fresh_hold_is_refused_by_the_production_claim(lane_repo, call_id):
    """The original's hold is gone from the funded ref, so the replay's reserve creates
    a hold of its own under the same id. The production ``claim_dispatch`` finds the
    byte-identical DispatchStarted: nothing is sent, the fresh hold is released at zero,
    RouteReplayError."""
    hf, local = _HF({}), _Local({})
    _audited(lane_repo, _sink(lane_repo), hf, local, call_id=call_id)
    subprocess.run(["git", "update-ref", "-d", FUNDED_LEDGER_REF], cwd=str(lane_repo), check=True)
    with pytest.raises(RouteReplayError):
        _audited(lane_repo, _sink(lane_repo), hf, local, call_id=call_id)
    assert hf.calls == [B] and local.calls == []
    assert charged(lane_repo) == {_rid(B, call_id or _derived("route-R")): 0.0}
    assert not [r for r in project(events(lane_repo)).values() if r.state == STATE_OPEN]


def test_same_route_under_a_different_explicit_call_id_is_an_audit_conflict_in_production(lane_repo):
    """Explicit call ids c1 then c2 on ONE route: the second call's hold is its own, but
    its ReservationOpened names another reservation id under the same audit event id.
    The production sink refuses that as a conflicting payload: RouteAuditError (not
    RouteReplayError) — route-fatal, nothing sent, no later candidate, and the second
    call's own hold released at zero."""
    hf, local = _HF({}), _Local({})
    _audited(lane_repo, _sink(lane_repo), hf, local, call_id="c1")
    with pytest.raises(RouteAuditError) as err:
        _audited(lane_repo, _sink(lane_repo), hf, local, call_id="c2")
    assert not isinstance(err.value, RouteReplayError)
    assert hf.calls == [B] and local.calls == []
    assert charged(lane_repo) == {_rid(B, "c1"): pytest.approx(B_COST), _rid(B, "c2"): 0.0}
    assert _outcomes(lane_repo) == [(0, "success")]


# Unaudited rows not covered above

def test_unaudited_explicit_call_id_meeting_an_ended_hold_skips(repo):
    _run(repo, _HF({}), sel("cheap_structured", snapshot(local=False)), call_id="shared")
    before, hf = list(events(repo)), _HF({})
    res = _run(repo, hf, sel("cheap_structured", snapshot(local=False)), call_id="shared")
    assert hf.calls == [E] and res.model_ref.model_id == E
    assert [e for e in events(repo) if e["reservation_id"] == _rid(B, "shared")] == \
        [e for e in before if e["reservation_id"] == _rid(B, "shared")]


@pytest.mark.parametrize("failure", ["denied", "ledger-unreadable"])
@pytest.mark.parametrize("call_id", [None, "explicit"])
def test_unaudited_reserve_failure_skips_to_the_next_candidate(repo, tmp_path, failure, call_id):
    hf, local, parked = _HF({}), _Local({}), tmp_path / "parked-git"
    if failure == "ledger-unreadable":
        shutil.move(str(repo / ".git"), str(parked))
    try:
        res = _audited(repo, None, hf, local, call_id=call_id, obs=OBS(cap=0.0) if failure == "denied" else OBS())
    finally:
        if parked.exists():
            shutil.move(str(parked), str(repo / ".git"))
    assert res.model_ref.backend == "local" and hf.calls == [] and events(repo) == []


# D. notes, audit reasons and errors carry an exception's TYPE, never its text

def test_skip_notes_and_audit_reasons_carry_exception_types_only(lane_repo):
    hf, local = _HF({}), _Local({})
    denied = _audited(lane_repo, _sink(lane_repo), hf, local, obs=OBS(cap=0.0), route_id="r-denied")
    raised = _audited(lane_repo, _sink(lane_repo), hf, local, obs=_exploding, route_id="r-raised")
    reasons = [e.payload["reason"] for e in _lane(lane_repo) if e.event_type == "CandidateOutcome"]
    text = "\n".join([*denied.notes, *raised.notes, *reasons])
    assert "reservation denied (LedgerDenied)" in text and "could not reserve (RuntimeError)" in text
    assert "SECRET" not in text and "exceeds cap" not in text and "fresh spend" not in text


def test_claim_failure_error_carries_the_exception_type_only(repo):
    with pytest.raises(RouteAuditError) as err:
        _run(repo, _HF({}), sel("cheap_structured", snapshot(local=False)),
             route_audit=FailingRecorder({"DispatchStarted"}))
    assert "RuntimeError" in str(err.value) and "simulated" not in str(err.value)


# --- a missing or rejected Dartmouth key skips to the next candidate (final review A5) ---

def test_missing_dartmouth_key_skips_to_the_funded_candidate(repo, monkeypatch, tmp_path):
    from llmxive.backends.router import make_backend
    from tests.helpers.funded import GLM

    monkeypatch.delenv("DARTMOUTH_CHAT_API_KEY", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "no-config"))  # no credentials file
    chain = sel("cheap_structured", snapshot(dartmouth=(GLM,), local=False))
    assert [c.model_ref.backend for c in chain.candidates][:2] == ["dartmouth", "huggingface"]
    with ReplayServer({("POST", "/chat/completions"): lambda req: (200, _chat_ok(req["json"]["model"]))}) as srv:
        hf = _hf(srv)
        res = execute(chain, MSG, options=ExecutionOptions(max_tokens=512),
                      backend_factory=lambda n: hf if n == "huggingface" else make_backend(n),
                      ledger_repo=repo, funded_ledger_config=CFG, funded_observer=OBS(), now=NOW)
        assert [r["json"]["model"] for r in srv.requests] == [B]
    assert res.model_ref.model_id == B and res.charged_usd == pytest.approx(B_COST)
    assert any("BackendCredentialError" in n for n in res.notes)


# --- an allowance denied at execute time does not fall through to paid (final review A7) ---

def _paid_after_funded_chain():
    from tests.helpers.funded import CLAUDE

    snap = snapshot(claude=True, paid_opt_in=True, local=False, prices={CLAUDE: (1e-8, 1e-8)})
    chain = sel("cheap_structured", snap, allow_paid=True)
    assert [c.cost_class for c in chain.candidates] == ["funded", "funded", "paid"]
    return chain, CLAUDE


def _paid_kwargs(monkeypatch):
    from llmxive.backends.credits import CreditBalance, reset_balance_cache

    reset_balance_cache()
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    return dict(
        ledger_config=LedgerConfig(remote=None),
        credit_observer=lambda: CreditObservation(spend=100.0, effective_cap=1500.0, budget_epoch="2026-11-24"),
        balance_fetch=lambda: CreditBalance(account="P", spend=100.0, max_budget=2000.0,
                                            budget_duration="1d", budget_reset_at="2026-11-24"),
    )


def test_allowance_denied_at_execute_time_skips_paid_too(repo, monkeypatch):
    chain, claude = _paid_after_funded_chain()
    hf, paid = _HF({}), _Local({})
    with pytest.raises(ChainExhausted) as ei:
        execute(chain, MSG, options=ExecutionOptions(max_tokens=512), ledger_repo=repo,
                backend_factory=lambda n: hf if n == "huggingface" else paid,
                funded_ledger_config=CFG, funded_observer=OBS(cap=0.0), now=NOW, **_paid_kwargs(monkeypatch))
    assert hf.calls == [] and paid.calls == []
    assert f"paid {claude!r} skipped" in str(ei.value) and "allowance" in str(ei.value)
    assert events(repo) == [] and read_events(repo) == []  # no funded hold, no paid hold


def test_paid_still_runs_when_funded_was_skipped_for_another_reason(repo, monkeypatch):
    # Control: a funded skip that is not an allowance denial (no funded ledger here)
    # leaves the paid candidate in play, so the A7 rule is keyed to the denial only.
    chain, claude = _paid_after_funded_chain()
    hf, paid = _HF({}), _Local({})
    res = execute(chain, MSG, options=ExecutionOptions(max_tokens=512), ledger_repo=repo,
                  backend_factory=lambda n: hf if n == "huggingface" else paid,
                  funded_ledger_config=CFG, funded_observer=None, now=NOW, **_paid_kwargs(monkeypatch))
    assert hf.calls == [] and paid.calls == [claude] and res.model_ref.model_id == claude


# --- a stalled git cannot hang the route (final review A8) ---

@pytest.fixture
def stalled_git(tmp_path, monkeypatch):
    """A real executable named ``git`` first on PATH that never answers."""
    import os

    import llmxive.git_event_log as gel

    bin_dir = tmp_path / "stalled-bin"
    bin_dir.mkdir()
    fake = bin_dir / "git"
    fake.write_text("#!/bin/sh\nexec sleep 30\n")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    assert gel.GIT_TIMEOUT_S == 60.0
    monkeypatch.setattr(gel, "GIT_TIMEOUT_S", 0.5)  # keep the test fast; the default is pinned above
    return gel


def test_a_stalled_ledger_read_times_out_as_a_ledger_error(repo, stalled_git):
    from llmxive.model_selection.ledger_transport import LedgerError

    started = time.monotonic()
    with pytest.raises(LedgerError, match="timed out"):
        read_events(repo, ref=FUNDED_LEDGER_REF)
    assert time.monotonic() - started < 10.0


def test_a_stalled_ledger_skips_the_funded_candidate_with_a_type_only_note(repo, stalled_git):
    hf, local = _HF({}), _Local({})
    started = time.monotonic()
    res = execute(sel("cheap_structured", snapshot()), MSG, options=ExecutionOptions(max_tokens=512),
                  ledger_repo=repo, backend_factory=lambda n: local if n == "local" else hf,
                  funded_ledger_config=CFG, funded_observer=OBS(), now=NOW)
    assert time.monotonic() - started < 20.0
    assert hf.calls == [] and res.model_ref.backend == "local"
    funded_notes = [n for n in res.notes if "funded" in n]
    assert funded_notes and all("timed out" not in n for n in funded_notes)  # TYPE only, never text
    assert any("LedgerError" in n for n in funded_notes)
