"""Requirement-profile tests (spec 026, slice 2, FR-012)."""

from __future__ import annotations

import pytest

from llmxive.model_selection.profiles import PROFILES, build_requirement, profile
from llmxive.model_selection.types import CallBudget, IndependenceBaseline, ModelRequirement

_REQUIRED_PROFILES = {
    "cheap_structured",
    "standard_generation",
    "deep_review",
    "deep_code",
    "vision",
    "independent_review",
}

_CB = CallBudget(max_input_tokens=1000, max_output_tokens=512)


def test_all_required_profiles_present():
    assert _REQUIRED_PROFILES <= set(PROFILES)


def test_profile_capabilities():
    assert profile("cheap_structured").capability == "cheap"
    assert profile("standard_generation").capability == "standard"
    assert profile("deep_review").capability == "deep"
    assert profile("deep_code").capability == "deep"
    assert profile("vision").capability == "vision"
    assert profile("independent_review").capability == "deep"


def test_independent_review_encodes_panel_independence():
    p = profile("independent_review")
    assert p.required_independence == frozenset({"family"})
    assert p.preferred_independence == frozenset({"serving_endpoint"})
    assert p.max_catalog_age_s == 900  # tighter freshness for a high-stakes review


def test_build_produces_requirement_with_budget_and_capability():
    req = profile("deep_review").build(_CB)
    assert isinstance(req, ModelRequirement)
    assert req.capability == "deep"
    assert req.call_budget is _CB
    assert req.allow_paid is False
    assert req.independence_against == IndependenceBaseline()


def test_build_overrides_apply():
    req = profile("deep_review").build(_CB, allow_paid=True, max_credits=5)
    assert req.allow_paid is True
    assert req.max_credits == 5
    assert req.capability == "deep"  # untouched fields preserved


def test_build_threads_independence_baseline():
    base = IndependenceBaseline(families=frozenset({"qwen3.5"}))
    req = profile("independent_review").build(_CB, independence_against=base)
    assert req.independence_against is base
    assert req.required_independence == frozenset({"family"})


def test_build_requirement_convenience_matches_profile_build():
    a = build_requirement("vision", _CB)
    b = profile("vision").build(_CB)
    assert a == b


def test_unknown_profile_raises():
    with pytest.raises(KeyError):
        profile("no_such_profile")
