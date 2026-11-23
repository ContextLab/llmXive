"""
Unit tests for the BenchmarkQuery schema definition.
"""

import pytest
from data.data.schema import BenchmarkQuery


def test_benchmark_query_creation():
    """Test basic creation of a BenchmarkQuery."""
    query = BenchmarkQuery(
        prompt="What is gravity?",
        ground_truth="Gravity is a fundamental interaction...",
        steps=["Define gravity", "Explain interaction"],
        seed=42,
        domain="physics"
    )

    assert query.prompt == "What is gravity?"
    assert query.ground_truth == "Gravity is a fundamental interaction..."
    assert query.steps == ["Define gravity", "Explain interaction"]
    assert query.seed == 42
    assert query.domain == "physics"


def test_benchmark_query_default_values():
    """Test that default values are applied correctly."""
    query = BenchmarkQuery(
        prompt="Simple prompt",
        ground_truth="Simple answer"
    )

    assert query.steps == []
    assert query.seed == 0
    assert query.domain == "general"


def test_benchmark_query_from_dict():
    """Test dictionary parsing."""
    data = {
        "prompt": "Test prompt",
        "ground_truth": "Test truth",
        "steps": ["step1", "step2"],
        "seed": 123,
        "domain": "biology"
    }

    query = BenchmarkQuery.from_dict(data)

    assert query.prompt == "Test prompt"
    assert query.ground_truth == "Test truth"
    assert query.steps == ["step1", "step2"]
    assert query.seed == 123
    assert query.domain == "biology"


def test_benchmark_query_from_dict_missing_fields():
    """Test that missing required fields raise errors."""
    data = {
        "prompt": "Test prompt"
        # Missing ground_truth
    }

    with pytest.raises(KeyError):
        BenchmarkQuery.from_dict(data)


def test_benchmark_query_to_dict():
    """Test conversion back to dictionary."""
    query = BenchmarkQuery(
        prompt="Prompt",
        ground_truth="Truth",
        steps=["s1"],
        seed=1,
        domain="chem"
    )

    data = query.to_dict()

    assert data["prompt"] == "Prompt"
    assert data["ground_truth"] == "Truth"
    assert data["steps"] == ["s1"]
    assert data["seed"] == 1
    assert data["domain"] == "chem"


def test_benchmark_query_to_json():
    """Test JSON serialization."""
    query = BenchmarkQuery(
        prompt="Prompt",
        ground_truth="Truth",
        steps=[],
        seed=0,
        domain="general"
    )

    json_str = query.to_json()

    assert "Prompt" in json_str
    assert "Truth" in json_str
    assert "general" in json_str