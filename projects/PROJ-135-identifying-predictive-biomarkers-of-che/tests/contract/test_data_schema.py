"""
Contract test for data schema validation.

This task verifies that `dataset.schema.yaml` (output of T006) is valid.
It implements the following logic:
1. Try to load `dataset.schema.yaml`.
2. If FileNotFoundError, raise an explicit error stating T006 must run first.
3. Validate a synthetic sample conforming to the schema.
4. Assert that schema validation passes for valid data and fails for invalid data.
"""

import os
import sys
import json
import yaml
from pathlib import Path
import pytest

# Import project utilities if available, otherwise define local helpers
try:
    from src.config import get_project_root
except ImportError:
    def get_project_root():
        """Fallback to current working directory if config is not available."""
        return Path.cwd()

SCHEMA_FILE_NAME = "dataset.schema.yaml"
SCHEMAS_DIR = "specs/001-chemo-biomarker-discovery/contracts"

def get_schema_path():
    """Construct the full path to the dataset schema file."""
    root = get_project_root()
    return root / SCHEMAS_DIR / SCHEMA_FILE_NAME

def load_schema():
    """
    Load the dataset schema from disk.
    
    Raises:
        FileNotFoundError: If the schema file does not exist (T006 not run).
        yaml.YAMLError: If the schema file is invalid YAML.
    """
    schema_path = get_schema_path()
    if not schema_path.exists():
        raise FileNotFoundError(
            f"Schema file not found at {schema_path}. "
            "Task T006 (Create schema definitions) must be executed first to generate this file."
        )
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_type(value, expected_type):
    """
    Simple type validation helper.
    
    Args:
        value: The value to check.
        expected_type: The expected type name (e.g., 'string', 'integer', 'number', 'array', 'object').
        
    Returns:
        bool: True if the value matches the expected type.
    """
    type_map = {
        'string': str,
        'integer': int,
        'number': (int, float),
        'boolean': bool,
        'array': list,
        'object': dict,
        'null': type(None)
    }
    
    python_type = type_map.get(expected_type)
    if python_type is None:
        return True # Unknown type, assume valid for now
        
    if expected_type == 'integer':
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == 'number':
        return isinstance(value, (int, float)) and not isinstance(value, bool)
        
    return isinstance(value, python_type)

def validate_required_fields(data, required_fields):
    """
    Ensure all required fields are present in the data.
    
    Args:
        data: The data dictionary to validate.
        required_fields: List of required field names.
        
    Raises:
        ValueError: If a required field is missing.
    """
    missing = [field for field in required_fields if field not in data]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

def validate_data_against_schema(data, schema):
    """
    Validate a data sample against the loaded schema.
    
    This is a simplified validator focusing on:
    1. Required fields presence.
    2. Basic type checking for defined properties.
    
    Args:
        data: The data sample (dict).
        schema: The schema definition (dict).
        
    Raises:
        ValueError: If validation fails.
    """
    if not isinstance(schema, dict):
        raise ValueError("Invalid schema format: expected a dictionary.")
        
    properties = schema.get('properties', {})
    required = schema.get('required', [])
    
    # Check required fields
    validate_required_fields(data, required)
    
    # Check types
    for field, rules in properties.items():
        if field in data:
            value = data[field]
            expected_type = rules.get('type')
            
            if expected_type and not validate_type(value, expected_type):
                raise ValueError(
                    f"Field '{field}' has invalid type. "
                    f"Expected {expected_type}, got {type(value).__name__}."
                )

# --- Test Cases ---

def test_schemas_exist():
    """Verify that the schema file exists on disk."""
    schema_path = get_schema_path()
    assert schema_path.exists(), f"Schema file missing at {schema_path}. Ensure T006 has run."

def test_dataset_schema_structure():
    """
    Verify that the loaded schema has the expected structure.
    Specifically checks for the fields mentioned in the task description:
    sample_id, tumor_type, response_label, expression_vector, set_type.
    """
    schema = load_schema()
    
    assert 'properties' in schema, "Schema must have 'properties' key."
    properties = schema['properties']
    
    expected_fields = ['sample_id', 'tumor_type', 'response_label', 'expression_vector', 'set_type']
    for field in expected_fields:
        assert field in properties, f"Schema missing required field: {field}"

def test_sample_data_validation():
    """
    Test that a valid synthetic sample passes validation.
    """
    schema = load_schema()
    
    # Construct a valid synthetic sample based on typical schema requirements
    # Note: expression_vector is often an array of numbers
    valid_sample = {
        "sample_id": "TCGA-AB-1234-01",
        "tumor_type": "BRCA",
        "response_label": "Responder",
        "expression_vector": [1.2, 3.4, 5.6, 7.8],
        "set_type": "discovery"
    }
    
    # This should not raise an exception
    try:
        validate_data_against_schema(valid_sample, schema)
    except ValueError as e:
        pytest.fail(f"Valid sample failed validation: {e}")

def test_invalid_data_catches_error():
    """
    Test that invalid data (missing required field or wrong type) fails validation.
    """
    schema = load_schema()
    
    # Case 1: Missing required field
    invalid_sample_missing_field = {
        "sample_id": "TCGA-AB-1234-01",
        "tumor_type": "BRCA",
        # Missing response_label, expression_vector, set_type
    }
    
    with pytest.raises(ValueError) as exc_info:
        validate_data_against_schema(invalid_sample_missing_field, schema)
    
    assert "Missing required fields" in str(exc_info.value)
    
    # Case 2: Wrong type
    invalid_sample_wrong_type = {
        "sample_id": 12345, # Should be string
        "tumor_type": "BRCA",
        "response_label": "Responder",
        "expression_vector": [1.2, 3.4],
        "set_type": "discovery"
    }
    
    with pytest.raises(ValueError) as exc_info:
        validate_data_against_schema(invalid_sample_wrong_type, schema)
        
    assert "invalid type" in str(exc_info.value)

def test_file_not_found_error_message():
    """
    Test that the FileNotFoundError is raised with the correct message if schema is missing.
    This is a unit test for the error handling logic.
    """
    # Temporarily rename the file to simulate missing T006 output
    schema_path = get_schema_path()
    if schema_path.exists():
        backup_path = schema_path.with_suffix('.yaml.bak')
        schema_path.rename(backup_path)
        try:
            with pytest.raises(FileNotFoundError) as exc_info:
                load_schema()
            
            assert "T006" in str(exc_info.value)
        finally:
            # Restore the file
            backup_path.rename(schema_path)
    else:
        # If file is already missing, just verify the error
        with pytest.raises(FileNotFoundError) as exc_info:
            load_schema()
        assert "T006" in str(exc_info.value)
