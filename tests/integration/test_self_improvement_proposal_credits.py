"""F2: the Attempt budget binds through the PANEL, not just through a direct execute()
call. The engine dispatches the 5 lenses through a real ThreadPoolExecutor
(engine.py:85-133, cap 8), all sharing ONE AttemptCreditLedger, so this exercises the
genuine concurrent-reservation path with paid opt-in ON.
"""

from __future__ import annotations

import subprocess
import threading
from dataclasses import replace
from pathlib import Path

import pytest

from llmxive.convergence.self_improvement_specs import (
    LANE_ATTEMPT_CEILING,
    PROPOSAL_LENSES,
    run_proposal_review,
)
from llmxive.model_selection.types import (
    IndependenceBaseline,
    ModelPricing,
    worst_case_credits,
)
from llmxive.self_improvement.audit_sink import EventStoreRouteAudit
from llmxive.self_improvement.call_ledger import LaneCallLedger
from llmxive.self_improvement.credit_ledger import (
    AttemptCreditLedger,
    counting_total,
    project_reservations,
)
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log, read
from llmxive.self_improvement.route_context import LaneRouteContext

from .test_self_improvement_proposal_review import (  # the SSoT scripted panel
    _ScriptedPanelBackend,
)

_CLOCK = lambda: "2026-07-25T00:00:00+00:00"  # noqa: E731
_BASELINE = IndependenceBaseline(families=frozenset({"qwen3.5"}))
_REPO_ROOT = Path(__file__).resolve().parents[2]
#: `route_chat`'s own default (route.py:254). The retry envelope reserves
#: `worst_case x retries`, so the budget arithmetic must use the SAME number.
_ROUTE_RETRIES = 3


def _git(repo, *a):
    subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    bootstrap_lane_log(tmp_path, config=LaneLogConfig())
    return tmp_path


class _ThreadRecordingAuthority:
    """A REAL delegating ReservationAuthority (not a mock): every call goes to the genuine
    AttemptCreditLedger; this only RECORDS who called and what came back, so the test can
    prove the authority was actually exercised concurrently and that some candidate was
    genuinely refused by the cap."""

    def __init__(self, inner):
        self._inner = inner
        self._lock = threading.Lock()
        self.threads: set[int] = set()
        self.admitted: list[tuple[str, float]] = []
        self.refused: list[tuple[str, float]] = []

    def reserve(self, credits, *, reservation_id, call_id) -> bool:
        ok = self._inner.reserve(credits, reservation_id=reservation_id, call_id=call_id)
        with self._lock:
            self.threads.add(threading.get_ident())
            (self.admitted if ok else self.refused).append((reservation_id, credits))
        return ok

    def release(self, reservation_id) -> None:
        self._inner.release(reservation_id)

    def mark_retained(self, reservation_id) -> None:
        self._inner.mark_retained(reservation_id)


def _paid_only_snapshot(*, paid_opt_in: bool = True):
    """The offline chain repriced so EVERY candidate is paid, with a live credit guard.

    Asserts its own contract at the end: `select.py:139` admits a paid candidate only when
    `credit.source == "live" and credit.paid_opt_in`, so a wrong credit field would filter
    every candidate and the test would pass by proving nothing about the ledger.
    """
    import llmxive.model_selection.route as route_mod

    base = route_mod.runtime_snapshot()
    pricing = {mid: ModelPricing(1e-6, 5e-6) for mid in base.pricing}
    # The DAILY (026) cap is raised far above the Attempt budget on purpose: two ledgers
    # gate a paid call, and this test is about the ATTEMPT one. Leaving the daily cap near
    # the Attempt budget would make it ambiguous which ledger refused a candidate.
    credit = replace(base.credit, source="live", paid_opt_in=paid_opt_in,
                     max_budget=1_000_000.0, effective_cap=750_000.0,
                     available_headroom=750_000.0, spend=0.0)
    snap = replace(base, pricing=pricing, credit=credit,
                   sources={**base.sources,
                            "credit": replace(base.sources["credit"], source="live")})

    assert snap.credit.source == "live"
    assert snap.credit.paid_opt_in is paid_opt_in
    assert snap.pricing and all(not p.is_free for p in snap.pricing.values()), \
        "a free candidate would dispatch without ever consulting the Attempt authority"
    return snap


