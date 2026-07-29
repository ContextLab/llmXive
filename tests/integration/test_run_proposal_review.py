"""`run_proposal_review` — the lane entry point that fails closed (spec 025 slice 1B, T8).

The engine's `_abort_provenance` catches only `BackendUnavailable`/`TransientBackendError`,
so the three lane-fatal conditions would otherwise propagate raw with no provenance. This
suite pins that classification, and pins what is deliberately NOT caught.

`run_convergence` itself is substituted here so a specific failure can be raised from
inside it; the REAL engine drives the same entry point in Task 9's suite.
"""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.convergence.self_improvement_specs import (
    LANE_ATTEMPT_CEILING,
    ProposalReviewOutcome,
)
from llmxive.convergence.types import ConvergenceResult
from llmxive.model_selection.attempt_hooks import (
    ChainResolved,
    DispatchCompleted,
    RouteAuditError,
    RouteReplayError,
)
from llmxive.model_selection.types import (
    IndependenceBaseline,
    ModelRef,
    SnapshotProvenance,
)
from llmxive.self_improvement.audit_sink import EventStoreRouteAudit
from llmxive.self_improvement.call_ledger import LaneCallLedger
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log
from llmxive.self_improvement.route_context import LaneCallCeilingExceeded, LaneRouteContext

_CLOCK = lambda: "2026-07-25T00:00:00+00:00"  # noqa: E731
_OBSERVED = datetime(2026, 7, 25, tzinfo=UTC)
_BUDGET = 50.0   # the Attempt credit budget; ONE AttemptConfigured record binds it
                 # together with the call ceiling (Slice 1A Task 13), so every
                 # ledger for this Attempt must present the SAME pair.

#: The producer baseline every call site in this file shares. It MUST name at least one
#: family: Task 4 refuses `IndependenceBaseline()` at construction, because
#: `independent_review` asks for a family DIFFERENCE and with nothing to differ from, any
#: model satisfies it. Shared as a constant so a later edit cannot leave one call site
#: quietly empty — an empty baseline here would not test fail-closed routing at all, it
#: would raise while building the panel, before the code under test ever ran.
_PROPOSER_BASELINE = IndependenceBaseline(families=frozenset({"qwen3.5"}))

#: The real repo, so the builder resolves the real lens prompts.
_REPO_ROOT = Path(__file__).resolve().parents[2]

_SENTINEL_RESULT = ConvergenceResult(stage="self_improvement_proposal", converged=True,
                                     rounds_used=1)


class _Sink:
    def record(self, event) -> None: ...
    def claim_dispatch(self, event) -> bool: return True


class _Budget:
    def reserve(self, credits, *, reservation_id, call_id) -> bool: return True
    def release(self, reservation_id) -> None: ...
    def mark_retained(self, reservation_id) -> None: ...


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        subprocess.run(["git", "config", k, v], cwd=str(tmp_path), check=True)
    bootstrap_lane_log(tmp_path, config=LaneLogConfig())
    return tmp_path


def _ctx(repo):
    ledger = LaneCallLedger(repo=repo, problem_id="P1", attempt_id="A1",
                            call_ceiling=LANE_ATTEMPT_CEILING,
                            attempt_budget_credits=_BUDGET, actor="lane",
                            clock=_CLOCK, config=LaneLogConfig())
    return LaneRouteContext(
        repo=repo, problem_id="P1", attempt_id="A1", actor="lane",
        clock=_CLOCK, route_audit=_Sink(),
        reservation_authority=_Budget(), call_ledger=ledger,
    )


def _write_proposer_route(repo, *, route_id, attempt="A1"):
    """Write a REAL ChainResolved + DispatchCompleted pair through the REAL sink, so the
    identity this test resolves comes out of the production write path."""
    sink = EventStoreRouteAudit(repo=repo, problem_id="P1", attempt_id=attempt,
                                actor="proposer", clock=_CLOCK, config=LaneLogConfig())
    model = ModelRef(backend="dartmouth", serving_endpoint="chat", model_id="qwen3.5-122b",
                     model_family="qwen3.5", vendor="qwen")
    prov = {"catalog": SnapshotProvenance(source="live", observed_at=_OBSERVED, age_s=0.0)}
    sink.record(ChainResolved(
        route_id=route_id, requirement_digest="rq-1", prompt_digest="pd",
        context_digest="cd", snapshot_digest="sd", snapshot_provenance=prov,
        selection_policy_version=3, resolved_at=_CLOCK(), explanation=("only free family",),
        candidates=(model,),
    ))
    sink.record(DispatchCompleted(route_id=route_id, candidate_index=0, candidate=model,
                                  reservation_id=None))



def _run(repo, monkeypatch, boom, **kw):
    from llmxive.convergence import self_improvement_specs as mod

    def _fake_run_convergence(spec, artifacts, **kwargs):
        if boom is not None:
            raise boom
        return _SENTINEL_RESULT

    monkeypatch.setattr(mod, "run_convergence", _fake_run_convergence)
    return mod.run_proposal_review(
        backend=object(), repo_root=_REPO_ROOT, proposer_baseline=_PROPOSER_BASELINE,
        route_context=_ctx(repo), artifacts={"proposal.md": "# P"}, **kw,
    )


# ---- the three lane-fatal classifications ----


def test_audit_fatal_fails_closed(repo, monkeypatch):
    out = _run(repo, monkeypatch, RouteAuditError("sink down"))
    assert out.failed_closed and out.failure_kind == "audit_fatal" and out.result is None
    assert "sink down" in out.failure_detail


