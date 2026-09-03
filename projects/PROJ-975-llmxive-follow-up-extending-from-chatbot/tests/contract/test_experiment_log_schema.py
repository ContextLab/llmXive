"""
Contract test for T009c: Validate experiment_log.schema.yaml against sample data.
"""
import json
import os
import yaml
import pytest
from jsonschema import validate, ValidationError

SCHEMA_PATH = "contracts/experiment_log.schema.yaml"

def load_schema():
    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def test_schema_validates_sample_entry():
    """Verify that a valid sample log entry passes validation."""
    schema = load_schema()
    
    sample_entry = {
        "task_id": "task_001",
        "skill_id": "skill_42",
        "success": True,
        "latency": 0.45,
        "tokens": 120,
        "retrieval_precision": 0.85,
        "retrieval_diversity": 2.5,
        "pruning_risk_count": 0,
        "library_size": 50,
        "pruning_enabled": True,
        "edge_case": False
    }

    # This should not raise
    validate(instance=sample_entry, schema=schema)

def test_schema_rejects_missing_field():
    """Verify that missing required fields cause validation failure."""
    schema = load_schema()
    
    incomplete_entry = {
        "task_id": "task_001",
        # missing other required fields
    }

    with pytest.raises(ValidationError):
        validate(instance=incomplete_entry, schema=schema)

def test_schema_rejects_wrong_type():
    """Verify that type mismatches cause validation failure."""
    schema = load_schema()
    
    invalid_entry = {
        "task_id": "task_001",
        "skill_id": "skill_42",
        "success": "not_a_boolean",  # Should be boolean
        "latency": 0.45,
        "tokens": 120,
        "retrieval_precision": 0.85,
        "retrieval_diversity": 2.5,
        "pruning_risk_count": 0,
        "library_size": 50,
        "pruning_enabled": True,
        "edge_case": False
    }

    with pytest.raises(ValidationError):
        validate(instance=invalid_entry, schema=schema)

def test_schema_rejects_extra_field():
    """Verify that additional properties are rejected (additionalProperties: false)."""
    schema = load_schema()
    
    extra_field_entry = {
        "task_id": "task_001",
        "skill_id": "skill_42",
        "success": True,
        "latency": 0.45,
        "tokens": 120,
        "retrieval_precision": 0.85,
        "retrieval_diversity": 2.5,
        "pruning_risk_count": 0,
        "library_size": 50,
        "pruning_enabled": True,
        "edge_case": False,
        "unexpected_field": "should_fail"
    }

    with pytest.raises(ValidationError):
        validate(instance=extra_field_entry, schema=schema)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