def _worst_case_envelope(snap, *, max_tokens: int) -> float:
    """One candidate's RESERVED envelope, from the snapshot's own prices and the real
    call budget — never a hard-coded credit figure (F9).

    Uses the largest lens prompt as the input sample, so the derived budget admits at least
    a few whole envelopes rather than being accidentally too small for any of them.
    """
    from llmxive.backends.base import ChatMessage
    from llmxive.convergence.llm_reviewer import _load_system_prompt
    from llmxive.model_selection.tokens import call_budget_for

    biggest = max(
        (_load_system_prompt(stage="self_improvement_proposal", lens=lens,
                             repo_root=_REPO_ROOT) for lens in PROPOSAL_LENSES),
        key=len,
    )
    budget = call_budget_for([ChatMessage(role="system", content=biggest)], max_tokens)
    per_call = max(
        c for c in (worst_case_credits(p, budget) for p in snap.pricing.values())
        if c is not None
    )
    # execute.py:178 — a paid candidate reserves worst_case x retries.
    return per_call * _ROUTE_RETRIES


def _reviewer_max_tokens() -> int:
    """The token bound a lane reviewer actually routes with, read off the REAL class
    rather than restated as a literal that could drift."""
    from llmxive.convergence.llm_reviewer import LLMReviewer

    reviewer = LLMReviewer(lens=PROPOSAL_LENSES[0], stage="self_improvement_proposal",
                           backend=object(), repo_root=_REPO_ROOT)
    return reviewer._max_tokens


def _controlled_balance(monkeypatch) -> dict:
    """Inject a fresh, SUCCESSFUL credit observation through the production seam.

    `execute`'s paid path makes TWO live balance reads before it ever consults
    `reservation_authority` (execute.py:179 `observer()`, then :192 `paid_call_allowed`),
    and BOTH fail closed on error. Left to the real fetch, this test passes only on a
    machine that happens to hold Dartmouth credentials — and then only by making live
    network calls. Anywhere else every candidate is skipped before the Attempt authority
    is reached, and the whole suite passes while proving nothing. (That is exactly how it
    passed locally and failed in review.)

    `balance_fetch` is `execute`'s documented injection point and both call sites resolve
    it from `credits.fetch_credit_balance`, so patching that one module attribute is the
    supported seam. Everything else stays REAL: the daily ledger, the Attempt ledger, the
    reservations, the CAS. The DAILY headroom is set far above the Attempt budget so the
    binding constraint is unambiguously the Attempt cap.
    """
    import llmxive.backends.credits as credits_mod

    calls: dict = {"n": 0}

    def _fetch():
        calls["n"] += 1
        return credits_mod.CreditBalance(
            account="test", spend=0.0, max_budget=1_000_000.0,
            budget_duration="1d", budget_reset_at="2026-07-26T03:45:00-04:00",
        )

    credits_mod.reset_balance_cache()
    monkeypatch.setattr(credits_mod, "fetch_credit_balance", _fetch)
    monkeypatch.setattr(credits_mod, "paid_opt_in_enabled", lambda: True)
    return calls


