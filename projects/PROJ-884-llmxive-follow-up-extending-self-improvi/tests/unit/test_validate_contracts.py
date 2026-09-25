"""
Unit tests for validate_data_against_contracts.py
"""
import json
import os
import sys
import pytest
from pathlib import Path
import tempfile
import yaml

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from dataset.validate_data_against_contracts import (
    load_schema,
    validate_puzzle_instance,
    validate_dataset,
    save_report
)

@pytest.fixture
def sample_schema():
    return {
        "type": "object",
        "required": ["constraints", "initial_state", "target_state", "verifier_output", "metadata"],
        "properties": {
            "constraints": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "initial_state": {"type": "object"},
            "target_state": {"type": "object"},
            "verifier_output": {
                "type": "object",
                "required": ["valid", "error_code"],
                "properties": {
                    "valid": {"type": "boolean"},
                    "error_code": {"type": "string"}
                }
            },
            "metadata": {
                "type": "object",
                "required": ["source_id", "generation_seed"],
                "properties": {
                    "source_id": {"type": "string"},
                    "generation_seed": {"type": "integer"}
                }
            }
        }
    }

@pytest.fixture
def valid_instance():
    return {
        "constraints": ["A > B", "C = D"],
        "initial_state": {"A": 1, "B": 2},
        "target_state": {"A": 5, "B": 5},
        "verifier_output": {"valid": True, "error_code": "NONE"},
        "metadata": {"source_id": "test_v1", "generation_seed": 42}
    }

@pytest.fixture
def invalid_instance_missing_field():
    return {
        "constraints": ["A > B"],
        "initial_state": {"A": 1},
        "target_state": {"A": 5},
        "verifier_output": {"valid": True, "error_code": "NONE"},
        # Missing metadata
    }

def test_validate_puzzle_instance_valid(valid_instance, sample_schema):
    errors = validate_puzzle_instance(valid_instance, sample_schema)
    assert len(errors) == 0

def test_validate_puzzle_instance_missing_required(valid_instance, sample_schema):
    # Remove a required field
    del valid_instance["metadata"]
    errors = validate_puzzle_instance(valid_instance, sample_schema)
    assert len(errors) > 0
    assert any("metadata" in e for e in errors)

def test_validate_puzzle_instance_invalid_types(valid_instance, sample_schema):
    # Make constraints a string instead of list
    valid_instance["constraints"] = "invalid"
    errors = validate_puzzle_instance(valid_instance, sample_schema)
    assert len(errors) > 0
    assert any("constraints" in e for e in errors)

def test_validate_dataset_valid(tmp_path, valid_instance, sample_schema):
    data_file = tmp_path / "test_data.json"
    with open(data_file, 'w') as f:
        json.dump([valid_instance], f)
    
    report = validate_dataset(data_file, sample_schema)
    assert report["valid"] is True
    assert report["valid_count"] == 1
    assert report["invalid_count"] == 0

def test_validate_dataset_invalid(tmp_path, valid_instance, sample_schema):
    # Create one valid and one invalid
    invalid_inst = dict(valid_instance)
    del invalid_inst["metadata"]
    
    data_file = tmp_path / "test_data_mixed.json"
    with open(data_file, 'w') as f:
        json.dump([valid_instance, invalid_inst], f)
    
    report = validate_dataset(data_file, sample_schema)
    assert report["valid"] is False
    assert report["valid_count"] == 1
    assert report["invalid_count"] == 1

def test_save_report(tmp_path, sample_schema):
    report = {"status": "ok", "data": [1, 2, 3]}
    output_file = tmp_path / "report.json"
    save_report(report, output_file)
    
    assert output_file.exists()
    with open(output_file, 'r') as f:
        loaded = json.load(f)
    assert loaded == report