"""Selection types for the funded provider (spec 027 task 6)."""

from __future__ import annotations

from datetime import date

import pytest

from llmxive.model_selection.types import (
    STRENGTH_LEVELS,
    ArenaScore,
    CallBudget,
    Candidate,
    ModelPricing,
    ModelRef,
    ModelRequirement,
    ModelScores,
    RequirementOverrides,
    cost_class_of,
    shift_level,
    worst_case_usd,
)
from tests.conftest import _offline_snapshot


def test_cost_class_is_funded_even_at_zero_price():
    assert cost_class_of("huggingface", ModelPricing(0.0, 0.0)) == "funded"
    assert cost_class_of("huggingface", ModelPricing(None, None)) == "funded"


def test_cost_class_free_and_paid_follow_price_off_hugging_face():
    assert cost_class_of("dartmouth", ModelPricing(0.0, 0.0)) == "free"
    assert cost_class_of("dartmouth", ModelPricing(1e-6, 5e-6)) == "paid"
    assert cost_class_of("local", ModelPricing(0.0, 0.0)) == "free"


def test_candidate_cost_class_is_derived_not_defaulted():
    paid = Candidate(ModelRef("dartmouth", "ep", "m", "f", "v"), ModelPricing(1e-6, 5e-6), 2.5, 10.0)
    assert paid.cost_class == "paid"
    hf = Candidate(ModelRef("huggingface", "ep", "m", "f", "v"), ModelPricing(0.0, 0.0), 0.0, 10.0)
    assert hf.cost_class == "funded"


def test_worst_case_usd():
    assert worst_case_usd(ModelPricing(1e-7, 4e-7), CallBudget(10_000, 2_000)) == pytest.approx(0.0018)
    assert worst_case_usd(ModelPricing(None, None), CallBudget(1, 1)) is None


@pytest.mark.parametrize(
    "level,delta,want",
    [
        ("strong", 1, "strongest"),
        ("strong", 5, "strongest"),
        ("economy", -1, "economy"),
        ("balanced", -1, "economy"),
        ("economy", 2, "strong"),
        ("strongest", 0, "strongest"),
    ],
)
def test_shift_level_clamps(level, delta, want):
    assert shift_level(level, delta) == want
    assert STRENGTH_LEVELS == ("economy", "balanced", "strong", "strongest")


def test_arena_score_rejects_inconsistent_bounds_and_scores_pick_by_track():
    d = date(2026, 11, 22)
    with pytest.raises(ValueError):
        ArenaScore(1300.0, 1310.0, 1320.0, d)
    with pytest.raises(ValueError):
        ArenaScore(float("nan"), 1.0, 2.0, d)
    s = ModelScores(reasoning=ArenaScore(1300.0, 1300.0, 1300.0, d))
    assert s.for_track("reasoning").rating == 1300.0 and s.for_track("coding") is None


def test_requirement_and_override_defaults():
    r = ModelRequirement(capability="deep", call_budget=CallBudget(1, 1))
    assert (r.profile, r.track, r.strength, r.budget_step_down) == (None, None, None, False)
    assert RequirementOverrides().level_delta == 0 and RequirementOverrides(level_delta=-2).level_delta == -2
    for bad in (True, 1.0, "1"):
        with pytest.raises(TypeError):
            RequirementOverrides(level_delta=bad)


def test_snapshot_new_fields_default_empty_and_are_read_only():
    snap = _offline_snapshot()
    assert snap.funded is None and dict(snap.scores) == {} and dict(snap.observed) == {}
    with pytest.raises(TypeError):
        snap.scores["x"] = ModelScores()
