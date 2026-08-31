"""
Contract test for T009c: Validate experiment_log.schema.yaml.

This test ensures that the schema defined in contracts/experiment_log.schema.yaml
is valid JSON Schema and that a sample log entry conforms to it.
"""
import os
import json
import pytest
import yaml
from jsonschema import validate, ValidationError

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'contracts', 'experiment_log.schema.yaml')
SAMPLE_ENTRY = {
    "task_id": "T-001",
    "skill_id": "S-104",
    "success": True,
    "latency": 0.45,
    "tokens": 128,
    "retrieval_precision": 0.8,
    "retrieval_diversity": 2.5,
    "pruning_risk_count": 0,
    "library_size": 100,
    "pruning_enabled": True
}

def test_schema_file_exists():
    """Verify the schema file exists on disk."""
    assert os.path.exists(SCHEMA_PATH), f"Schema file not found at {SCHEMA_PATH}"

def test_schema_is_valid_json_schema():
    """Verify the YAML file parses correctly and is a valid JSON Schema object."""
    with open(SCHEMA_PATH, 'r') as f:
        schema = yaml.safe_load(f)
    
    assert isinstance(schema, dict), "Schema must be a dictionary"
    assert "$schema" in schema, "Schema must define $schema"
    assert "properties" in schema, "Schema must define properties"
    assert "required" in schema, "Schema must define required fields"

def test_sample_entry_validates_against_schema():
    """Verify a sample log entry validates successfully."""
    with open(SCHEMA_PATH, 'r') as f:
        schema = yaml.safe_load(f)
    
    try:
        validate(instance=SAMPLE_ENTRY, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Sample entry failed validation: {e.message}")

def test_missing_required_field_fails():
    """Verify that removing a required field causes validation to fail."""
    with open(SCHEMA_PATH, 'r') as f:
        schema = yaml.safe_load(f)
    
    invalid_entry = SAMPLE_ENTRY.copy()
    del invalid_entry["task_id"]
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_entry, schema=schema)

def test_wrong_type_fails():
    """Verify that providing a wrong type for a field causes validation to fail."""
    with open(SCHEMA_PATH, 'r') as f:
        schema = yaml.safe_load(f)
    
    invalid_entry = SAMPLE_ENTRY.copy()
    invalid_entry["success"] = "true"  # Should be boolean
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_entry, schema=schema)