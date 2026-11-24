"""The self_improvement_proposal ReviewSpec (spec 025 slice 1B, Task 7).

Integration, because the builder resolves REAL prompt files from the REAL repo root: a
missing or misnamed lens prompt must fail here rather than at runtime, inside an Attempt
that has already spent its budget getting there.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from llmxive.convergence.self_improvement_specs import (
    LANE_ATTEMPT_CEILING,
    PATCH_LENSES,
    PROPOSAL_LENSES,
    PROPOSAL_MAX_ROUNDS,
    PROPOSAL_STAGE,
    build_proposal_review_spec,
)
from llmxive.convergence.types import Severity
from llmxive.model_selection.types import IndependenceBaseline
from llmxive.self_improvement.call_ledger import LaneCallLedger
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log
from llmxive.self_improvement.route_context import (
    LaneRouteContext,
    patch_call_ceiling,
    proposal_call_ceiling,
)

_BUDGET = 50.0   # the Attempt credit budget; ONE AttemptConfigured record binds it
                 # together with the call ceiling (Slice 1A Task 13), so every
                 # ledger for this Attempt must present the SAME pair.
_BASELINE = IndependenceBaseline(families=frozenset({"qwen3.5"}))
#: The real repo, so the builder resolves the real prompt files.
_REPO_ROOT = Path(__file__).resolve().parents[2]


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
    ledger = LaneCallLedger(
        repo=repo, problem_id="P1", attempt_id="A1", actor="lane",
        clock=lambda: "2026-07-25T00:00:00+00:00", config=LaneLogConfig(),
        call_ceiling=LANE_ATTEMPT_CEILING,      # the WHOLE-Attempt figure, never a component
        attempt_budget_credits=_BUDGET,
    )
    return LaneRouteContext(
        repo=repo, problem_id="P1", attempt_id="A1", actor="lane",
        clock=lambda: "2026-07-25T00:00:00+00:00", route_audit=_Sink(),
        reservation_authority=_Budget(), call_ledger=ledger,
    )


def test_spec_wires_every_lens_with_the_reroute_and_the_shared_context(repo):
    ctx = _ctx(repo)
    spec = build_proposal_review_spec(
        backend=object(), repo_root=_REPO_ROOT, proposer_baseline=_BASELINE,
        route_context=ctx,
    )
    assert spec.stage == PROPOSAL_STAGE and spec.max_rounds == PROPOSAL_MAX_ROUNDS
    assert tuple(r.name for r in spec.reviewers) == PROPOSAL_LENSES
    for r in spec.reviewers:
        assert r._profile == "independent_review" and r._fallback_profile == "deep_review"
        assert r._independence_against is _BASELINE
        assert r._route_context is ctx          # the SAME context across the panel
    # the reviser shares the context too (F3: its calls are audited + budgeted)
    assert spec.reviser is not None and spec.reviser._route_context is ctx
    assert spec.artifacts == ["proposal.md"]


def test_every_lens_prompt_actually_loads_from_the_real_repo(repo):
    # `LLMReviewer.__init__` loads its prompt eagerly (llm_reviewer.py:962), so a missing
    # panel_si_proposal_<lens>.md already fails CONSTRUCTION rather than surfacing
    # mid-Attempt — good, and the reason every test in this file that builds a spec is
    # also a prompt-existence test. This one additionally checks the CONTENT contract:
    # the lens is actually addressed, and the SSoT output protocol got concatenated.
    spec = build_proposal_review_spec(
        backend=object(), repo_root=_REPO_ROOT, proposer_baseline=_BASELINE,
        route_context=_ctx(repo),
    )
    from llmxive.convergence.llm_reviewer import _load_system_prompt

    for reviewer in spec.reviewers:
        prompt = _load_system_prompt(stage=PROPOSAL_STAGE, lens=reviewer.name,
                                     repo_root=_REPO_ROOT)
        assert reviewer.name in prompt, f"{reviewer.name}'s prompt does not name its lens"
        # the SSoT output protocol is CONCATENATED by the loader, never restated per lens
        assert "Concerns" in prompt, "the shared panel-review block did not get appended"


def test_context_is_mandatory():
    # F3: there is no way to build an unaudited/unbudgeted proposal panel.
    with pytest.raises(TypeError):
        build_proposal_review_spec(
            backend=object(), repo_root=_REPO_ROOT,
            proposer_baseline=IndependenceBaseline(), )  # no route_context


def test_the_bound_ceiling_is_the_WHOLE_attempt_not_this_panel():
    # F1: AttemptConfigured binds ONE immutable number for the whole Attempt. Binding the
    # proposal component would starve the proposer/implementer/patch stages AND make the
    # real figure unbindable later.
    assert proposal_call_ceiling(len(PROPOSAL_LENSES), PROPOSAL_MAX_ROUNDS) == 56  # N=5, R=3
    assert len(PATCH_LENSES) == 5                        # the ceiling's N_q
    assert LANE_ATTEMPT_CEILING == 90
    assert LANE_ATTEMPT_CEILING > proposal_call_ceiling(len(PROPOSAL_LENSES),
                                                        PROPOSAL_MAX_ROUNDS)
    # and it is the SUM of the whole Attempt, not just the bigger component
    assert LANE_ATTEMPT_CEILING == (
        1 + 2
        + proposal_call_ceiling(len(PROPOSAL_LENSES), PROPOSAL_MAX_ROUNDS)
        + patch_call_ceiling(len(PATCH_LENSES), PROPOSAL_MAX_ROUNDS)
    )


def test_every_severity_routes_to_rejected():
    # A proposal is pre-claim work with nothing behind it: there is no lesser outcome to
    # route a writing-class concern to, the way the doc stages have.
    from llmxive.convergence.self_improvement_specs import _kickback_routing

    routing = _kickback_routing()
    assert set(routing) == set(Severity), "every severity must be explicit, not a fallback"
    assert set(routing.values()) == {"rejected"}


def test_the_overflow_goal_is_a_summarizer_instruction_not_a_stage(repo):
    # engine._maybe_reduce passes overflow_goal straight to the SSoT summarizer as its
    # goal. A stage name there would tell the summarizer to preserve the word "rejected",
    # degrading the exact artifact the five lenses read.
    spec = build_proposal_review_spec(
        backend=object(), repo_root=_REPO_ROOT, proposer_baseline=_BASELINE,
        route_context=_ctx(repo),
    )
    assert spec.overflow_goal != "rejected"
    assert "preserve" in spec.overflow_goal
    for must_survive in ("causal claim", "evidence", "file/test list"):
        assert must_survive in spec.overflow_goal
