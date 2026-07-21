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


def test_reserve_ledger_error_skips_not_aborts(repo, monkeypatch):
    # Finding-2: a reserve() LedgerError AFTER the pre-check passes — sustained CAS
    # contention (LedgerContention) or an unreachable/unauthorized ledger
    # (LedgerAuthError) — makes the paid candidate ineligible at call time →
    # skip-candidate (advance), NEVER an abort (FR-010). The REAL reserve() is
    # covered by 19 ledger integration tests; here we FAULT-INJECT the rare
    # distributed failure to assert execute's DISPOSITION of it (the same
    # fault-injection seam the ScriptedBackend exception tests use).
    import importlib
    execmod = importlib.import_module("llmxive.model_selection.execute")
    from llmxive.model_selection.ledger_transport import LedgerContention

    def _contend(*_a, **_k):
        raise LedgerContention("could not fast-forward after 8 attempts (sustained contention)")

    monkeypatch.setattr(execmod, "reserve", _contend)
    be = _PaidBackend("ok")
    with pytest.raises(ChainExhausted) as ei:
        _exec(_paid_chain(), repo, be, monkeypatch=monkeypatch)
    assert "could not reserve" in str(ei.value) and "LedgerContention" in str(ei.value)
    assert be.calls == []  # skipped before the call, not aborted mid-call


def test_reserve_unexpected_error_surfaces(repo, monkeypatch):
    # The reserve() catch is NARROW (LedgerError only): an unexpected programmer /
    # data-validation error is NOT a transport failure and must SURFACE, never be
    # swallowed as a silent skip.
    import importlib
    execmod = importlib.import_module("llmxive.model_selection.execute")

    def _bug(*_a, **_k):
        raise ValueError("programmer bug: reservation invariant violated")

    monkeypatch.setattr(execmod, "reserve", _bug)
    be = _PaidBackend("ok")
    with pytest.raises(ValueError, match="programmer bug"):
        _exec(_paid_chain(), repo, be, monkeypatch=monkeypatch)


# --------------------------------------------------------------------------- #
# Finding-3 (round 2): execute() resolves the PRODUCTION ledger config by default.
# The default (ledger_config omitted) must NEVER silently open a LOCAL-only paid
# reservation — a missing/unreachable production config fails closed (skip).
# --------------------------------------------------------------------------- #


def _exec_production(repo, backend, monkeypatch, *, call_id="cprod"):
    """execute() with a ledger_repo but NO explicit ledger_config → production
    resolution (the path a forgetful caller would hit)."""
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    return execute(
        _paid_chain(), MSG,
        options=ExecutionOptions(max_tokens=512, deadline_s=30.0),
        backend_factory=lambda name: backend,
        retries=1,
        ledger_repo=repo,  # NOTE: ledger_config OMITTED → production default
        credit_observer=_observer(), balance_fetch=_balance(), now=NOW, call_id=call_id,
    )


def test_missing_production_config_fails_closed_not_local(repo, monkeypatch):
    from llmxive.model_selection.ledger_transport import LEDGER_ANCHOR_ENV, LEDGER_REMOTE_ENV

    monkeypatch.delenv(LEDGER_ANCHOR_ENV, raising=False)  # anchor NOT pinned
    monkeypatch.delenv(LEDGER_REMOTE_ENV, raising=False)
    be = _PaidBackend("ok")
    with pytest.raises(ChainExhausted) as ei:
        _exec_production(repo, be, monkeypatch)
    assert "production ledger not configured" in str(ei.value)
    assert be.calls == []           # never called
    assert read_events(repo) == []  # NOT silently reserved on a local ledger


def test_production_config_unreachable_remote_fails_closed(repo, monkeypatch):
    # Anchor pinned but the configured remote does not hold the ledger → fail closed
    # (skip), never a local reservation.
    from llmxive.model_selection.ledger_transport import LEDGER_ANCHOR_ENV, LEDGER_REMOTE_ENV

    monkeypatch.setenv(LEDGER_ANCHOR_ENV, "deadbeefdeadbeef")
    monkeypatch.setenv(LEDGER_REMOTE_ENV, "no-such-remote")
    be = _PaidBackend("ok")
    with pytest.raises(ChainExhausted):
        _exec_production(repo, be, monkeypatch)
    assert be.calls == []
    assert read_events(repo) == []