def test_replay_fails_closed_and_is_never_retried(repo, monkeypatch):
    out = _run(repo, monkeypatch, RouteReplayError("already dispatched"))
    assert out.failed_closed and out.failure_kind == "replay"


def test_ceiling_fails_closed(repo, monkeypatch):
    out = _run(repo, monkeypatch, LaneCallCeilingExceeded("out of calls"))
    assert out.failed_closed and out.failure_kind == "ceiling"


def test_a_clean_run_reports_the_engines_result_verbatim(repo, monkeypatch):
    out = _run(repo, monkeypatch, None)
    assert out.result is _SENTINEL_RESULT
    assert not out.failed_closed and out.failure_kind == "" and out.failure_detail == ""


def test_backend_unavailable_is_not_swallowed(repo, monkeypatch):
    # The engine already records + re-raises this clean abort; the lane must NOT convert it
    # into a fail-closed outcome. The abort ENDS this Attempt — it does not park it for a
    # later tick, because a resumed process would re-derive the same operation ids and the
    # dispatch gate would refuse them as replays. A retry is a NEW attempt_id.
    from llmxive.backends.base import BackendUnavailable
    with pytest.raises(BackendUnavailable):
        _run(repo, monkeypatch, BackendUnavailable("breaker open"))


def test_an_unexpected_error_is_not_misclassified(repo, monkeypatch):
    # Only the three named lane conditions are classified. Anything else is a genuine
    # defect and must surface, not be laundered into a tidy failure_kind.
    with pytest.raises(ZeroDivisionError):
        _run(repo, monkeypatch, ZeroDivisionError("engine defect"))


# ---- producer provenance (F7) ----


def test_producer_is_forwarded_to_the_engine(repo, monkeypatch):
    # F7: the documented secondary guard. NOT the safeguard — that is the family
    # constraint — but it must actually reach run_convergence.
    from llmxive.convergence import self_improvement_specs as mod
    seen = {}

    def _fake_run_convergence(spec, artifacts, **kwargs):
        seen.update(kwargs)
        return _SENTINEL_RESULT

    monkeypatch.setattr(mod, "run_convergence", _fake_run_convergence)
    mod.run_proposal_review(
        backend=object(), repo_root=_REPO_ROOT, proposer_baseline=_PROPOSER_BASELINE,
        route_context=_ctx(repo), artifacts={"proposal.md": "# P"}, producer="proposer",
    )
    assert seen["producer"] == "proposer"


def test_an_unresolvable_proposer_route_id_fails_closed(repo, monkeypatch):
    # F7: a proposal whose author cannot be identified must not be reviewed as if it could.
    from llmxive.self_improvement.invocation_identity import InvocationIdentityError
    with pytest.raises(InvocationIdentityError, match="no durable author provenance"):
        _run(repo, monkeypatch, None, proposer_route_id="never-dispatched")


def test_a_resolvable_proposer_route_id_is_carried_on_the_outcome(repo, monkeypatch):
    # Write a real ChainResolved + DispatchCompleted pair for the proposer's route, then
    # assert the outcome carries the FULL identity — not just the baseline.
    _write_proposer_route(repo, route_id="PR-1")
    out = _run(repo, monkeypatch, None, proposer_route_id="PR-1")
    assert out.producer_identity is not None
    assert out.producer_identity.actor_instance_id == "PR-1"
    assert out.producer_identity.model == "qwen3.5-122b"
    assert out.producer_identity.family == "qwen3.5"
    assert out.producer_identity.route_outcome == "success"


def test_omitting_the_proposer_route_id_is_allowed_and_yields_no_identity(repo, monkeypatch):
    # The proposer itself lands in a later slice; this slice must not require it.
    out = _run(repo, monkeypatch, None)
    assert out.producer_identity is None


def test_the_identity_is_resolved_BEFORE_the_panel_runs(repo, monkeypatch):
    # Fail-closed ordering: an unidentifiable author must abort before any reviewer call is
    # dispatched, or the Attempt pays its whole budget for a review it cannot attribute.
    from llmxive.convergence import self_improvement_specs as mod
    from llmxive.self_improvement.invocation_identity import InvocationIdentityError
    ran = []

    monkeypatch.setattr(mod, "run_convergence",
                        lambda spec, artifacts, **kw: ran.append(1) or _SENTINEL_RESULT)
    ctx = _ctx(repo)
    with pytest.raises(InvocationIdentityError):
        mod.run_proposal_review(
            backend=object(), repo_root=_REPO_ROOT, proposer_baseline=_PROPOSER_BASELINE,
            route_context=ctx, artifacts={"proposal.md": "# P"},
            proposer_route_id="never-dispatched",
        )
    assert ran == [], "the panel ran despite an unresolvable author"
    assert ctx.calls_used() == 0, "the Attempt was charged for an aborted review"


def test_a_fail_closed_outcome_still_carries_the_producer_identity(repo, monkeypatch):
    # The identity is durable provenance about the AUTHOR; a lane failure during review
    # does not make it unknown, and dropping it would lose the one thing that says who
    # wrote the proposal this Attempt failed on.
    _write_proposer_route(repo, route_id="PR-1")
    out = _run(repo, monkeypatch, RouteAuditError("sink down"), proposer_route_id="PR-1")
    assert out.failed_closed and out.producer_identity is not None
    assert out.producer_identity.actor_instance_id == "PR-1"


def test_the_outcome_is_frozen():
    from dataclasses import FrozenInstanceError

    out = ProposalReviewOutcome(None, True, "ceiling", "detail")
    with pytest.raises(FrozenInstanceError):
        out.failure_kind = "replay"
