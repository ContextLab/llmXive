import pytest
import yaml
from pathlib import Path
import json

# Import functions from the data_loader module
from code.utils.data_loader import load_schema, validate_fields, SCHEMA_PATH

def test_schema_exists():
    """Test that the schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

def test_schema_is_valid_yaml():
    """Test that the schema file is valid YAML."""
    try:
        with open(SCHEMA_PATH, "r") as f:
            schema = yaml.safe_load(f)
        assert isinstance(schema, dict), "Schema must be a dictionary"
        assert "required" in schema, "Schema must have 'required' field"
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in schema file: {e}")

def test_validate_fields_with_valid_data():
    """Test validation with data that matches the schema."""
    schema = load_schema()
    valid_data = [
        {
            "id": "1",
            "domain": "medical",
            "leak-target": "patient record",
            "role": "doctor",
            "outcome": "allowed",
            "authorization_boundaries": {}
        }
    ]
    
    missing = validate_fields(valid_data, schema)
    assert len(missing) == 0, f"Valid data should not have missing fields: {missing}"

def test_validate_fields_with_missing_required():
    """Test validation detects missing required fields."""
    schema = load_schema()
    invalid_data = [
        {
            "id": "1",
            "domain": "medical",
            # Missing "leak-target", "role", etc.
        }
    ]
    
    missing = validate_fields(invalid_data, schema)
    assert len(missing) > 0, "Should detect missing required fields"
    assert "leak-target" in str(missing), "Should report missing leak-target"

def test_schema_contains_expected_fields():
    """Test that the schema defines the expected fields."""
    schema = load_schema()
    expected_fields = ["id", "domain", "leak-target", "role", "outcome", "authorization_boundaries"]
    
    for field in expected_fields:
        assert field in schema["required"], f"Field '{field}' should be required"