def test_explicit_local_config_is_the_opt_in_for_paid(repo, monkeypatch):
    # The opt-in local/test mode: an EXPLICIT LedgerConfig(remote=None) reserves
    # locally even with no anchor env — how tests + single-runner mode work.
    from llmxive.model_selection.ledger_transport import LEDGER_ANCHOR_ENV

    monkeypatch.delenv(LEDGER_ANCHOR_ENV, raising=False)
    be = _PaidBackend("ok")
    res = _exec(_paid_chain(), repo, be, monkeypatch=monkeypatch)  # _exec passes LOCAL_CFG
    assert res.response.text == f"paid:{CLAUDE}"
    assert res.reserved_credits > 0


# --------------------------------------------------------------------------- #
# Review findings 1+2+3: the WHOLE routing chokepoint (route_chat → select →
# execute) reaches the guarded paid tail over the real git ledger.
# --------------------------------------------------------------------------- #

QWEN = "qwen.qwen3.5-122b"
GEMMA4 = "google.gemma-4-31B-it"
GPT_OSS = "openai.gpt-oss-120b"
LOCAL = "Qwen/Qwen2.5-3B-Instruct"


def _composite_paid_snapshot():
    """The REAL composite: 3 free Dartmouth + 1 free local + the paid claude tail,
    all live + opted-in with ample headroom (so select keeps claude last)."""
    from llmxive.model_selection.types import CreditGuardSnapshot, RuntimeSnapshot

    def ref(mid, backend, endpoint, family, vendor):
        return ModelRef(backend, endpoint, mid, family, vendor)

    models = (
        ref(QWEN, "dartmouth", EP, "qwen3.5", "qwen"),
        ref(GEMMA4, "dartmouth", EP, "gemma-4", "google"),
        ref(GPT_OSS, "dartmouth", EP, "gpt-oss", "openai"),
        ref(LOCAL, "local", "local", "qwen2.5", "qwen"),
        _paid_ref(),
    )
    pricing = {m.model_id: ModelPricing(0.0, 0.0) for m in models[:-1]}
    pricing[CLAUDE] = ModelPricing(1e-6, 5e-6)
    credit = CreditGuardSnapshot(
        balance=1000.0, spend=100.0, max_budget=2000.0, paid_opt_in=True,
        budget_fraction=0.75, effective_cap=1500.0, available_headroom=1400.0,
        budget_reset_at=EPOCH, observed_at=NOW, source="live",
    )
    live = SnapshotProvenance("live", NOW, 0.0)
    return RuntimeSnapshot(
        models=models, pricing=pricing, health={m.model_id: "ok" for m in models},
        credit=credit, observed_at=NOW,
        sources={"catalog": live, "local": live, "credit": live}, digest="COMPOSITE",
    )


class _FreeDownServesPaid:
    """Dartmouth backend: every FREE model is down (transient → advance); the paid
    claude answers. Records every model tried."""

    name = "dartmouth"

    def __init__(self):
        self.calls: list[str] = []

    def chat(self, messages, *, model=None, max_tokens=None, temperature=None, deadline_s=None):
        self.calls.append(model)
        if model == CLAUDE:
            return ChatResponse(text=f"paid:{model}", model=model, backend="dartmouth")
        raise ModelDownError(f"free model {model!r} is down")


class _UnavailableLocal:
    """Local runtime not configured (review finding 3) → advance, don't abort."""

    name = "local"

    def __init__(self):
        self.calls: list[str] = []

    def chat(self, messages, *, model=None, max_tokens=None, temperature=None, deadline_s=None):
        from llmxive.backends.base import BackendUnavailable

        self.calls.append(model)
        raise BackendUnavailable("transformers not installed; local runtime unavailable")


def test_route_chat_reaches_paid_after_free_down_and_local_unavailable(repo, monkeypatch):
    # Findings 1+2+3 together: route_chat with the composite paid snapshot walks
    # dartmouth-free (all down) → local (unavailable, ADVANCES) → claude PAID, which
    # opens an authoritative reservation on the real git ledger and moves it to
    # settling. Proves the wrappers' paid fallback is now functional end-to-end.
    from llmxive.backends import credits as credits_mod
    from llmxive.model_selection.route import route_chat

    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    monkeypatch.setattr(credits_mod, "fetch_credit_balance", _balance())  # ample live credit

    dart = _FreeDownServesPaid()
    local_be = _UnavailableLocal()
    resp = route_chat(
        MSG, profile="standard_generation", caller_model=QWEN, max_tokens=512,
        snapshot=_composite_paid_snapshot(),
        backend_factory=lambda name: local_be if name == "local" else dart,
        ledger_repo=repo, ledger_config=LOCAL_CFG,
    )

    # Reached the guarded paid tail (finding 2: claude was NOT truncated).
    assert resp.model == CLAUDE
    # Local was tried (finding 3: it advanced rather than aborting the chain).
    assert local_be.calls == [LOCAL]
    # The dartmouth free chain was walked before claude answered (finding 2 order).
    assert dart.calls[0] in {QWEN, GEMMA4, GPT_OSS} and dart.calls[-1] == CLAUDE
    # An authoritative reservation was opened and RETAINED as settling (findings 1+FR-016).
    reservations = project(read_events(repo))
    assert reservations, "no reservation was opened — paid path never reserved"
    (res,) = list(reservations.values())
    assert res.model == CLAUDE
    assert res.state == STATE_SETTLING


