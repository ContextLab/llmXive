"""
Contract test for T009c: Verify experiment_log.schema.yaml validity.
Ensures that a sample log entry validates against the defined schema.
"""
import os
import yaml
import json
import pytest
from jsonschema import validate, ValidationError

SCHEMA_PATH = "contracts/experiment_log.schema.yaml"

@pytest.fixture
def schema():
    """Load the experiment log schema from disk."""
    if not os.path.exists(SCHEMA_PATH):
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def valid_sample_entry():
    """Provide a valid sample log entry matching the schema."""
    return {
        "task_id": "task_001",
        "skill_id": "skill_42",
        "success": True,
        "latency": 1.234,
        "tokens": 150,
        "retrieval_precision": 0.8,
        "retrieval_diversity": 0.05,
        "pruning_risk_count": 2,
        "library_size": 100,
        "pruning_enabled": True
    }

@pytest.fixture
def invalid_sample_entry_missing_field():
    """Provide an invalid entry missing a required field."""
    return {
        "task_id": "task_002",
        "skill_id": "skill_43",
        "success": False,
        "latency": 0.5,
        "tokens": 50,
        # Missing retrieval_precision, etc.
        "library_size": 50,
        "pruning_enabled": False
    }

@pytest.fixture
def invalid_sample_entry_type_mismatch():
    """Provide an invalid entry with wrong data types."""
    return {
        "task_id": "task_003",
        "skill_id": "skill_44",
        "success": "yes",  # Should be boolean
        "latency": "fast", # Should be number
        "tokens": 100,
        "retrieval_precision": 0.5,
        "retrieval_diversity": 0.1,
        "pruning_risk_count": 0,
        "library_size": 100,
        "pruning_enabled": True
    }

def test_schema_loads(schema):
    """Verify the schema file is valid YAML and loads correctly."""
    assert schema is not None
    assert schema["type"] == "object"
    assert "properties" in schema

def test_valid_entry_passes_validation(schema, valid_sample_entry):
    """Verify a valid entry passes jsonschema.validate."""
    try:
        validate(instance=valid_sample_entry, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Valid entry failed validation: {e.message}")

def test_missing_required_field_fails(schema, invalid_sample_entry_missing_field):
    """Verify an entry missing required fields fails validation."""
    with pytest.raises(ValidationError):
        validate(instance=invalid_sample_entry_missing_field, schema=schema)

def test_type_mismatch_fails(schema, invalid_sample_entry_type_mismatch):
    """Verify an entry with wrong types fails validation."""
    with pytest.raises(ValidationError):
        validate(instance=invalid_sample_entry_type_mismatch, schema=schema)

def test_boundary_values(schema):
    """Verify boundary values (0.0, 1.0, negative) are handled correctly."""
    # Valid boundary
    valid_boundary = {
        "task_id": "t", "skill_id": "s", "success": True, "latency": 0.0,
        "tokens": 0, "retrieval_precision": 0.0, "retrieval_diversity": 0.0,
        "pruning_risk_count": 0, "library_size": 1, "pruning_enabled": False
    }
    validate(instance=valid_boundary, schema=schema)

    # Invalid: negative precision
    invalid_boundary = valid_boundary.copy()
    invalid_boundary["retrieval_precision"] = -0.1
    with pytest.raises(ValidationError):
        validate(instance=invalid_boundary, schema=schema)

    # Invalid: precision > 1.0
    invalid_boundary["retrieval_precision"] = 1.1
    with pytest.raises(ValidationError):
        validate(instance=invalid_boundary, schema=schema)