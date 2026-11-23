"""
Unit tests for schema validation utility.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from code.utils.validate_schema import (
    load_json_file,
    load_schema_file,
    validate_against_schema,
    validate_raw_schema,
    validate_filtered_schema,
    validate_error_classification_schema
)


def test_load_json_file_valid():
    """Test loading a valid JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"key": "value"}, f)
        temp_path = f.name

    try:
        data = load_json_file(Path(temp_path))
        assert data == {"key": "value"}
    finally:
        os.unlink(temp_path)


def test_load_json_file_not_found():
    """Test loading a non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        load_json_file(Path("/nonexistent/file.json"))


def test_load_json_file_invalid():
    """Test loading invalid JSON raises error."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        temp_path = f.name

    try:
        with pytest.raises(ValueError):
            load_json_file(Path(temp_path))
    finally:
        os.unlink(temp_path)


def test_validate_against_schema_valid():
    """Test validation with valid data."""
    schema = {
        "type": "object",
        "required": ["task_id"],
        "properties": {
            "task_id": {"type": "string"},
            "score": {"type": "number"}
        }
    }
    data = {"task_id": "test_1", "score": 0.95}
    
    errors = validate_against_schema(data, schema, "test_schema")
    assert len(errors) == 0


def test_validate_against_schema_invalid():
    """Test validation with invalid data (missing required field)."""
    schema = {
        "type": "object",
        "required": ["task_id"],
        "properties": {
            "task_id": {"type": "string"}
        }
    }
    data = {"score": 0.95}  # Missing task_id
    
    errors = validate_against_schema(data, schema, "test_schema")
    assert len(errors) > 0
    assert "task_id" in errors[0]


def test_validate_raw_schema_with_test_file():
    """Test validation of the test.json file against the schema."""
    # Create a temporary schema file
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["task_id", "perturbation_type", "raw_score", "is_valid", "candidate_text"],
            "properties": {
                "task_id": {"type": "string"},
                "perturbation_type": {"type": "string"},
                "raw_score": {"type": "number"},
                "is_valid": {"type": "boolean"},
                "candidate_text": {"type": "string"}
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as sf:
        json.dump(schema, sf)
        schema_path = sf.name

    try:
        # Use the test.json file created in the task
        test_json_path = Path("data/processed/test.json")
        assert test_json_path.exists(), "Test file data/processed/test.json not found"
        
        is_valid = validate_raw_schema(str(test_json_path), schema_path)
        # The test file should be valid
        assert is_valid
    finally:
        os.unlink(schema_path)


def test_validate_filtered_schema():
    """Test the filtered schema validation function."""
    # Same as raw validation for now
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["task_id"],
            "properties": {
                "task_id": {"type": "string"}
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as sf:
        json.dump(schema, sf)
        schema_path = sf.name

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as df:
            json.dump([{"task_id": "test"}], df)
            data_path = df.name

        try:
            is_valid = validate_filtered_schema(data_path, schema_path)
            assert is_valid
        finally:
            os.unlink(data_path)
    finally:
        os.unlink(schema_path)
