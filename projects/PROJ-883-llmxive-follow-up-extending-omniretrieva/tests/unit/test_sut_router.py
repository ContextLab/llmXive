"""Unit tests for the unified router (sut_router)."""

import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths

# Import the router's internal helper for plan generation.
from code.router.sut_router import _generate_sut_plan

@pytest.fixture
def sample_queries(tmp_path: Path):
    """Create a minimal generation_log.json file for testing."""
    queries = [
        {
            "query_id": "q_1_001",
            "source_type": "text",
            "complexity_level": 1,
            "logical_plan": {"steps": []},
        },
        {
            "query_id": "q_2_002",
            "source_type": "relational",
            "complexity_level": 3,
            "logical_plan": {"steps": []},
        },
        {
            "query_id": "q_3_003",
            "source_type": "graph",
            "complexity_level": 2,
            "logical_plan": {"steps": []},
        },
    ]
    file_path = tmp_path / "generation_log.json"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(queries, f, indent=2)
    return file_path

def test_generate_sut_plan_text():
    query = {
        "source_type": "text",
        "complexity_level": 2,
    }
    plan = _generate_sut_plan(query)
    assert plan["estimated_cost"] == 2  # base_cost 1 * complexity 2
    assert plan["steps"] == ["retrieve_text", "retrieve_text"]

def test_generate_sut_plan_unknown_source():
    query = {
        "source_type": "unknown_source",
        "complexity_level": 1,
    }
    plan = _generate_sut_plan(query)
    assert plan["estimated_cost"] == 1
    assert plan["steps"] == ["generic_operation"]

def test_router_enriches_file(tmp_path: Path, sample_queries: Path):
    """Run the router on a temporary file and verify ``sut_plan`` added."""
    from code.router import sut_router

    # Run the main function with the temporary paths.
    args = ["--input", str(sample_queries), "--output", str(sample_queries)]
    # Simulate CLI invocation
    parser = sut_router._parse_args
    # monkey‑patch sys.argv is avoided; directly call main after setting args
    # using argparse's parse_args with a custom list.
    import sys
    original_argv = sys.argv
    sys.argv = ["sut_router.py"] + args
    try:
        sut_router.main()
    finally:
        sys.argv = original_argv

    # Load the file and check that each entry now contains ``sut_plan``.
    with open(sample_queries, "r", encoding="utf-8") as f:
        enriched = json.load(f)

    assert isinstance(enriched, list)
    for entry in enriched:
        assert "sut_plan" in entry
        # Basic sanity checks on the plan structure
        plan = entry["sut_plan"]
        assert "estimated_cost" in plan
        assert "steps" in plan
        assert isinstance(plan["steps"], list)
        # The number of steps should equal the declared complexity level
        assert len(plan["steps"]) == int(entry["complexity_level"])