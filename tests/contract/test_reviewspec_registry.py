"""Contract tests for the ReviewSpec registry (spec 015 T048).

Verifies: EXEMPT stages return None; every reviewable stage returns a populated
ReviewSpec with the right kickback routing + advance stage + constitution flag;
TODO placeholders fail loudly when invoked (no silent empty verdicts).
"""

from __future__ import annotations

import pytest

from llmxive.convergence.reviewspecs import (
    EXEMPT_STAGES,
    reviewable_stages,
    reviewspec_for,
)
from llmxive.convergence.types import ReviewSpec, Severity


@pytest.mark.parametrize("stage", sorted(EXEMPT_STAGES))
def test_exempt_stages_return_none(stage):
    """FR-029: mechanical / dispatch / maintenance steps run no convergence loop."""
    assert reviewspec_for(stage) is None


def test_reviewable_stages_have_specs():
    """Every reviewable stage in the contract returns a ReviewSpec."""
    stages = reviewable_stages()
    # 9 stages from the contract table (idea + 4 research + 4 paper).
    assert len(stages) == 9
    for s in stages:
        spec = reviewspec_for(s)
        assert isinstance(spec, ReviewSpec)
        assert spec.stage == s
        assert spec.reviewers, f"stage {s!r} has no reviewers"
        assert spec.reviser is not None, f"stage {s!r} has no reviser"
        assert spec.advance_stage is not None, f"stage {s!r} has no advance_stage"
        assert spec.kickback_routing, f"stage {s!r} has no kickback_routing"
        assert spec.overflow_goal, f"stage {s!r} has no overflow_goal"


def test_constitution_input_set_from_specified_onward():
    """FR-030 (global rule): per-project constitution is a standard panel + analyze
    input from ``specified`` onward. The idea-stage spec doesn't include it (no
    constitution exists yet at that stage); every other spec does."""
    idea = reviewspec_for("flesh_out_complete")
    assert idea is not None and idea.constitution_input is False

    for stage in reviewable_stages():
        if stage == "flesh_out_complete":
            continue
        spec = reviewspec_for(stage)
        assert spec is not None and spec.constitution_input is True, \
            f"{stage!r} must have constitution_input=True (FR-030)"


def test_kickback_routing_covers_writing_through_fatal():
    """Every spec routes the major severities. (TRIVIAL/CODE intentionally absent
    in some specs — early stages don't deal with code-level concerns.)"""
    for stage in reviewable_stages():
        spec = reviewspec_for(stage)
        assert spec is not None
        required = {Severity.WRITING, Severity.REQUIREMENT, Severity.METHODOLOGY,
                    Severity.SCIENCE, Severity.FATAL}
        missing = required - set(spec.kickback_routing)
        assert not missing, f"{stage!r} kickback_routing missing severities: {missing}"


def test_max_rounds_default_is_three():
    """FR-013: per-step cap is 3 unless a spec overrides for a specific reason."""
    for stage in reviewable_stages():
        spec = reviewspec_for(stage)
        assert spec is not None and spec.max_rounds == 3


def test_placeholder_reviewer_fails_loud(tmp_path):
    """TODO-reviewer placeholders MUST raise a clear pointer to the follow-up
    task when called — never produce silent empty verdicts."""
    spec = reviewspec_for("planned")
    assert spec is not None
    rev = spec.reviewers[0]
    with pytest.raises(NotImplementedError, match=r"prompt is authored in T0\d{2}"):
        rev.identify({}, constitution=None, advisory=[])
    with pytest.raises(NotImplementedError):
        rev.rereview({}, [], [], constitution=None, advisory=[])
    with pytest.raises(NotImplementedError, match=r"agent wiring lands in T0\d{2}"):
        spec.reviser.revise({}, [])


def test_research_unit_reuses_8_panel_lenses():
    """The research-unit ReviewSpec carries the EXISTING 8-panel (generic + 7
    specialists) per the design's reuse-and-extend principle."""
    spec = reviewspec_for("research_review")
    assert spec is not None
    names = {r.name for r in spec.reviewers}
    expected = {
        "research_reviewer",            # generic
        "idea_quality", "creativity",
        "implementation_correctness", "implementation_completeness",
        "code_quality", "data_quality", "filesystem_hygiene",
    }
    assert expected <= names


def test_paper_implement_reuses_12_panel_lenses():
    """The paper-implement ReviewSpec carries the EXISTING 12-panel."""
    spec = reviewspec_for("paper_review")
    assert spec is not None
    names = {r.name for r in spec.reviewers}
    # generic + 12 specialists from agents/registry.yaml
    assert "paper_reviewer" in names
    assert len(spec.reviewers) >= 12


def test_unknown_stage_returns_none():
    assert reviewspec_for("not_a_real_stage") is None
