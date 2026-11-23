"""
Unit tests for the validate_data_against_contracts module.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import yaml

# Import the module under test
# Adjust import path based on how the module is structured
try:
    from code.dataset.validate_data_against_contracts import (
        load_schema,
        validate_puzzle_instance,
        validate_dataset,
        save_report
    )
except ImportError:
    from dataset.validate_data_against_contracts import (
        load_schema,
        validate_puzzle_instance,
        validate_dataset,
        save_report
    )

@pytest.fixture
def valid_schema():
    return {
        "type": "object",
        "required": ["constraints", "initial_state", "target_state", "verifier_output", "metadata"]
    }

@pytest.fixture
def valid_instance():
    return {
        "constraints": ["row 1 sum to 10", "col 1 sum to 10"],
        "initial_state": {"grid": [[0,0,0]]},
        "target_state": {"grid": [[1,2,3]]},
        "verifier_output": {"valid": True, "error_code": "OK"},
        "metadata": {"source_id": "test", "generation_seed": 123}
    }

@pytest.fixture
def invalid_instance_missing_field():
    return {
        "constraints": ["row 1 sum to 10"],
        # missing initial_state
        "target_state": {"grid": [[1,2,3]]},
        "verifier_output": {"valid": True, "error_code": "OK"},
        "metadata": {"source_id": "test", "generation_seed": 123}
    }

@pytest.fixture
def invalid_instance_wrong_type():
    return {
        "constraints": "not an array", # Should be list
        "initial_state": {"grid": [[0,0,0]]},
        "target_state": {"grid": [[1,2,3]]},
        "verifier_output": {"valid": True, "error_code": "OK"},
        "metadata": {"source_id": "test", "generation_seed": 123}
    }

def test_validate_puzzle_instance_valid(valid_instance, valid_schema):
    errors = validate_puzzle_instance(valid_instance, valid_schema)
    assert len(errors) == 0

def test_validate_puzzle_instance_missing_field(invalid_instance_missing_field, valid_schema):
    errors = validate_puzzle_instance(invalid_instance_missing_field, valid_schema)
    assert len(errors) > 0
    assert any("Missing required key: initial_state" in e for e in errors)

def test_validate_puzzle_instance_wrong_type(invalid_instance_wrong_type, valid_schema):
    errors = validate_puzzle_instance(invalid_instance_wrong_type, valid_schema)
    assert len(errors) > 0
    assert any("'constraints' must be an array" in e for e in errors)

def test_validate_dataset_valid(tmp_path):
    # Create a temporary schema file
    schema_path = tmp_path / "schema.yaml"
    schema = {"type": "object"}
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f)

    # Create a temporary data file
    data_path = tmp_path / "data.json"
    data = [
        {
            "constraints": ["a"],
            "initial_state": {},
            "target_state": {},
            "verifier_output": {"valid": True, "error_code": "OK"},
            "metadata": {"source_id": "s", "generation_seed": 1}
        }
    ]
    with open(data_path, 'w') as f:
        json.dump(data, f)

    report = validate_dataset(data_path, schema)
    assert report["is_valid"] is True
    assert report["valid_count"] == 1
    assert report["invalid_count"] == 0

def test_validate_dataset_invalid(tmp_path):
    # Create a temporary schema file
    schema_path = tmp_path / "schema.yaml"
    schema = {"type": "object"}
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f)

    # Create a temporary data file with invalid item
    data_path = tmp_path / "data.json"
    data = [
        {
            "constraints": "string", # Invalid
            "initial_state": {},
            "target_state": {},
            "verifier_output": {"valid": True, "error_code": "OK"},
            "metadata": {"source_id": "s", "generation_seed": 1}
        }
    ]
    with open(data_path, 'w') as f:
        json.dump(data, f)

    report = validate_dataset(data_path, schema)
    assert report["is_valid"] is False
    assert report["valid_count"] == 0
    assert report["invalid_count"] == 1

def test_save_report(tmp_path):
    report = {
        "is_valid": True,
        "total_count": 1,
        "valid_count": 1,
        "invalid_count": 0,
        "invalid_indices": [],
        "error_details": [],
        "schema_path": "test.yaml",
        "data_path": "test.json",
        "validation_timestamp": "2023-01-01T00:00:00Z"
    }
    output_path = tmp_path / "report.json"
    save_report(report, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        saved_report = json.load(f)
    
    assert saved_report["is_valid"] is True
    assert saved_report["total_count"] == 1
