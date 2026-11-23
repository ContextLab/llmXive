"""
Unit tests for the schema validator module.
"""

import pytest
import json
from pathlib import Path
from code.utils.schema_validator import (
    load_schema,
    validate_type,
    validate_value_constraints,
    validate_object,
    validate_dataset,
    get_missing_fields,
    validate_dataset_schema,
    SchemaValidationError
)

# Test fixtures
@pytest.fixture
def sample_schema():
    return {
        "type": "object",
        "required": ["Dialogue", "User"],
        "properties": {
            "Dialogue": {
                "type": "object",
                "required": ["dialogue_id", "user_id"],
                "properties": {
                    "dialogue_id": {
                        "type": "string",
                        "pattern": "^[A-Za-z0-9_-]+$"
                    },
                    "user_id": {
                        "type": "string",
                        "pattern": "^[A-Za-z0-9_-]+$"
                    },
                    "quality_rating": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5
                    }
                }
            },
            "User": {
                "type": "object",
                "required": ["user_id"],
                "properties": {
                    "user_id": {
                        "type": "string"
                    },
                    "age": {
                        "type": "integer",
                        "minimum": 18,
                        "maximum": 100
                    },
                    "gender": {
                        "type": "string",
                        "enum": ["male", "female", "other"]
                    }
                }
            }
        }
    }

@pytest.fixture
def valid_dataset():
    return {
        "Dialogue": {
            "dialogue_id": "dlg_123",
            "user_id": "usr_456",
            "quality_rating": 4
        },
        "User": {
            "user_id": "usr_456",
            "age": 25,
            "gender": "female"
        }
    }

@pytest.fixture
def invalid_dataset_missing_field():
    return {
        "Dialogue": {
            "dialogue_id": "dlg_123",
            # Missing user_id
            "quality_rating": 4
        },
        "User": {
            "user_id": "usr_456",
            "age": 25,
            "gender": "female"
        }
    }

@pytest.fixture
def invalid_dataset_wrong_type():
    return {
        "Dialogue": {
            "dialogue_id": "dlg_123",
            "user_id": "usr_456",
            "quality_rating": "not_an_integer"  # Should be integer
        },
        "User": {
            "user_id": "usr_456",
            "age": 25,
            "gender": "female"
        }
    }

@pytest.fixture
def invalid_dataset_out_of_range():
    return {
        "Dialogue": {
            "dialogue_id": "dlg_123",
            "user_id": "usr_456",
            "quality_rating": 10  # Out of range (1-5)
        },
        "User": {
            "user_id": "usr_456",
            "age": 25,
            "gender": "female"
        }
    }

def test_load_schema_default_path(tmp_path, sample_schema):
    """Test loading schema from default path."""
    # Create a temporary schema file
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir()
    schema_file = contracts_dir / "dataset.schema.yaml"
    
    import yaml
    with open(schema_file, 'w') as f:
        yaml.dump(sample_schema, f)
    
    # Change to temp directory to test default path resolution
    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        schema = load_schema()
        assert schema == sample_schema
    finally:
        os.chdir(original_cwd)

def test_load_schema_custom_path(sample_schema, tmp_path):
    """Test loading schema from custom path."""
    schema_file = tmp_path / "custom_schema.yaml"
    
    import yaml
    with open(schema_file, 'w') as f:
        yaml.dump(sample_schema, f)
    
    schema = load_schema(schema_file)
    assert schema == sample_schema

def test_load_schema_file_not_found():
    """Test that FileNotFoundError is raised for missing schema."""
    with pytest.raises(FileNotFoundError):
        load_schema("/nonexistent/path/schema.yaml")

def test_validate_type_string():
    """Test type validation for strings."""
    assert validate_type("hello", "string", "test_field") is True
    
    with pytest.raises(SchemaValidationError):
        validate_type(123, "string", "test_field")

def test_validate_type_integer():
    """Test type validation for integers."""
    assert validate_type(42, "integer", "test_field") is True
    assert validate_type(0, "integer", "test_field") is True
    assert validate_type(-5, "integer", "test_field") is True
    
    with pytest.raises(SchemaValidationError):
        validate_type("42", "integer", "test_field")
    
    with pytest.raises(SchemaValidationError):
        validate_type(True, "integer", "test_field")  # bool should not match int

def test_validate_type_float():
    """Test type validation for numbers (int or float)."""
    assert validate_type(3.14, "number", "test_field") is True
    assert validate_type(42, "number", "test_field") is True

def test_validate_type_array():
    """Test type validation for arrays."""
    assert validate_type([1, 2, 3], "array", "test_field") is True
    
    with pytest.raises(SchemaValidationError):
        validate_type("not a list", "array", "test_field")

def test_validate_type_object():
    """Test type validation for objects."""
    assert validate_type({"key": "value"}, "object", "test_field") is True
    
    with pytest.raises(SchemaValidationError):
        validate_type([], "object", "test_field")

