"""
Unit tests for the fork_point.schema.yaml schema validation.
Verifies that the schema correctly defines the output structure for fork-point genes.
"""
import json
import os
import yaml
import pytest
from pathlib import Path

# Import jsonschema for validation
try:
    import jsonschema
except ImportError:
    pytest.skip("jsonschema not installed", allow_module_level=True)


@pytest.fixture
def schema_path():
    """Return the path to the fork_point.schema.yaml file."""
    return Path(__file__).parent.parent.parent / "contracts" / "fork_point.schema.yaml"


@pytest.fixture
def schema(schema_path):
    """Load the schema from the YAML file."""
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def test_schema_exists(schema_path):
    """Assert that the schema file exists."""
    assert schema_path.exists(), f"Schema file not found at {schema_path}"


def test_schema_is_valid_yaml(schema):
    """Assert that the schema is valid YAML and loads correctly."""
    assert isinstance(schema, dict), "Schema should be a dictionary"
    assert "$schema" in schema, "Schema must include $schema field"
    assert "title" in schema, "Schema must include title field"


def test_schema_has_required_top_level_fields(schema):
    """Assert that the schema has required top-level fields."""
    assert "type" in schema, "Schema must define type"
    assert schema["type"] == "object", "Schema root must be an object"
    assert "required" in schema, "Schema must define required fields"
    assert "fork_points" in schema["required"], "fork_points must be required"


def test_valid_fork_point_data(schema):
    """Test that valid fork point data passes schema validation."""
    valid_data = {
        "fork_points": [
            {
                "branch_id": "GSE136103_branch_1",
                "divergence_score": 2.5,
                "genes": [
                    {
                        "gene_symbol": "CD38",
                        "timing_rank": 1,
                        "timing_pseudotime": 0.15,
                        "confidence_flag": "high_confidence"
                    },
                    {
                        "gene_symbol": "TCF7",
                        "timing_rank": 2,
                        "timing_pseudotime": 0.25,
                        "confidence_flag": "high_confidence"
                    }
                ]
            }
        ]
    }
    jsonschema.validate(instance=valid_data, schema=schema)


def test_low_confidence_flag(schema):
    """Test that low_confidence flag is accepted for divergence < 2.0."""
    data = {
        "fork_points": [
            {
                "branch_id": "GSE127465_branch_2",
                "divergence_score": 1.8,
                "genes": [
                    {
                        "gene_symbol": "NOTCH1",
                        "timing_rank": 1,
                        "timing_pseudotime": 0.12,
                        "confidence_flag": "low_confidence"
                    }
                ]
            }
        ]
    }
    jsonschema.validate(instance=data, schema=schema)


def test_invalid_branch_id_format(schema):
    """Test that invalid branch_id format raises validation error."""
    invalid_data = {
        "fork_points": [
            {
                "branch_id": "invalid_format",
                "divergence_score": 2.1,
                "genes": [
                    {
                        "gene_symbol": "CD38",
                        "timing_rank": 1,
                        "timing_pseudotime": 0.1,
                        "confidence_flag": "high_confidence"
                    }
                ]
            }
        ]
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_data, schema=schema)


def test_missing_required_field(schema):
    """Test that missing required field raises validation error."""
    invalid_data = {
        "fork_points": [
            {
                "branch_id": "GSE136103_branch_1",
                "divergence_score": 2.5,
                # Missing 'genes' field
            }
        ]
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_data, schema=schema)


def test_invalid_confidence_flag(schema):
    """Test that invalid confidence_flag raises validation error."""
    invalid_data = {
        "fork_points": [
            {
                "branch_id": "GSE136103_branch_1",
                "divergence_score": 2.5,
                "genes": [
                    {
                        "gene_symbol": "CD38",
                        "timing_rank": 1,
                        "timing_pseudotime": 0.1,
                        "confidence_flag": "invalid_flag"
                    }
                ]
            }
        ]
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_data, schema=schema)


def test_timing_rank_minimum(schema):
    """Test that timing_rank must be >= 1."""
    invalid_data = {
        "fork_points": [
            {
                "branch_id": "GSE136103_branch_1",
                "divergence_score": 2.5,
                "genes": [
                    {
                        "gene_symbol": "CD38",
                        "timing_rank": 0,
                        "timing_pseudotime": 0.1,
                        "confidence_flag": "high_confidence"
                    }
                ]
            }
        ]
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_data, schema=schema)


def test_divergence_score_minimum(schema):
    """Test that divergence_score must be >= 0."""
    invalid_data = {
        "fork_points": [
            {
                "branch_id": "GSE136103_branch_1",
                "divergence_score": -1.0,
                "genes": [
                    {
                        "gene_symbol": "CD38",
                        "timing_rank": 1,
                        "timing_pseudotime": 0.1,
                        "confidence_flag": "high_confidence"
                    }
                ]
            }
        ]
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_data, schema=schema)