def _local_production_ledger(monkeypatch, repo):
    """Point the 026 PRODUCTION credit ledger at the temp repo, local-only.

    Two ledgers gate a paid dispatch: 026's daily ledger and this lane's Attempt ledger.
    Without this the daily one fails closed first (`ledger_config_from_env` raises unless
    `LLMXIVE_CREDIT_LEDGER_ANCHOR` is pinned), every paid candidate is SKIPPED before the
    Attempt authority is ever consulted, and the test passes while proving nothing.

    Both remain REAL — a real git-CAS ledger in a real temp repo. Only the *location* is
    redirected: `LLMXIVE_REPO_ROOT` so `execute`'s `ledger_repo = repo_root()` resolves to
    the temp repo rather than the developer's actual checkout (which it would otherwise
    write reservations into), and a local-only `LedgerConfig` so no remote fetch is
    attempted.
    """
    # `importlib`, not `import ... as` or a dotted monkeypatch string: the package
    # re-exports the `execute` FUNCTION under the same name as its module, so both of
    # those resolve to the function and setattr fails.
    import importlib

    from llmxive.model_selection.ledger_transport import LedgerConfig

    execute_mod = importlib.import_module("llmxive.model_selection.execute")

    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(repo))
    monkeypatch.setattr(execute_mod, "ledger_config_from_env",
                        lambda **_kw: LedgerConfig(remote=None))


def _paid_ctx(repo, *, budget: float):
    """The full paid wiring: a REAL AttemptCreditLedger behind a recording delegate, the
    REAL audit sink, and the REAL call ledger — all on one temp git repo."""
    cfg = LaneLogConfig()
    inner = AttemptCreditLedger(repo=repo, problem_id="P1", attempt_id="A1",
                                attempt_budget_credits=budget,
                                call_ceiling=LANE_ATTEMPT_CEILING, actor="lane",
                                clock=_CLOCK, config=cfg)
    authority = _ThreadRecordingAuthority(inner)
    sink = EventStoreRouteAudit(repo=repo, problem_id="P1", attempt_id="A1",
                                actor="lane", clock=_CLOCK, config=cfg)
    call_ledger = LaneCallLedger(
        repo=repo, problem_id="P1", attempt_id="A1", actor="lane", clock=_CLOCK, config=cfg,
        call_ceiling=LANE_ATTEMPT_CEILING,  # the WHOLE-Attempt figure, never a component
        attempt_budget_credits=budget,      # the SAME budget the credit ledger binds
    )
    ctx = LaneRouteContext(
        repo=repo, problem_id="P1", attempt_id="A1", actor="lane", clock=_CLOCK,
        route_audit=sink, reservation_authority=authority, call_ledger=call_ledger,
        config=cfg,
    )
    return ctx, authority