def test_validate_value_constraints_minimum():
    """Test minimum constraint validation."""
    assert validate_value_constraints(5, {"minimum": 1}, "test_field") is True
    
    with pytest.raises(SchemaValidationError):
        validate_value_constraints(0, {"minimum": 1}, "test_field")

def test_validate_value_constraints_maximum():
    """Test maximum constraint validation."""
    assert validate_value_constraints(3, {"maximum": 5}, "test_field") is True
    
    with pytest.raises(SchemaValidationError):
        validate_value_constraints(10, {"maximum": 5}, "test_field")

def test_validate_value_constraints_pattern():
    """Test pattern constraint validation."""
    assert validate_value_constraints("abc123", {"pattern": "^[A-Za-z0-9]+$"}, "test_field") is True
    
    with pytest.raises(SchemaValidationError):
        validate_value_constraints("abc-123", {"pattern": "^[A-Za-z0-9]+$"}, "test_field")

def test_validate_value_constraints_enum():
    """Test enum constraint validation."""
    assert validate_value_constraints("male", {"enum": ["male", "female", "other"]}, "test_field") is True
    
    with pytest.raises(SchemaValidationError):
        validate_value_constraints("unknown", {"enum": ["male", "female", "other"]}, "test_field")

def test_validate_value_constraints_minlength():
    """Test minLength constraint validation."""
    assert validate_value_constraints("hello", {"minLength": 3}, "test_field") is True
    
    with pytest.raises(SchemaValidationError):
        validate_value_constraints("hi", {"minLength": 3}, "test_field")

def test_validate_object_valid(sample_schema, valid_dataset):
    """Test validating a valid object."""
    errors = validate_object(valid_dataset["Dialogue"], sample_schema["properties"]["Dialogue"], "Dialogue")
    assert len(errors) == 0

def test_validate_object_missing_required(sample_schema, invalid_dataset_missing_field):
    """Test validating an object with missing required fields."""
    errors = validate_object(
        invalid_dataset_missing_field["Dialogue"],
        sample_schema["properties"]["Dialogue"],
        "Dialogue"
    )
    assert len(errors) > 0
    assert any("user_id" in err for err in errors)

def test_validate_object_wrong_type(sample_schema, invalid_dataset_wrong_type):
    """Test validating an object with wrong field types."""
    errors = validate_object(
        invalid_dataset_wrong_type["Dialogue"],
        sample_schema["properties"]["Dialogue"],
        "Dialogue"
    )
    assert len(errors) > 0
    assert any("quality_rating" in err for err in errors)

def test_validate_dataset_valid(valid_dataset, sample_schema):
    """Test validating a complete valid dataset."""
    is_valid, errors = validate_dataset(valid_dataset, sample_schema)
    assert is_valid is True
    assert len(errors) == 0

def test_validate_dataset_missing_section(valid_dataset, sample_schema):
    """Test validating a dataset missing a required section."""
    invalid = {"Dialogue": valid_dataset["Dialogue"]}  # Missing User
    is_valid, errors = validate_dataset(invalid, sample_schema)
    assert is_valid is False
    assert len(errors) > 0

def test_get_missing_fields(valid_dataset, sample_schema):
    """Test getting missing fields from a valid dataset."""
    missing = get_missing_fields(valid_dataset, sample_schema)
    assert len(missing) == 0

def test_get_missing_fields_invalid(invalid_dataset_missing_field, sample_schema):
    """Test getting missing fields from an invalid dataset."""
    missing = get_missing_fields(invalid_dataset_missing_field, sample_schema)
    assert len(missing) > 0
    assert any("user_id" in field for field in missing)

def test_validate_dataset_schema(tmp_path, valid_dataset):
    """Test the high-level validate_dataset_schema function."""
    # Create schema file
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir()
    schema_file = contracts_dir / "dataset.schema.yaml"
    
    import yaml
    schema = {
        "type": "object",
        "required": ["Dialogue"],
        "properties": {
            "Dialogue": {
                "type": "object",
                "required": ["dialogue_id"],
                "properties": {
                    "dialogue_id": {"type": "string"}
                }
            }
        }
    }
    
    with open(schema_file, 'w') as f:
        yaml.dump(schema, f)
    
    # Test valid dataset
    is_valid, validation_errors, missing_fields = validate_dataset_schema(valid_dataset, schema_file)
    assert is_valid is True
    assert len(validation_errors) == 0
    assert len(missing_fields) == 0

def test_schema_validation_error_message():
    """Test that SchemaValidationError has meaningful messages."""
    try:
        validate_type("hello", "integer", "test_field")
        assert False, "Should have raised SchemaValidationError"
    except SchemaValidationError as e:
        assert "test_field" in str(e)
        assert "integer" in str(e)