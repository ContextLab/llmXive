"""
Unit tests for T020: Schema validation logic.
"""
import csv
import json
import tempfile
import os
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validate_network_metrics_schema import validate_row, VALID_FLAGS, REQUIRED_FIELDS

def test_validate_row_missing_required():
    """Test that missing required fields are caught."""
    schema = {"required": REQUIRED_FIELDS}
    row = {"subject_id": "123", "age": 30} # Missing many fields
    errors = validate_row(row, schema, 1)
    
    assert len(errors) > 0
    assert any("Missing or empty required field" in e for e in errors)

def test_validate_row_valid():
    """Test that a valid row passes."""
    schema = {"required": REQUIRED_FIELDS}
    row = {
        "subject_id": "123",
        "age": 30,
        "global_efficiency": 0.5,
        "local_efficiency": 0.4,
        "characteristic_path_length": 2.0,
        "clustering_coefficient": 0.3,
        "modularity": 0.4,
        "signal_quality_flag": "High Signal Quality",
        "trace_id": "abc123"
    }
    errors = validate_row(row, schema, 1)
    assert len(errors) == 0

def test_validate_row_invalid_flag():
    """Test that invalid signal quality flag is caught."""
    schema = {"required": REQUIRED_FIELDS, "properties": {"signal_quality_flag": {"enum": VALID_FLAGS}}}
    row = {
        "subject_id": "123",
        "age": 30,
        "global_efficiency": 0.5,
        "local_efficiency": 0.4,
        "characteristic_path_length": 2.0,
        "clustering_coefficient": 0.3,
        "modularity": 0.4,
        "signal_quality_flag": "Bad Flag",
        "trace_id": "abc123"
    }
    errors = validate_row(row, schema, 1)
    assert len(errors) == 1
    assert "Invalid signal_quality_flag" in errors[0]

def test_validate_row_non_numeric():
    """Test that non-numeric values in numeric fields are caught."""
    schema = {"required": REQUIRED_FIELDS}
    row = {
        "subject_id": "123",
        "age": "not_a_number",
        "global_efficiency": 0.5,
        "local_efficiency": 0.4,
        "characteristic_path_length": 2.0,
        "clustering_coefficient": 0.3,
        "modularity": 0.4,
        "signal_quality_flag": "High Signal Quality",
        "trace_id": "abc123"
    }
    errors = validate_row(row, schema, 1)
    assert len(errors) == 1
    assert "is not a valid number" in errors[0]

def test_validate_row_empty_string():
    """Test that empty strings in required fields are caught."""
    schema = {"required": REQUIRED_FIELDS}
    row = {
        "subject_id": "",
        "age": 30,
        "global_efficiency": 0.5,
        "local_efficiency": 0.4,
        "characteristic_path_length": 2.0,
        "clustering_coefficient": 0.3,
        "modularity": 0.4,
        "signal_quality_flag": "High Signal Quality",
        "trace_id": "abc123"
    }
    errors = validate_row(row, schema, 1)
    assert len(errors) > 0
    assert any("Missing or empty" in e for e in errors)

if __name__ == "__main__":
    test_validate_row_missing_required()
    test_validate_row_valid()
    test_validate_row_invalid_flag()
    test_validate_row_non_numeric()
    test_validate_row_empty_string()
    print("All unit tests passed.")