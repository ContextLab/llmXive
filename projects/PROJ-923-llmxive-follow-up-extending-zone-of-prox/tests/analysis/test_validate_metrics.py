"""
Tests for the metrics validation module.

These tests verify that the validation logic correctly identifies
compliant and non-compliant metrics data against the schema.
"""

import json
import yaml
import tempfile
import os
from pathlib import Path
import pytest

from analysis.validate_metrics import (
    load_schema,
    load_metrics_data,
    validate_metrics_against_schema,
    validate_aggregated_metrics_file
)


@pytest.fixture
def sample_schema():
    """Create a sample schema for testing."""
    return {
        "type": "object",
        "properties": {
            "baseline_aucc": {"type": "number"},
            "cap_aucc": {"type": "number"},
            "p_value": {"type": "number"},
            "effect_size": {"type": "number"},
            "runs_count": {"type": "integer"},
            "tasks": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["baseline_aucc", "cap_aucc", "p_value"]
    }


@pytest.fixture
def valid_metrics():
    """Create valid metrics data."""
    return {
        "baseline_aucc": 0.75,
        "cap_aucc": 0.82,
        "p_value": 0.03,
        "effect_size": 0.45,
        "runs_count": 100,
        "tasks": ["task1", "task2", "task3"]
    }


@pytest.fixture
def invalid_metrics_missing_required():
    """Create metrics missing required fields."""
    return {
        "baseline_aucc": 0.75,
        # Missing cap_aucc and p_value
    }


@pytest.fixture
def invalid_metrics_wrong_type():
    """Create metrics with wrong types."""
    return {
        "baseline_aucc": "not_a_number",
        "cap_aucc": 0.82,
        "p_value": 0.03
    }


def test_load_schema_from_yaml():
    """Test loading a schema from a YAML file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}}
        }
        yaml.dump(schema, f)
        f.flush()

        try:
            loaded = load_schema(f.name)
            assert loaded == schema
        finally:
            os.unlink(f.name)


def test_load_schema_from_json():
    """Test loading a schema from a JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}}
        }
        json.dump(schema, f)
        f.flush()

        try:
            loaded = load_schema(f.name)
            assert loaded == schema
        finally:
            os.unlink(f.name)


def test_load_schema_file_not_found():
    """Test that loading a non-existent schema raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_schema("/nonexistent/path/schema.yaml")


def test_load_metrics_valid():
    """Test loading valid metrics data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        metrics = {"baseline_aucc": 0.75, "cap_aucc": 0.82}
        json.dump(metrics, f)
        f.flush()

        try:
            loaded = load_metrics_data(f.name)
            assert loaded == metrics
        finally:
            os.unlink(f.name)


def test_load_metrics_file_not_found():
    """Test that loading non-existent metrics raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_metrics_data("/nonexistent/path/metrics.json")


def test_validate_metrics_against_schema_valid(sample_schema, valid_metrics):
    """Test validation of valid metrics against schema."""
    is_valid, errors = validate_metrics_against_schema(valid_metrics, sample_schema)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_metrics_missing_required(sample_schema, invalid_metrics_missing_required):
    """Test validation fails when required fields are missing."""
    is_valid, errors = validate_metrics_against_schema(
        invalid_metrics_missing_required,
        sample_schema
    )
    assert is_valid is False
    assert len(errors) > 0
    assert any("required" in err.lower() for err in errors)


def test_validate_metrics_wrong_type(sample_schema, invalid_metrics_wrong_type):
    """Test validation fails when types are incorrect."""
    is_valid, errors = validate_metrics_against_schema(
        invalid_metrics_wrong_type,
        sample_schema
    )
    assert is_valid is False
    assert len(errors) > 0
    assert any("number" in err.lower() for err in errors)


def test_validate_aggregated_metrics_file_valid(tmp_path, sample_schema, valid_metrics):
    """Test end-to-end validation with valid data."""
    # Create schema file
    schema_file = tmp_path / "schema.yaml"
    with open(schema_file, 'w') as f:
        yaml.dump(sample_schema, f)

    # Create metrics file
    metrics_file = tmp_path / "metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump(valid_metrics, f)

    is_valid, report = validate_aggregated_metrics_file(
        str(metrics_file),
        str(schema_file)
    )

    assert is_valid is True
    assert report["is_valid"] is True
    assert len(report["errors"]) == 0


def test_validate_aggregated_metrics_file_invalid(tmp_path, sample_schema, invalid_metrics_missing_required):
    """Test end-to-end validation with invalid data."""
    # Create schema file
    schema_file = tmp_path / "schema.yaml"
    with open(schema_file, 'w') as f:
        yaml.dump(sample_schema, f)

    # Create metrics file
    metrics_file = tmp_path / "metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump(invalid_metrics_missing_required, f)

    is_valid, report = validate_aggregated_metrics_file(
        str(metrics_file),
        str(schema_file)
    )

    assert is_valid is False
    assert report["is_valid"] is False
    assert len(report["errors"]) > 0
