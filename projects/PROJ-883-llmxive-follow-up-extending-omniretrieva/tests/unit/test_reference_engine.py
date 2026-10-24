"""Unit tests for the deterministic greedy ReferenceEngine.

The tests verify that:
1. Steps are ordered according to the greedy rule (lowest cost first,
   ties broken by original depth).
2. The generated identifier follows the required format
   ``greedy_plan_<8‑hex‑hash>`` and matches the expected hash for a known
   query.
"""
import re
import hashlib

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


def _expected_hash(query_id: str, ordered_step_ids: list[str]) -> str:
    """Compute the 8‑hex hash used by ReferenceEngine."""
    concatenated = "_".join([query_id] + ordered_step_ids)
    return hashlib.sha256(concatenated.encode("utf-8")).hexdigest()[:8]


def test_generate_plan_respects_cost_and_depth(sample_query):
    """Engine should order steps by cost, breaking ties by original depth."""
    engine = ReferenceEngine()
    plan = engine.generate_plan(sample_query)

    # Expected ordering: B (cost 3, depth 1), C (cost 3, depth 2), A (cost 5)
    expected_order = ["B", "C", "A"]
    expected_hash = _expected_hash(sample_query["query_id"], expected_order)
    expected_plan = f"greedy_plan_{expected_hash}"

    assert plan == expected_plan
    assert re.fullmatch(r"greedy_plan_[0-9a-f]{8}", plan)


def test_generate_plan_without_steps():
    """When no steps are provided, the hash is derived only from the query_id."""
    engine = ReferenceEngine()
    query = {"query_id": "999"}
    plan = engine.generate_plan(query)

    expected_hash = _expected_hash("999", [])
    expected_plan = f"greedy_plan_{expected_hash}"

    assert plan == expected_plan
    assert re.fullmatch(r"greedy_plan_[0-9a-f]{8}", plan)