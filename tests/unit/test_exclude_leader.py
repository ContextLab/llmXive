"""exclude_leader: the tier-1 'free second opinion' rung without a model id."""
from __future__ import annotations

from dataclasses import replace

import pytest

from llmxive.model_selection.profiles import build_requirement
from llmxive.model_selection.select import select
from llmxive.model_selection.types import CallBudget, ModelUnavailable, RequirementOverrides
from llmxive.state import execution_status as es

# Import the existing fixed-snapshot helper rather than rebuilding one.
from tests.unit.test_model_selection_select import _snapshot  # noqa: E402

_CB = CallBudget(max_input_tokens=1000, max_output_tokens=500)


def _leader(chain):
    return chain.candidates[0].model_ref.model_id


def test_exclude_leader_drops_rank_one_only():
    snap = _snapshot()
    base = build_requirement("standard_generation", _CB)
    full = select(base, snap)
    assert _leader(full) == "qwen.qwen3.5-122b"

    narrowed = replace(base, exclude_models=base.exclude_models | {_leader(full)})
    second = select(narrowed, snap)
    assert _leader(second) == "google.gemma-4-31B-it"
    # every OTHER candidate from the full chain survives, in order
    assert [c.model_ref.model_id for c in second.candidates] == [
        c.model_ref.model_id for c in full.candidates if c.model_ref.model_id != _leader(full)
    ]


def test_tier_constraint_carries_exclude_leader_not_a_model_id():
    rung = es.TierConstraint(allow_paid=False, exclude_leader=True)
    ov = rung.to_overrides()          # NO default_model argument
    assert ov.exclude_leader is True
    assert ov.exclude_models == frozenset()   # no model id smuggled in


def test_tier_overrides_needs_no_default_model(tmp_path):
    pid = "PROJ-001-x"
    ov0 = es.tier_overrides(pid, repo_root=tmp_path)   # tier 0
    assert ov0.exclude_leader is False
    es.bump_model_tier(pid, repo_root=tmp_path)
    ov1 = es.tier_overrides(pid, repo_root=tmp_path)   # tier 1
    assert ov1.exclude_leader is True
    assert ov1.exclude_models == frozenset()


def test_exclude_leader_composes_with_existing_exclusions():
    snap = _snapshot()
    base = build_requirement("standard_generation", _CB,
                             exclude_models=frozenset({"google.gemma-4-31B-it"}))
    full = select(base, snap)
    assert _leader(full) == "qwen.qwen3.5-122b"
    narrowed = replace(base, exclude_models=base.exclude_models | {_leader(full)})
    assert _leader(select(narrowed, snap)) == "openai.gpt-oss-120b"


def test_pass_one_model_unavailable_propagates_immediately():
    """When pass 1 finds nothing eligible, ModelUnavailable propagates and pass 2
    is NEVER invoked (there is no leader to exclude)."""
    snap = _snapshot()
    impossible = build_requirement(
        "standard_generation", _CB,
        exclude_models=frozenset({
            "qwen.qwen3.5-122b", "google.gemma-4-31B-it", "openai.gpt-oss-120b",
            "anthropic.claude-haiku-4-5-20251001", "Qwen/Qwen2.5-3B-Instruct",
        }),
    )
    with pytest.raises(ModelUnavailable):
        select(impossible, snap)