def test_concurrent_panel_reviewers_never_exceed_the_attempt_budget(repo, monkeypatch):
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    _local_production_ledger(monkeypatch, repo)
    balance_calls = _controlled_balance(monkeypatch)
    snap = _paid_only_snapshot()             # asserts its own contract
    monkeypatch.setattr("llmxive.model_selection.route._acquire_snapshot", lambda: snap)

    # Derive the budget from the SNAPSHOT's real prices + the call's token bound, not a
    # magic number (F9): room for ~2 of the 5 concurrent worst-case envelopes, so some
    # reviewers are admitted and some are genuinely refused by the cap.
    budget = 2 * _worst_case_envelope(snap, max_tokens=_reviewer_max_tokens())
    ctx, authority = _paid_ctx(repo, budget=budget)

    # Starving some lenses means those routes fail; whether the panel as a whole returns
    # or aborts is nondeterministic, so accept either and assert on the DURABLE state.
    from llmxive.backends.base import BackendUnavailable
    try:
        run_proposal_review(
            backend=_ScriptedPanelBackend(), repo_root=_REPO_ROOT,
            proposer_baseline=_BASELINE, route_context=ctx,
            artifacts={"proposal.md": "# Proposal\n\nNarrow the retry loop.\n"},
        )
    except BackendUnavailable:
        pass

    events = read(repo, "P1", config=LaneLogConfig())
    reservations = project_reservations(events, "A1")

    # 1. THE invariant (US1 scenario 5): reserved envelopes never exceed the cap, no matter
    #    how the 5 concurrent reviewers interleaved.
    assert counting_total(reservations) <= budget

    # 0. The balance seam was actually in effect. Without this the suite could silently
    #    revert to live fetching (passing only where credentials exist) or to failing
    #    closed before the authority (passing vacuously) — the two ways this test has
    #    already been wrong.
    assert balance_calls["n"] > 0, "the paid path never read a balance — it failed closed earlier"

    # 2. The authority was genuinely exercised, CONCURRENTLY (F9: without this, "no
    #    dispatch happened at all" would pass assertion 1 vacuously).
    assert len(authority.threads) > 1, "reviewers did not compete from separate threads"

    # 3. At least one paid dispatch actually COMPLETED — the budget bound is meaningless if
    #    nothing ever ran.
    completed = [e for e in events if e.event_type == "DispatchCompleted"]
    assert completed, "no paid dispatch completed — the test proved nothing about the cap"

    # 4. At least one candidate was REFUSED by the Attempt cap (that is the behavior under
    #    test; if everything fit, the budget was too generous).
    assert authority.refused, "no reservation was refused — tighten the budget"

    # 5. Every paid DispatchStarted is backed by a real reservation, and no reservation
    #    exists that the projection doesn't know about (no silent unpriced dispatch).
    started = [e for e in events if e.event_type == "DispatchStarted"]
    paid_started = [e for e in started if e.payload.get("reservation_id")]
    assert paid_started, "expected paid dispatches in a paid-only chain"
    for e in paid_started:
        assert e.payload["reservation_id"] in reservations

    # 6. The admitted envelopes sum EXACTLY to the durable projection — the recorded
    #    decisions and the persisted state cannot drift.
    assert counting_total(reservations) == pytest.approx(
        sum(c for rid, c in authority.admitted
            if rid in reservations and reservations[rid].state != "released")
    )
    for r in reservations.values():
        assert r.state in {"open", "retained", "reconciled", "released"}


def test_with_paid_opt_in_OFF_no_paid_candidate_ever_dispatches(repo, monkeypatch):
    """The other half of the F2 contract: paid eligibility follows the PROCESS opt-in
    (route.py:353), so with the opt-in off the same paid-only chain must select nothing and
    open no reservation — never a paid dispatch, never a charge."""
    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False)
    _local_production_ledger(monkeypatch, repo)
    # A balance read here would mean the opt-in gate did NOT stop it — the refusal must
    # come from SELECTION (allow_paid_eff=False filters every paid candidate), upstream of
    # the credit read entirely. Counting the reads is how this test proves it refused for
    # the right reason rather than passing because some later gate failed closed.
    balance_calls = _controlled_balance(monkeypatch)
    snap = _paid_only_snapshot(paid_opt_in=False)
    monkeypatch.setattr("llmxive.model_selection.route._acquire_snapshot", lambda: snap)
    # A budget large enough that ONLY the opt-in can be what blocks a reservation.
    ctx, authority = _paid_ctx(repo, budget=1000.0)

    # With a paid-only chain and the opt-in OFF, selection finds nothing eligible for
    # EVERY lens → ModelUnavailable → BackendUnavailable, which Task 8 propagates as a
    # clean abort. Assert the exception, THEN the durable state — which is what actually
    # proves the budget invariant (round-11 F4).
    from llmxive.backends.base import BackendUnavailable

    with pytest.raises(BackendUnavailable):
        run_proposal_review(
            backend=_ScriptedPanelBackend(), repo_root=_REPO_ROOT,
            proposer_baseline=_BASELINE, route_context=ctx,
            artifacts={"proposal.md": "# Proposal"},
        )

    events = read(repo, "P1", config=LaneLogConfig())
    assert not project_reservations(events, "A1"), "a paid reservation opened with opt-in OFF"
    assert not authority.admitted, "the Attempt authority admitted a reservation with opt-in OFF"
    assert not [e for e in events if e.event_type == "DispatchStarted"]
    assert balance_calls["n"] == 0, (
        "a credit balance was read with the opt-in OFF — selection should have filtered "
        "every paid candidate before the paid path was reached"
    )
