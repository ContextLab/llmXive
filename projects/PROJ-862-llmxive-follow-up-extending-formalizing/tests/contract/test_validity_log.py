"""
Contract test for validity log schema (T019).

This test verifies that the validity log produced by the pipeline
adheres to the schema defined in specs/001-lm-axive-noise-injection/contracts/validity-log.schema.yaml.

It ensures:
1. The output file exists at the expected path.
2. All required columns defined in the schema are present.
3. Data types match the schema definitions.
4. No null values exist in required fields.
"""

import os
import json
import csv
import pytest
from pathlib import Path
from typing import Dict, Any, List

# Project root relative to tests
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-lm-axive-noise-injection" / "contracts" / "validity-log.schema.yaml"
VALIDITY_LOG_PATH = PROJECT_ROOT / "data" / "processed" / "validity_log.csv"

def load_schema() -> Dict[str, Any]:
    """Load the validity log schema from YAML."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    
    import yaml
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def load_validity_log() -> List[Dict[str, Any]]:
    """Load the validity log CSV into a list of dictionaries."""
    if not VALIDITY_LOG_PATH.exists():
        pytest.fail(f"Validity log file not found: {VALIDITY_LOG_PATH}. "
                    "Ensure the pipeline has been run to generate this file.")
    
    rows = []
    with open(VALIDITY_LOG_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def test_schema_file_exists():
    """Verify the schema definition file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"

def test_required_columns_present():
    """Verify all required columns from the schema exist in the log."""
    schema = load_schema()
    required_fields = schema.get("required_fields", [])
    
    if not required_fields:
        pytest.fail("Schema 'required_fields' is empty or missing.")
    
    log_data = load_validity_log()
    if not log_data:
        pytest.fail("Validity log is empty. No rows to validate.")
    
    actual_columns = set(log_data[0].keys())
    missing_columns = set(required_fields) - actual_columns
    
    assert not missing_columns, (
        f"Missing required columns in validity log: {missing_columns}. "
        f"Expected: {required_fields}, Found: {list(actual_columns)}"
    )

def test_column_data_types():
    """Verify data types match the schema definitions."""
    schema = load_schema()
    field_types = schema.get("field_types", {})
    
    log_data = load_validity_log()
    if not log_data:
        pytest.fail("Validity log is empty. Cannot validate data types.")
    
    for row_idx, row in enumerate(log_data):
        for field, expected_type in field_types.items():
            if field not in row:
                continue  # Skip if optional and missing
            
            value = row[field]
            
            # Type validation logic based on schema type strings
            if expected_type == "integer":
                try:
                    int(value)
                except ValueError:
                    pytest.fail(f"Row {row_idx}, column '{field}': Expected integer, got '{value}'")
            
            elif expected_type == "float":
                try:
                    float(value)
                except ValueError:
                    pytest.fail(f"Row {row_idx}, column '{field}': Expected float, got '{value}'")
            
            elif expected_type == "boolean":
                if value.lower() not in ('true', 'false', '1', '0'):
                    pytest.fail(f"Row {row_idx}, column '{field}': Expected boolean, got '{value}'")
            
            elif expected_type == "string":
                if not isinstance(value, str):
                    pytest.fail(f"Row {row_idx}, column '{field}': Expected string, got type {type(value)}")

def test_required_fields_not_null():
    """Verify that required fields do not contain null/empty values."""
    schema = load_schema()
    required_fields = schema.get("required_fields", [])
    
    log_data = load_validity_log()
    if not log_data:
        pytest.fail("Validity log is empty.")
    
    for row_idx, row in enumerate(log_data):
        for field in required_fields:
            value = row.get(field, "")
            if value is None or value.strip() == "":
                pytest.fail(f"Row {row_idx}, column '{field}': Required field is null or empty.")

def test_validity_log_structure():
    """Comprehensive check of the validity log structure."""
    schema = load_schema()
    log_data = load_validity_log()
    
    if not log_data:
        pytest.fail("Validity log is empty.")
    
    # Check that the file is not empty and has a header
    assert len(log_data) > 0, "Validity log contains no data rows."
    
    # Verify the schema description matches expected purpose
    assert schema.get("description", "").lower().find("validity") != -1, (
        "Schema description does not indicate it is for a validity log."
    )