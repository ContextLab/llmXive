"""Funded policy cut-offs, per-profile track/level, and the level_delta override (spec 027 Task 11)."""

from dataclasses import fields

import pytest

from llmxive.model_selection.policy import FUNDED_POLICY, FundedPolicy
from llmxive.model_selection.profiles import PROFILES, build_requirement
from llmxive.model_selection.route import _requirement_digest, resolve_chain
from llmxive.model_selection.types import CallBudget, RequirementOverrides, shift_level

B1 = CallBudget(1_000, 100)


def test_profile_defaults_are_the_approved_track_and_level():
    want = {"cheap_structured": ("reasoning", "economy", True), "standard_generation": ("reasoning", "balanced", True),
            "deep_review": ("reasoning", "strong", False), "independent_review": ("reasoning", "strong", False),
            "deep_code": ("coding", "strong", True), "vision": ("reasoning", "balanced", False)}
    assert {n: (p.track, p.strength, p.budget_step_down) for n, p in PROFILES.items()} == want


def test_build_carries_profile_track_and_level():
    r = build_requirement("deep_code", B1)
    assert (r.profile, r.track, r.strength, r.budget_step_down) == ("deep_code", "coding", "strong", True)


def test_funded_policy_holds_the_approved_cutoffs_and_no_score():
    assert dict(FUNDED_POLICY.level_top_percent) == {"economy": 50, "balanced": 30, "strong": 10, "strongest": None}
    assert (FUNDED_POLICY.max_publish_age_days, FUNDED_POLICY.max_chain_slots) == (7, 2)
    assert {f.name for f in fields(FundedPolicy)} == {"level_top_percent", "max_publish_age_days", "max_chain_slots"}


@pytest.mark.parametrize("profile,delta,want", [("deep_code", 1, "strongest"), ("deep_code", 5, "strongest"),
    ("deep_code", -1, "balanced"), ("cheap_structured", -3, "economy"), ("standard_generation", 0, "balanced")])
def test_level_delta_shifts_the_profile_level_for_one_call(profile, delta, want):   # offline snapshot (tests/conftest.py)
    req, _ = resolve_chain([], profile=profile, max_tokens=1, overrides=RequirementOverrides(level_delta=delta))
    assert req.strength == want
    assert resolve_chain([], profile=profile, max_tokens=1)[0].strength == PROFILES[profile].strength


def test_requirement_digest_sees_profile_track_and_level():
    a = _requirement_digest(build_requirement("deep_review", B1))
    assert a != _requirement_digest(build_requirement("independent_review", B1))
    assert a != _requirement_digest(build_requirement("deep_review", B1, strength="strongest"))
    assert a != _requirement_digest(build_requirement("deep_review", B1, budget_step_down=True))
    assert a != _requirement_digest(build_requirement("deep_review", B1, track="coding"))   # track alone
    assert a == _requirement_digest(build_requirement("deep_review", B1))


def test_requirement_digest_sees_a_level_delta_resolved_through_resolve_chain():
    base, _ = resolve_chain([], profile="deep_review", max_tokens=1, overrides=RequirementOverrides(level_delta=0))
    raised, _ = resolve_chain([], profile="deep_review", max_tokens=1, overrides=RequirementOverrides(level_delta=1))
    assert (base.strength, raised.strength) == ("strong", "strongest")
    assert _requirement_digest(base) != _requirement_digest(raised)


def test_strongest_saturates_under_plus_one():
    assert shift_level("strongest", 1) == "strongest"
    once, _ = resolve_chain([], profile="deep_code", max_tokens=1, overrides=RequirementOverrides(level_delta=1))
    twice, _ = resolve_chain([], profile="deep_code", max_tokens=1, overrides=RequirementOverrides(level_delta=2))
    assert once.strength == twice.strength == "strongest"
    assert _requirement_digest(once) == _requirement_digest(twice)
