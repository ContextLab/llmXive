"""Execution-adapter PAID path over the REAL strict-CAS credit ledger (spec 026,
slice 3, US3 / FR-011 / FR-016 / SC-004). Uses a real ``git init`` ledger repo
(local-only ``LedgerConfig(remote=None)``) + injected fresh-credit seams — no
mocks of the ledger or the reservation lifecycle (Constitution III): a paid call
reserves ``worst_case x retries`` up front, RETAINS the hold on return (success
OR failure), and fails closed (skip, never abort) when it cannot safely reserve.
"""

from __future__ import annotations

import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.backends.base import ChatMessage, ChatResponse, ModelDownError
from llmxive.model_selection.attempt_hooks import DispatchStarted, RouteReplayError
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
from tests.helpers.audit_sinks import FailingRecorder
from tests.unit.test_model_selection_attempt_hooks import (
    _Budget,
    _ClaimingRecorder,
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
# _Budget is the real in-memory ReservationAuthority (imported at module top).


def _ok_factory():
    class _OK:
        def chat(self, messages, *, model=None, max_tokens=None, temperature=None, deadline_s=None):
            return ChatResponse(text=f"ok:{model}", model=model or "m", backend="scripted")
    return lambda name: _OK()


class _CallCounter:
    """A REAL, thread-safe call counter (no mock) — proves a replayed route_id
    does NOT re-invoke the backend (spec-025 maintainer review fix #5): the
    dispatch-claim crux is the backend-call COUNT, not merely event shape or
    reservation count."""

    def __init__(self):
        self._lock = threading.Lock()
        self.count = 0

    def increment(self) -> None:
        with self._lock:
            self.count += 1


class _CountingBackend:
    """A REAL backend whose ``.chat()`` increments a SHARED ``_CallCounter``."""

    def __init__(self, counter: _CallCounter):
        self._counter = counter

    def chat(self, messages, *, model=None, max_tokens=None, temperature=None, deadline_s=None):
        self._counter.increment()
        return ChatResponse(text=f"ok:{model}", model=model or "m", backend="counting")


def _counting_factory(counter: _CallCounter):
    return lambda name: _CountingBackend(counter)


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


def test_default_call_id_produces_12_hex_char_reservation_suffix(repo, monkeypatch):
    # Maintainer review finding #3: call_id must default INDEPENDENTLY of
    # route_id (both omitted here), preserving the PRIOR reservation-id suffix
    # format (`uuid.uuid4().hex[:12]` = 12 hex chars) — a regression widened it
    # to the 32-char route_id by seeding call_id from route_id.
    import re

    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    result = execute(_paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
                     backend_factory=_ok_factory(), ledger_repo=repo, ledger_config=LOCAL_CFG,
                     credit_observer=_observer(), balance_fetch=_balance())
    assert result.reservation_id is not None
    prefix = f"{CLAUDE}-"  # CLAUDE's id contains only chars _sanitize_reservation_id allows verbatim
    assert result.reservation_id.startswith(prefix), result.reservation_id
    suffix = result.reservation_id[len(prefix):]
    assert re.fullmatch(r"[0-9a-f]{12}", suffix), suffix


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
# FailingRecorder is the real in-memory failing sink (imported at module top).


def test_route_audit_postdispatch_failure_fails_closed_retained(repo, monkeypatch):
    from llmxive.model_selection.attempt_hooks import RouteAuditError

    # Without this, paid_call_allowed refuses before ever reaching dispatch,
    # and the test would pass for the wrong reason (the Task 3 lesson).
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    budget = _Budget(10_000.0)
    rec = FailingRecorder(fail_on={"DispatchCompleted"})
    with pytest.raises(RouteAuditError):
        execute(_paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
                backend_factory=_ok_factory(), ledger_repo=repo, ledger_config=LOCAL_CFG,
                credit_observer=_observer(), balance_fetch=_balance(),
                reservation_authority=budget, route_audit=rec)
    # Backend ran; audit failed post-dispatch → fail closed, reservation RETAINED (not released).
    assert budget.retained


class _RaisingRetainedBudget(_Budget):
    """A REAL in-memory ReservationAuthority (subclass of the real ``_Budget``)
    whose ``mark_retained`` raises — used to prove the money-path guard (Finding
    #3): a lane authority whose ``mark_retained`` blows up must NEVER discard an
    already-charged, already-returned successful response."""

    def mark_retained(self, reservation_id: str) -> None:
        raise RuntimeError("simulated mark_retained failure (e.g. lane DB down)")


def test_mark_retained_failure_does_not_discard_successful_response(repo, monkeypatch):
    # Finding #3: on the SUCCESS path, execute()'s `finally` calls settle() (already
    # best-effort guarded) THEN reservation_authority.mark_retained() — both run
    # AFTER the ExecutionResult is built. A raising mark_retained must be guarded
    # the same way settle() is: log and continue, never propagate and discard the
    # already-returned response. Non-vacuity: WITHOUT the guard this raises
    # RuntimeError instead of returning (see the companion assertion below).
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    budget = _RaisingRetainedBudget(10_000.0)
    result = execute(
        _paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
        backend_factory=_ok_factory(), ledger_repo=repo, ledger_config=LOCAL_CFG,
        credit_observer=_observer(), balance_fetch=_balance(),
        reservation_authority=budget,
    )
    # The successful, already-charged response is NOT discarded despite the
    # raising mark_retained.
    assert result.response.text == f"ok:{CLAUDE}"
    assert result.reservation_id is not None
    # mark_retained raised before it could record anything — proves the guard
    # actually caught a REAL raise (non-vacuous), not a no-op subclass.
    assert budget.retained == set()
    # The 026 ledger hold is still retained (settle() ran fine; unaffected by the
    # authority-side failure).
    (r,) = project(read_events(repo)).values()
    assert r.state == STATE_SETTLING


def test_route_audit_predispatch_failure_paid_releases_reservation(repo, monkeypatch):
    """FR-033a route-fatal branch, PAID candidate: the Attempt reservation has
    ALREADY opened when a PRE-dispatch audit event (ReservationOpened /
    DispatchStarted) fails. The route-fatal handler must release() the Attempt
    reservation AND settle() the 026 hold, then re-raise — WITHOUT ever
    dispatching to the backend. Guards execute.py:376-384."""
    import importlib

    from llmxive.model_selection.attempt_hooks import RouteAuditError

    execmod = importlib.import_module("llmxive.model_selection.execute")

    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")  # else the candidate is skipped pre-dispatch
    budget = _Budget(10_000.0)
    rec = FailingRecorder(fail_on={"DispatchStarted"})
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


class _ReleaseRaisingBudget(_Budget):
    """A REAL in-memory ReservationAuthority (subclass of the real ``_Budget``)
    whose ``release`` raises — used to prove the F3 independent-cleanup guard
    (execute.py's pre-dispatch ``except RouteAuditError:`` block): a failing
    ``release()`` must NOT suppress ``settle()``, and the primary
    ``RouteAuditError`` must still be what surfaces (not the release exception)."""

    def release(self, reservation_id: str) -> None:
        raise RuntimeError("simulated release failure (e.g. lane DB down)")


def test_route_audit_predispatch_failure_release_error_does_not_suppress_settle(repo, monkeypatch):
    """F3: when a PRE-dispatch audit event fails AND reservation_authority.release()
    itself raises, execute() must NOT let the release exception surface (masking the
    real RouteAuditError), and must NOT skip settle() just because release() blew up
    — release() and settle() each run in their OWN try/except, so one failing does
    not suppress the other, and the original RouteAuditError stays primary.
    Non-vacuity: WITHOUT the independent try/except, the raising release() would
    propagate INSTEAD of RouteAuditError — this test fails (a RuntimeError leaks
    past ``pytest.raises(RouteAuditError)``) against that unfixed code."""
    from llmxive.model_selection.attempt_hooks import RouteAuditError

    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")  # else the candidate is skipped pre-dispatch
    budget = _ReleaseRaisingBudget(10_000.0)
    rec = FailingRecorder(fail_on={"DispatchStarted"})

    class _MustNotDispatch:
        def chat(self, messages, *, model=None, max_tokens=None, temperature=None, deadline_s=None):
            raise AssertionError("dispatched despite pre-dispatch audit failure")

    with pytest.raises(RouteAuditError):
        execute(_paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
                backend_factory=lambda name: _MustNotDispatch(), ledger_repo=repo, ledger_config=LOCAL_CFG,
                credit_observer=_observer(), balance_fetch=_balance(),
                reservation_authority=budget, route_audit=rec)
    # settle() still ran DESPITE the raising release() — the 026 hold reached
    # settling, proving release()'s failure did not suppress settle().
    (r,) = project(read_events(repo)).values()
    assert r.state == STATE_SETTLING


# --------------------------------------------------------------------------- #
# Slice-0 audit fix #1 (HIGH, maintainer review): a retry-stable route_id must
# produce a retry-stable paid reservation_id. ``call_id`` now derives
# deterministically from ``route_id`` (a truncated SHA-256, execute.py:~333)
# instead of a fresh random token, so retrying the SAME logical route (same
# injected route_id) reuses the SAME reservation_id — the 026 ledger's
# reserve() is already idempotent on a matching (model, worst_case, epoch)
# identity under one reservation_id (reservations.py:239-255), so the retry's
# reserve() is a no-op rather than a second reservation (a double charge risk).
# --------------------------------------------------------------------------- #


def test_paid_replay_same_route_id_reuses_reservation_not_a_second_one(repo, monkeypatch):
    # Slice-0 audit fix #1 (retry-stable call_id) + fix #5 (atomic dispatch
    # claim): replaying execute() for the SAME route_id must (a) reuse the SAME
    # 026 reservation (fix #1) AND (b) NOT re-invoke the backend a second time
    # (fix #5 — round 4 only made the audit EVENTS idempotent, never the
    # backend-dispatch SIDE EFFECT). A SHARED _ClaimingRecorder + shared backend
    # counter across both execute() calls is what makes the replay detectable;
    # the second call now raises RouteReplayError instead of returning a second
    # ExecutionResult.
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    budget = _Budget(10_000.0)
    rec = _ClaimingRecorder()
    counter = _CallCounter()
    fixed_route_id = "retry-route-fixed"

    def _run():
        return execute(
            _paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
            backend_factory=_counting_factory(counter), ledger_repo=repo, ledger_config=LOCAL_CFG,
            credit_observer=_observer(), balance_fetch=_balance(), now=NOW,
            reservation_authority=budget, route_audit=rec, route_id=fixed_route_id,
        )

    result1 = _run()
    with pytest.raises(RouteReplayError):
        _run()

    # The crux of fix #5: the backend was invoked exactly ONCE across both
    # execute() calls — the replay did NOT re-dispatch. (On the pre-fix code —
    # an unconditional emit_audit(DispatchStarted) + dispatch, no claim gate —
    # this would be 2; see the report for the RED-code demonstration.)
    assert counter.count == 1

    # The 026 ledger holds exactly ONE reservation for that id — the second
    # reserve() call was an idempotent no-op, NOT a second (double-charge) hold.
    reservations = project(read_events(repo))
    matching = [rid for rid in reservations if rid == result1.reservation_id]
    assert len(matching) == 1
    assert reservations[result1.reservation_id].state == STATE_SETTLING

    # The reservation is RETAINED (never released) — the ORIGINAL dispatch
    # legitimately owns it; the replay path only ever retains, never releases.
    assert result1.reservation_id in budget.retained

    # Non-vacuity for fix #1 (required by the audit): under the OLD call_id
    # derivation (`call_id = call_id or uuid.uuid4().hex[:12]`, a FRESH random
    # token per call, ignoring route_id), the reservation_id below would NOT
    # match a hash derived from `fixed_route_id`. Demonstrate directly that the
    # deterministic derivation is what makes the SAME route_id always derive the
    # SAME call_id/reservation_id, while a DIFFERENT route_id derives a
    # DIFFERENT one.
    import hashlib

    from llmxive.model_selection.execute import _sanitize_reservation_id

    same_call_id = hashlib.sha256(fixed_route_id.encode()).hexdigest()[:12]
    other_call_id = hashlib.sha256(b"a-different-route-id").hexdigest()[:12]
    assert same_call_id != other_call_id
    assert _sanitize_reservation_id(CLAUDE, same_call_id) == result1.reservation_id
    assert _sanitize_reservation_id(CLAUDE, other_call_id) != result1.reservation_id


def test_paid_replay_before_dispatch_completed_never_dispatches_reservation_retained(repo, monkeypatch):
    # Replay after DispatchStarted, before DispatchCompleted, never re-dispatches:
    # pre-claim the recorder for the candidate's DispatchStarted event_id BEFORE
    # calling execute() at all — this simulates a crash/retry landing strictly
    # between the ORIGINAL dispatch's claim and its DispatchCompleted. execute()
    # must see claimed=False immediately: zero backend calls THIS execute() call,
    # and the (paid) reservation it opens is RETAINED, never released.
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    budget = _Budget(10_000.0)
    rec = _ClaimingRecorder()
    counter = _CallCounter()
    route_id = "pre-claimed-paid-route"

    # The ORIGINAL dispatch this replay simulates opened its reservation with the
    # SAME deterministic id execute() will derive (audited path: call_id =
    # sha256(route_id)[:12]). Pre-claim with that EXACT reservation_id — a paid
    # candidate's real DispatchStarted carries a non-None reservation_id, so
    # pre-claiming with None would now (finding #2) be a payload CONFLICT and raise
    # an integrity error, not a legitimate replay.
    import hashlib

    from llmxive.model_selection.execute import _sanitize_reservation_id

    derived_call_id = hashlib.sha256(route_id.encode()).hexdigest()[:12]
    derived_rid = _sanitize_reservation_id(_paid_ref().model_id, derived_call_id)
    pre_started = DispatchStarted(
        route_id=route_id, candidate_index=0, candidate=_paid_ref(), reservation_id=derived_rid,
    )
    assert rec.claim_dispatch(pre_started) is True  # simulates the ORIGINAL dispatch's own claim

    with pytest.raises(RouteReplayError):
        execute(
            _paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
            backend_factory=_counting_factory(counter), ledger_repo=repo, ledger_config=LOCAL_CFG,
            credit_observer=_observer(), balance_fetch=_balance(), now=NOW,
            reservation_authority=budget, route_audit=rec, route_id=route_id,
        )

    assert counter.count == 0  # never dispatched for THIS execute() call
    assert budget.retained, "the reservation opened by this call must be RETAINED, not released"
    (r,) = project(read_events(repo)).values()
    assert r.state == STATE_SETTLING  # settle() ran on the replay path — hold reached settling


def test_concurrent_same_route_id_dispatches_backend_exactly_once(repo, monkeypatch):
    # Concurrent same-route: backend called exactly once. Two threads race
    # execute() for the SAME route_id, sharing ONE _ClaimingRecorder + ONE
    # backend counter — the ATOMIC claim_dispatch() must let exactly one thread
    # cross the dispatch boundary; the other raises RouteReplayError. Proves the
    # claim is a genuine compare-and-swap, not a read-then-write race.
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    budget = _Budget(10_000.0)
    rec = _ClaimingRecorder()
    counter = _CallCounter()
    route_id = "concurrent-route"

    def _run():
        return execute(
            _paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
            backend_factory=_counting_factory(counter), ledger_repo=repo, ledger_config=LOCAL_CFG,
            credit_observer=_observer(), balance_fetch=_balance(), now=NOW,
            reservation_authority=budget, route_audit=rec, route_id=route_id,
        )

    outcomes: list[tuple[str, object]] = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(_run) for _ in range(2)]
        for fut in futures:
            try:
                outcomes.append(("ok", fut.result()))
            except RouteReplayError as exc:
                outcomes.append(("replay", exc))

    oks = [r for kind, r in outcomes if kind == "ok"]
    replays = [r for kind, r in outcomes if kind == "replay"]
    assert len(oks) == 1, f"expected exactly one success, got {outcomes}"
    assert len(replays) == 1, f"expected exactly one replay, got {outcomes}"
    # The crux: even racing two threads, the backend was invoked exactly once.
    assert counter.count == 1

    reservations = project(read_events(repo))
    matching = [rid for rid in reservations if rid == oks[0].reservation_id]
    assert len(matching) == 1
    assert reservations[oks[0].reservation_id].state == STATE_SETTLING