# --------------------------------------------------------------------------- #
# Task 3 (spec 025 slice-0): reservation_authority threaded through execute
# (FR-033b) — the Attempt-budget gate consulted BEFORE the 026 daily reserve.
# --------------------------------------------------------------------------- #

from tests.unit.test_model_selection_attempt_hooks import _Budget  # the real in-memory authority


def _ok_factory():
    class _OK:
        def chat(self, messages, *, model=None, max_tokens=None, temperature=None, deadline_s=None):
            return ChatResponse(text=f"ok:{model}", model=model or "m", backend="scripted")
    return lambda name: _OK()


def test_reservation_authority_denial_skips_paid_candidate(repo, monkeypatch):
    # NOTE: every paid-path test in this file sets LLMXIVE_PAID_OPT_IN (directly or
    # via _exec) — without it, paid_call_allowed refuses before ever reaching the
    # authority, which would exercise the wrong code path.
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    budget = _Budget(0.0)  # cap 0 → every Attempt reserve is refused
    with pytest.raises(ChainExhausted):  # the only candidate was skipped
        execute(_paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
                backend_factory=_ok_factory(), ledger_repo=repo, ledger_config=LOCAL_CFG,
                credit_observer=_observer(), balance_fetch=_balance(),
                reservation_authority=budget)
    assert budget.open == {}          # released/never-held: nothing reserved
    assert budget.retained == set()   # never dispatched


def test_reservation_authority_admits_within_budget(repo, monkeypatch):
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    budget = _Budget(10_000.0)  # ample
    result = execute(_paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
                     backend_factory=_ok_factory(), ledger_repo=repo, ledger_config=LOCAL_CFG,
                     credit_observer=_observer(), balance_fetch=_balance(),
                     reservation_authority=budget)
    assert result.reservation_id is not None
    assert result.reservation_id in budget.retained  # dispatched → retained (not released)


def test_reservation_authority_none_is_behavior_preserving(repo, monkeypatch):
    # No authority → identical to today's paid path (026 reserve only).
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    result = execute(_paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
                     backend_factory=_ok_factory(), ledger_repo=repo, ledger_config=LOCAL_CFG,
                     credit_observer=_observer(), balance_fetch=_balance())
    assert result.reservation_id is not None


def test_reservation_authority_released_when_026_reserve_fails(repo, monkeypatch):
    # FR-033b step ii rollback: the Attempt reserve opens (budget has ample
    # headroom), then the 026 daily reserve() raises LedgerError (fault-injected,
    # same seam as test_reserve_ledger_error_skips_not_aborts above) → the ALREADY
    # OPEN Attempt reservation must be released (open -> released), never left
    # open and never retained — the candidate is skipped, not aborted.
    import importlib
    execmod = importlib.import_module("llmxive.model_selection.execute")
    from llmxive.model_selection.ledger_transport import LedgerContention

    def _contend(*_a, **_k):
        raise LedgerContention("could not fast-forward after 8 attempts (sustained contention)")

    monkeypatch.setattr(execmod, "reserve", _contend)
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    budget = _Budget(10_000.0)  # ample — the Attempt reserve itself succeeds
    with pytest.raises(ChainExhausted) as ei:
        execute(_paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
                backend_factory=_ok_factory(), ledger_repo=repo, ledger_config=LOCAL_CFG,
                credit_observer=_observer(), balance_fetch=_balance(),
                reservation_authority=budget)
    assert "could not reserve" in str(ei.value) and "LedgerContention" in str(ei.value)
    assert budget.open == {}            # released, not left open
    assert len(budget.released) == 1    # the Attempt reserve WAS opened, then released
    assert budget.retained == set()     # never dispatched


