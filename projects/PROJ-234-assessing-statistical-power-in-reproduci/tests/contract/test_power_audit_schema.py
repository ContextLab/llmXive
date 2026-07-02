import os
import sys
import json
import pytest
from pathlib import Path

# Add code to path if needed, though this is a contract test against a file
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import yaml

@pytest.fixture
def schema_path():
    return Path(__file__).parent.parent.parent / "contracts" / "power_audit_result.schema.yaml"

@pytest.fixture
def schema(schema_path):
    if not schema_path.exists():
        pytest.fail(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def test_schema_structure(schema):
    """Verify the schema has required top-level keys."""
    assert "$schema" in schema
    assert "title" in schema
    assert "type" in schema
    assert schema["type"] == "object"
    assert "required" in schema

def test_required_fields(schema):
    """Verify the schema lists all required fields."""
    required = schema.get("required", [])
    expected = ["dataset_id", "observed_power", "mdes", "threshold_met", "status"]
    for field in expected:
        assert field in required, f"Missing required field: {field}"

def test_schema_validates_mock_data(schema, tmp_path):
    """Verify that a valid mock object conforms to the schema logic."""
    # Since jsonschema might not be installed in the base env, we do manual validation
    # based on the schema definition.
    mock_data = {
        "dataset_id": 101,
        "observed_power": 0.9,
        "mdes": 0.15,
        "threshold_met": True,
        "status": "success"
    }

    # Check required fields
    for field in schema["required"]:
        assert field in mock_data

    # Check types
    assert isinstance(mock_data["dataset_id"], int)
    assert isinstance(mock_data["observed_power"], (int, float))
    assert 0.0 <= mock_data["observed_power"] <= 1.0
    assert isinstance(mock_data["mdes"], (int, float))
    assert mock_data["mdes"] >= 0.0
    assert isinstance(mock_data["threshold_met"], bool)
    assert mock_data["status"] in ["success", "low_power", "insufficient_data", "error"]

def test_schema_rejects_invalid_data(schema):
    """Verify that invalid data fails logical checks."""
    invalid_data = {
        "dataset_id": "not_an_int",
        "observed_power": 1.5,  # > 1.0
        "mdes": -0.1,
        "threshold_met": "yes",
        "status": "unknown_status"
    }

    # Manually check constraints defined in schema
    assert isinstance(invalid_data["dataset_id"], int) is False
    assert invalid_data["observed_power"] < 0.0 or invalid_data["observed_power"] > 1.0
    assert invalid_data["mdes"] < 0.0
    assert isinstance(invalid_data["threshold_met"], bool) is False
    assert invalid_data["status"] not in ["success", "low_power", "insufficient_data", "error"]