# --------------------------------------------------------------------------- #
# Slice-0 audit fix #6 (HIGH finding #1): a stable route_id WITHOUT a route_audit
# sink must NOT collapse two same-route paid calls onto one reserved envelope.
# Without a sink there is no atomic claim_dispatch gate (claimed=True always), so
# a route_id-DERIVED call_id would give both calls the SAME reservation_id — the
# 026 ledger idempotently no-ops the second reserve(), yet the backend is STILL
# invoked twice → up to 2x retries paid attempts charged under ONE envelope. The
# fix mints a FRESH call_id per no-audit call so each opens its OWN envelope.
# --------------------------------------------------------------------------- #


def test_paid_no_audit_same_route_id_opens_separate_reservations(repo, monkeypatch):
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    budget = _Budget(10_000.0)
    counter = _CallCounter()
    fixed_route_id = "no-audit-retry-route"

    def _run():
        return execute(
            _paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
            backend_factory=_counting_factory(counter), ledger_repo=repo, ledger_config=LOCAL_CFG,
            credit_observer=_observer(), balance_fetch=_balance(), now=NOW,
            reservation_authority=budget, route_audit=None, route_id=fixed_route_id,
        )

    result1 = _run()
    result2 = _run()

    # Without a sink there is NO dispatch idempotency: both calls dispatched.
    assert counter.count == 2

    # The crux of fix #6: each no-audit call opened its OWN reservation — the two
    # reservation_ids DIFFER (fresh per-call call_id), NOT one shared envelope.
    assert result1.reservation_id is not None
    assert result2.reservation_id is not None
    assert result1.reservation_id != result2.reservation_id

    # The 026 ledger holds TWO distinct reservations, each independently budgeted —
    # under the pre-fix stable-call_id derivation this would be ONE (the second
    # reserve() no-op'd), i.e. a double dispatch under a single envelope.
    reservations = project(read_events(repo))
    assert result1.reservation_id in reservations
    assert result2.reservation_id in reservations
    assert reservations[result1.reservation_id].state == STATE_SETTLING
    assert reservations[result2.reservation_id].state == STATE_SETTLING

    # Both envelopes are retained by the Attempt authority (both dispatched
    # successfully), accounted separately — never collapsed to one.
    assert {result1.reservation_id, result2.reservation_id} <= budget.retained