def test_reservation_authority_released_on_non_ledger_error_from_026_reserve(repo, monkeypatch):
    # Review finding 1 (regression): the 026 reserve() can raise a NON-LedgerError
    # (e.g. a ValueError for a negative amount — deliberately surfaced uncaught, see
    # test_reserve_unexpected_error_surfaces above). When an Attempt authority is
    # engaged, that exception must NOT leak the Attempt reservation: release() must
    # still run (then the ValueError re-raises) — same rollback as the LedgerError
    # branch, just for a different exception type.
    import importlib
    execmod = importlib.import_module("llmxive.model_selection.execute")

    def _bug(*_a, **_k):
        raise ValueError("programmer bug: reservation invariant violated")

    monkeypatch.setattr(execmod, "reserve", _bug)
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    budget = _Budget(10_000.0)  # ample — the Attempt reserve itself succeeds
    call_id = "cbug1"
    rid = execmod._sanitize_reservation_id(CLAUDE, call_id)
    with pytest.raises(ValueError, match="programmer bug"):
        execute(_paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
                backend_factory=_ok_factory(), ledger_repo=repo, ledger_config=LOCAL_CFG,
                credit_observer=_observer(), balance_fetch=_balance(),
                reservation_authority=budget, call_id=call_id)
    assert budget.open == {}       # released, NOT leaked (the bug this test guards against)
    assert rid in budget.released  # the Attempt reserve WAS opened, then released
    assert budget.retained == set()  # never dispatched


# --------------------------------------------------------------------------- #
# Task 4 (spec 025 slice-0): route_audit outbox — the PAID post-dispatch
# fail-closed-with-reservation-retained case (needs the real ledger fixture;
# the FREE-path outbox/route-fatal/none-preserving cases are in
# tests/unit/test_model_selection_execute.py).
# --------------------------------------------------------------------------- #

from tests.unit.test_model_selection_attempt_hooks import _FailingRecorder


def test_route_audit_postdispatch_failure_fails_closed_retained(repo, monkeypatch):
    from llmxive.model_selection.attempt_hooks import RouteAuditError

    # Without this, paid_call_allowed refuses before ever reaching dispatch,
    # and the test would pass for the wrong reason (the Task 3 lesson).
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    budget = _Budget(10_000.0)
    rec = _FailingRecorder(fail_on={"DispatchCompleted"})
    with pytest.raises(RouteAuditError):
        execute(_paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
                backend_factory=_ok_factory(), ledger_repo=repo, ledger_config=LOCAL_CFG,
                credit_observer=_observer(), balance_fetch=_balance(),
                reservation_authority=budget, route_audit=rec)
    # Backend ran; audit failed post-dispatch → fail closed, reservation RETAINED (not released).
    assert budget.retained


def test_route_audit_predispatch_failure_paid_releases_reservation(repo, monkeypatch):
    """FR-033a route-fatal branch, PAID candidate: the Attempt reservation has
    ALREADY opened when a PRE-dispatch audit event (ReservationOpened /
    DispatchStarted) fails. The route-fatal handler must release() the Attempt
    reservation AND settle() the 026 hold, then re-raise — WITHOUT ever
    dispatching to the backend. Guards execute.py:376-384."""
    from llmxive.model_selection.attempt_hooks import RouteAuditError

    import importlib
    execmod = importlib.import_module("llmxive.model_selection.execute")

    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")  # else the candidate is skipped pre-dispatch
    budget = _Budget(10_000.0)
    rec = _FailingRecorder(fail_on={"DispatchStarted"})
    call_id = "cpre1"
    rid = execmod._sanitize_reservation_id(CLAUDE, call_id)

    class _MustNotDispatch:
        def chat(self, messages, *, model=None, max_tokens=None, temperature=None, deadline_s=None):
            raise AssertionError("dispatched despite pre-dispatch audit failure")

    with pytest.raises(RouteAuditError):
        execute(_paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
                backend_factory=lambda name: _MustNotDispatch(), ledger_repo=repo, ledger_config=LOCAL_CFG,
                credit_observer=_observer(), balance_fetch=_balance(),
                reservation_authority=budget, route_audit=rec, call_id=call_id)
    # Pre-dispatch failure → the Attempt reservation is RELEASED, not stuck open
    # and not retained (retained is reserved for post-dispatch fail-closed).
    assert budget.open == {}
    assert rid in budget.released
    assert budget.retained == set()
