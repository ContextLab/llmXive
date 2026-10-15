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
    """Generator with deterministic seed."""
    return SyntheticQueryGenerator(seed=123)


def test_generate_minimum_queries(generator):
    """Generate a small deterministic set and ensure basic shape."""
    queries = generator.generate()
    assert len(queries) == len(generator.complexity_levels) * generator.count_per_level
    for q in queries:
        assert isinstance(q["query_id"], str)
        assert isinstance(q["source_type"], str)
        assert isinstance(q["complexity_level"], int)
        # logical_plan.steps must be non‑empty
        assert q["logical_plan"]["steps"]
        # ground_truth_plan must be either a string or an object with steps
        gt = q["ground_truth_plan"]
        if isinstance(gt, dict):
            assert gt["steps"]  # non‑empty list


def test_generate_queries_even_distribution(generator):
    """Evenly distribute a custom count across levels."""
    count = 23
    queries = generator.generate_queries(count)
    assert len(queries) == count
    # Verify distribution logic (roughly even)
    levels = [q["complexity_level"] for q in queries]
    # Each level should appear at least floor(count/len(levels))
    min_expected = count // len(generator.complexity_levels)
    for lvl in generator.complexity_levels:
        assert levels.count(lvl) >= min_expected


def test_schema_validation(generator, tmp_path):
    """Validate a generated query against the JSON‑Schema."""
    q = generator._create_query(2)
    schema = load_schema(_schema_path("query_instance"))
    # Should not raise ValidationError
    validate_instance(schema, q, "query_instance")


def test_save_and_load(tmp_path):
    """Saving to disk produces valid JSON that can be re‑loaded."""
    gen = SyntheticQueryGenerator(seed=0)
    out_file = tmp_path / "queries.json"
    gen.save_queries(out_file, count=7)
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 7
    # Spot‑check first entry
    first = data[0]
    assert "query_id" in first
    assert "logical_plan" in first
    assert "ground_truth_plan" in first