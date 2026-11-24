"""``selection_identity`` and the selector previews that replaced model-id pins.

Spec 026 removed "the requested model id". Receipts, retry counters and policy
fingerprints that used to bind one are bound to the SELECTION instead: profile +
capability-policy version + effective escalation overrides. These tests use the
real selector over the offline snapshot (``tests/conftest.py``); nothing is
mocked.
"""
from __future__ import annotations

import pytest

from llmxive.convergence import review_cache
from llmxive.model_selection import policy
from llmxive.model_selection.profiles import selection_identity
from llmxive.model_selection.route import free_peer_ids, resolve_chain
from llmxive.model_selection.types import (
    ModelUnavailable,
    RequirementOverrides,
    canonical_overrides,
)

GLM = "zai-org.glm-5.3"
QWEN = "qwen.qwen3.5-122b"
GEMMA4 = "google.gemma-4-31B-it"
GPT_OSS = "openai.gpt-oss-120b"


def test_no_overrides_and_default_overrides_are_the_same_selection():
    assert selection_identity("deep_review") == selection_identity(
        "deep_review", RequirementOverrides()
    )


@pytest.mark.parametrize(
    "other",
    [
        RequirementOverrides(allow_paid=False),
        RequirementOverrides(exclude_leader=True),
        RequirementOverrides(exclude_leaders=2),
        RequirementOverrides(require_paid=True),
        RequirementOverrides(max_credits=5),
        RequirementOverrides(level_delta=1),
        RequirementOverrides(exclude_models=frozenset({QWEN})),
    ],
)
def test_every_override_field_changes_the_selection(other):
    assert selection_identity("deep_review", other) != selection_identity("deep_review")


def test_profile_and_policy_version_are_part_of_the_selection(monkeypatch):
    base = selection_identity("deep_review")
    assert selection_identity("deep_code") != base
    assert f"policy={policy.SELECTION_POLICY_VERSION}" in base
    # A reviewed policy change is a new selection: the identity is computed from
    # the module constant, so bumping it changes every stored binding.
    import llmxive.model_selection.profiles as profiles

    monkeypatch.setattr(profiles, "SELECTION_POLICY_VERSION", policy.SELECTION_POLICY_VERSION + 1)
    assert selection_identity("deep_review") != base


def test_exclusion_set_order_does_not_change_the_selection():
    a = RequirementOverrides(exclude_models=frozenset([QWEN, GEMMA4, GPT_OSS]))
    b = RequirementOverrides(exclude_models=frozenset([GPT_OSS, QWEN, GEMMA4]))
    assert selection_identity("deep_review", a) == selection_identity("deep_review", b)


def test_review_cache_uses_the_one_canonical_form():
    ov = RequirementOverrides(allow_paid=False, exclude_leader=True)
    assert review_cache._canonical_overrides(ov) == canonical_overrides(ov)
    assert review_cache._canonical_overrides(None) == canonical_overrides(RequirementOverrides())


def test_free_peer_ids_is_the_free_chain_in_selector_order():
    assert free_peer_ids("deep_review") == (GLM, QWEN, GEMMA4, GPT_OSS)
    assert free_peer_ids("deep_review", exclude_models=frozenset({QWEN})) == (GLM, GEMMA4, GPT_OSS)


def test_free_peer_ids_agrees_with_the_real_decision():
    ov = RequirementOverrides(allow_paid=False, exclude_models=frozenset({GLM}))
    _, chain = resolve_chain([], profile="deep_review", max_tokens=1, overrides=ov)
    assert free_peer_ids("deep_review", exclude_models=frozenset({GLM})) == tuple(
        c.model_ref.model_id for c in chain.candidates
    )


def test_free_peer_ids_is_empty_on_a_paid_only_rung_or_when_nothing_is_left():
    paid_only = RequirementOverrides(allow_paid=True, require_paid=True)
    assert free_peer_ids("deep_review", overrides=paid_only) == ()
    everything = frozenset({GLM, QWEN, GEMMA4, GPT_OSS})
    assert free_peer_ids("deep_review", exclude_models=everything) == ()


@pytest.mark.parametrize(
    "overrides,leader",
    [
        (RequirementOverrides(), GLM),
        (RequirementOverrides(exclude_leader=True), QWEN),
        (RequirementOverrides(exclude_leaders=1), QWEN),
        (RequirementOverrides(exclude_leaders=2), GEMMA4),
        (RequirementOverrides(exclude_leaders=3), GPT_OSS),
        # ``exclude_leader`` is the count-of-one spelling; the larger count wins.
        (RequirementOverrides(exclude_leader=True, exclude_leaders=2), GEMMA4),
    ],
)
def test_counted_leader_exclusion_walks_down_the_ranking(overrides, leader):
    requirement, chain = resolve_chain(
        [], profile="deep_review", max_tokens=1, overrides=overrides
    )
    assert chain.candidates[0].model_ref.model_id == leader
    assert leader not in requirement.exclude_models


def test_excluding_more_leaders_than_exist_is_unavailable_not_a_wraparound():
    with pytest.raises(ModelUnavailable):
        resolve_chain(
            [], profile="deep_review", max_tokens=1,
            overrides=RequirementOverrides(exclude_leaders=4),
        )


@pytest.mark.parametrize("bad", [-1, True, 1.5, "2"])
def test_exclude_leaders_rejects_non_counts(bad):
    with pytest.raises((TypeError, ValueError)):
        RequirementOverrides(exclude_leaders=bad)


def test_allow_paid_given_twice_is_refused():
    with pytest.raises(ValueError, match="exactly one"):
        resolve_chain(
            [], profile="deep_review", max_tokens=1, allow_paid=True,
            overrides=RequirementOverrides(allow_paid=False),
        )
