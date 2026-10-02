"""
Contract test for T009c: Validates that experiment log entries conform to the schema.
"""
import os
import sys
import yaml
import pytest
from jsonschema import validate, ValidationError

# Ensure code directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

SCHEMA_PATH = os.path.join("contracts", "experiment_log.schema.yaml")

@pytest.fixture
def schema():
    if not os.path.exists(SCHEMA_PATH):
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def test_valid_log_entry(schema):
    """Test that a valid log entry passes validation."""
    valid_entry = {
        "task_id": "T001",
        "skill_id": "SKILL_A",
        "success": True,
        "latency": 0.123,
        "tokens": 50,
        "retrieval_precision": 0.95,
        "retrieval_diversity": 1.5,
        "pruning_risk_count": 0,
        "library_size": 100,
        "pruning_enabled": False,
        "edge_case": False
    }
    validate(instance=valid_entry, schema=schema)

def test_edge_case_entry(schema):
    """Test that an edge case entry (maximal overlap) passes validation."""
    edge_entry = {
        "task_id": "T099",
        "skill_id": "SKILL_Z",
        "success": False,
        "latency": 1.2,
        "tokens": 200,
        "retrieval_precision": 0.0,
        "retrieval_diversity": 0.0,
        "pruning_risk_count": 5,
        "library_size": 100,
        "pruning_enabled": True,
        "edge_case": True
    }
    validate(instance=edge_entry, schema=schema)

def test_missing_required_field(schema):
    """Test that missing a required field raises ValidationError."""
    invalid_entry = {
        "task_id": "T001",
        "skill_id": "SKILL_A",
        # Missing 'success'
        "latency": 0.1,
        "tokens": 10,
        "retrieval_precision": 0.5,
        "retrieval_diversity": 1.0,
        "pruning_risk_count": 0,
        "library_size": 10,
        "pruning_enabled": False,
        "edge_case": False
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_entry, schema=schema)

def test_wrong_type_field(schema):
    """Test that wrong type for a field raises ValidationError."""
    invalid_entry = {
        "task_id": "T001",
        "skill_id": "SKILL_A",
        "success": "true",  # Should be boolean
        "latency": 0.1,
        "tokens": 10,
        "retrieval_precision": 0.5,
        "retrieval_diversity": 1.0,
        "pruning_risk_count": 0,
        "library_size": 10,
        "pruning_enabled": False,
        "edge_case": False
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_entry, schema=schema)

def test_additional_properties_rejected(schema):
    """Test that additional properties are rejected."""
    invalid_entry = {
        "task_id": "T001",
        "skill_id": "SKILL_A",
        "success": True,
        "latency": 0.1,
        "tokens": 10,
        "retrieval_precision": 0.5,
        "retrieval_diversity": 1.0,
        "pruning_risk_count": 0,
        "library_size": 10,
        "pruning_enabled": False,
        "edge_case": False,
        "extra_field": "should_fail"
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_entry, schema=schema)