"""Unit tests for the synthetic query generator."""

import json
from pathlib import Path
import pytest

from generators.synthetic_query import SyntheticQueryGenerator
from validate_schemas import load_schema, validate_instance

def _schema_path(name: str) -> Path:
    """Helper to locate contract schemas."""
    return Path("specs") / "001-structural-mismatch-cost" / "contracts" / f"{name}.schema.yaml"

@pytest.fixture
def generator():
    """Generator with deterministic seed. 
    Note: This requires T003 raw data to be present on disk.
    """
    return SyntheticQueryGenerator(seed=123)

def test_generate_minimum_queries(generator):
    """Generate a small set and ensure basic shape and non-empty steps."""
    queries = generator.generate_queries(count=10)
    assert len(queries) == 10
    for q in queries:
        assert isinstance(q["query_id"], str)
        assert isinstance(q["source_type"], str)
        assert isinstance(q["complexity_level"], int)
        # Fix verification: logical_plan.steps must be non-empty (T004 requirement)
        assert q["logical_plan"]["steps"]
        assert len(q["logical_plan"]["steps"]) == q["complexity_level"]
        # Ground truth must be attached
        assert "ground_truth_plan" in q
        assert "plan_id" in q["ground_truth_plan"]

def test_generate_queries_even_distribution(generator):
    """Evenly distribute a custom count across levels."""
    count = 23
    queries = generator.generate_queries(count)
    assert len(queries) == count
    levels = [q["complexity_level"] for q in queries]
    min_expected = count // len(generator.complexity_levels)
    for lvl in generator.complexity_levels:
        assert levels.count(lvl) >= min_expected

def test_schema_validation(generator):
    """Validate a generated query against the JSON-Schema if it exists."""
    q = generator._create_query(2)
    schema_p = _schema_path("query_instance")
    if schema_p.is_file():
        schema = load_schema(schema_p)
        validate_instance(schema, q, "query_instance")
    else:
        pytest.skip("Schema file missing; skipping validation")

def test_save_and_load(generator, tmp_path):
    """Saving to disk produces valid JSON that can be re-loaded."""
    out_file = tmp_path / "queries.json"
    generator.save_queries(out_file, count=7)
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 7
    assert "logical_plan" in data[0]
    assert data[0]["logical_plan"]["steps"]