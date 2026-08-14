"""
Unit tests for schema validation logic (Task T033).
"""

import json
import os
import tempfile
import pytest
import yaml

# Import the function being tested
from validation import run_schema_validation, save_validation_report

def test_valid_data():
    """Test that valid data passes validation."""
    schema = {
        "required_fields": ["participant_id", "condition"],
        "field_types": {
            "participant_id": "string",
            "condition": "string",
            "time_spent": "float"
        },
        "optional_fields": ["notes"]
    }
    data = [
        {"participant_id": "P001", "condition": "llm", "time_spent": 120.5},
        {"participant_id": "P002", "condition": "human", "time_spent": 90.0}
    ]
    
    is_valid, report = run_schema_validation(data, schema)
    
    assert is_valid is True
    assert len(report["errors"]) == 0
    assert report["record_count"] == 2

def test_missing_required_field():
    """Test that missing required fields are caught."""
    schema = {
        "required_fields": ["participant_id", "condition"],
        "field_types": {}
    }
    data = [
        {"participant_id": "P001"},  # Missing 'condition'
        {"participant_id": "P002", "condition": "llm"}
    ]
    
    is_valid, report = run_schema_validation(data, schema)
    
    assert is_valid is False
    assert any("Missing required field 'condition'" in err for err in report["errors"])

def test_type_mismatch():
    """Test that type mismatches are caught."""
    schema = {
        "required_fields": ["participant_id"],
        "field_types": {
            "participant_id": "string",
            "score": "integer"
        }
    }
    data = [
        {"participant_id": 123, "score": "high"},  # Both wrong types
        {"participant_id": "P001", "score": 10}
    ]
    
    is_valid, report = run_schema_validation(data, schema)
    
    assert is_valid is False
    assert len(report["errors"]) == 2
    assert any("must be string" in err for err in report["errors"])
    assert any("must be integer" in err for err in report["errors"])

def test_non_list_root():
    """Test that non-list root data fails."""
    schema = {"required_fields": []}
    data = {"not": "a list"}
    
    is_valid, report = run_schema_validation(data, schema)
    
    assert is_valid is False
    assert "Root element must be a list" in report["errors"][0]

def test_save_validation_report():
    """Test that the report is saved correctly."""
    report = {"valid": True, "errors": [], "warnings": []}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        save_validation_report(report, temp_path)
        assert os.path.exists(temp_path)
        with open(temp_path, 'r') as f:
            loaded = json.load(f)
        assert loaded == report
    finally:
        os.unlink(temp_path)