"""Unit tests for the deterministic greedy ReferenceEngine."""

import pytest
from generators.reference_engine import ReferenceEngine


@pytest.fixture
def sample_query():
    """A query with three steps where two have identical costs."""
    return {
        "query_id": "123",
        "steps": [
            {"step_id": "A", "estimated_cost": 5.0},
            {"step_id": "B", "estimated_cost": 3.0},
            {"step_id": "C", "estimated_cost": 3.0},
        ],
    }


def test_generate_plan_respects_cost_and_depth(sample_query):
    """The engine should pick the lowest cost step first; ties resolved by depth."""
    engine = ReferenceEngine()
    plan = engine.generate_plan(sample_query)

    # Expected order: B (cost 3, depth 1) then C (cost 3, depth 2) then A (cost 5)
    expected_plan = "gt_plan_123_B_C_A"
    assert plan == expected_plan, f"Expected {expected_plan}, got {plan}"


def test_generate_plan_without_steps():
    """When no steps are provided, fallback to simple deterministic ID."""
    engine = ReferenceEngine()
    query = {"query_id": "999"}
    plan = engine.generate_plan(query)
    assert plan == "gt_plan_999"