"""
Tests for the utils module.

This module contains unit tests for contract validation, schema loading,
and file I/O functions.
"""
import json
import csv
import os
import tempfile
from pathlib import Path
import pytest

from utils import (
    SchemaValidationError,
    load_json_file,
    save_json_file,
    load_csv_file,
    save_csv_file,
    load_schema,
    validate_against_schema,
    validate_schema,
    is_valid_uuid4,
    load_drift_result_schema,
    validate_drift_result_schema,
)


class TestLoadSaveJson:
    """Tests for JSON file loading and saving."""

    def test_load_json_file_success(self, tmp_path):
        """Test successful loading of a JSON file."""
        test_data = {"key": "value", "number": 42}
        file_path = tmp_path / "test.json"
        
        with open(file_path, 'w') as f:
            json.dump(test_data, f)
        
        result = load_json_file(file_path)
        assert result == test_data

    def test_load_json_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_json_file("/nonexistent/path/file.json")

    def test_load_json_file_invalid_json(self, tmp_path):
        """Test that JSONDecodeError is raised for invalid JSON."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("not valid json")
        
        with pytest.raises(json.JSONDecodeError):
            load_json_file(file_path)

    def test_save_json_file(self, tmp_path):
        """Test saving a dictionary to a JSON file."""
        test_data = {"key": "value", "nested": {"a": 1}}
        file_path = tmp_path / "output.json"
        
        save_json_file(test_data, file_path)
        
        assert file_path.exists()
        loaded = load_json_file(file_path)
        assert loaded == test_data

    def test_save_json_file_creates_directories(self, tmp_path):
        """Test that save_json_file creates parent directories."""
        test_data = {"key": "value"}
        file_path = tmp_path / "subdir" / "nested" / "output.json"
        
        save_json_file(test_data, file_path)
        
        assert file_path.exists()


class TestLoadSaveCsv:
    """Tests for CSV file loading and saving."""

    def test_load_csv_file_success(self, tmp_path):
        """Test successful loading of a CSV file."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("name,age\nAlice,30\nBob,25")
        
        result = load_csv_file(file_path)
        
        assert len(result) == 2
        assert result[0] == {"name": "Alice", "age": "30"}
        assert result[1] == {"name": "Bob", "age": "25"}

    def test_load_csv_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_csv_file("/nonexistent/path/file.csv")

    def test_save_csv_file(self, tmp_path):
        """Test saving a list of dictionaries to a CSV file."""
        test_data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        file_path = tmp_path / "output.csv"
        
        save_csv_file(test_data, file_path)
        
        assert file_path.exists()
        loaded = load_csv_file(file_path)
        assert len(loaded) == 2
        assert loaded[0]["name"] == "Alice"

    def test_save_csv_file_empty_list(self, tmp_path):
        """Test saving an empty list creates an empty file."""
        file_path = tmp_path / "empty.csv"
        
        save_csv_file([], file_path)
        
        assert file_path.exists()
        assert file_path.stat().st_size == 0


class TestSchemaValidation:
    """Tests for schema validation functions."""

    def test_validate_against_schema_valid_data(self):
        """Test validation with valid data."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        data = {"name": "Alice", "age": 30}
        
        assert validate_against_schema(data, schema) is True

    def test_validate_against_schema_missing_required(self):
        """Test validation fails for missing required field."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "required": ["name"]
        }
        data = {"age": 30}
        
        with pytest.raises(SchemaValidationError, match="Missing required field"):
            validate_against_schema(data, schema)

    def test_validate_against_schema_type_mismatch(self):
        """Test validation fails for type mismatch."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            }
        }
        data = {"name": 123}
        
        with pytest.raises(SchemaValidationError, match="Type mismatch"):
            validate_against_schema(data, schema)

    def test_validate_against_schema_nested_object(self):
        """Test validation of nested objects."""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    },
                    "required": ["name"]
                }
            },
            "required": ["user"]
        }
        data = {"user": {"name": "Alice"}}
        
        assert validate_against_schema(data, schema) is True

    def test_validate_against_schema_nested_object_invalid(self):
        """Test validation fails for nested object with missing field."""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    },
                    "required": ["name"]
                }
            }
        }
        data = {"user": {}}
        
        with pytest.raises(SchemaValidationError, match="Missing required field"):
            validate_against_schema(data, schema)

    def test_validate_against_schema_array(self):
        """Test validation of arrays."""
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
        data = {"items": ["a", "b", "c"]}
        
        assert validate_against_schema(data, schema) is True

    def test_validate_against_schema_array_invalid(self):
        """Test validation fails for array with wrong item type."""
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
        data = {"items": ["a", 123, "c"]}
        
        with pytest.raises(SchemaValidationError, match="Type mismatch"):
            validate_against_schema(data, schema)


class TestIsValidUuid4:
    """Tests for UUID4 validation."""

    def test_valid_uuid4(self):
        """Test valid UUID4 format."""
        assert is_valid_uuid4("550e8400-e29b-41d4-a716-446655440000") is True
        assert is_valid_uuid4("550E8400-E29B-41D4-A716-446655440000") is True

    def test_invalid_uuid4_format(self):
        """Test invalid UUID4 format."""
        assert is_valid_uuid4("not-a-uuid") is False
        assert is_valid_uuid4("550e8400-e29b-41d4-a716-44665544000") is False
        assert is_valid_uuid4("550e8400e29b41d4a716446655440000") is False

    def test_empty_string(self):
        """Test empty string."""
        assert is_valid_uuid4("") is False

    def test_none(self):
        """Test None value."""
        assert is_valid_uuid4(None) is False


class TestDriftResultSchema:
    """Tests specific to drift result schema validation."""

    def test_validate_drift_result_schema_valid(self, tmp_path):
        """Test validation with valid drift result data."""
        # Create a mock schema file
        schema_path = tmp_path / "drift_result.schema.yaml"
        schema_content = {
            "type": "object",
            "properties": {
                "log_id": {"type": "string"},
                "drift_score": {"type": "number"},
                "review_flag": {"type": "boolean"}
            },
            "required": ["log_id", "drift_score", "review_flag"]
        }
        
        # Save schema temporarily
        import yaml
        with open(schema_path, 'w') as f:
            yaml.dump(schema_content, f)
        
        # Temporarily patch get_path to return our test schema
        import utils
        original_get_path = utils.get_path
        
        def mock_get_path(path):
            if "drift_result.schema.yaml" in path:
                return str(schema_path)
            return original_get_path(path)
        
        utils.get_path = mock_get_path
        
        try:
            data = {
                "log_id": "550e8400-e29b-41d4-a716-446655440000",
                "drift_score": 0.85,
                "review_flag": True
            }
            
            result = validate_drift_result_schema(data)
            assert result is True
        finally:
            utils.get_path = original_get_path

    def test_validate_drift_result_schema_missing_field(self, tmp_path):
        """Test validation fails for missing required field."""
        schema_path = tmp_path / "drift_result.schema.yaml"
        schema_content = {
            "type": "object",
            "properties": {
                "log_id": {"type": "string"},
                "drift_score": {"type": "number"},
                "review_flag": {"type": "boolean"}
            },
            "required": ["log_id", "drift_score", "review_flag"]
        }
        
        import yaml
        with open(schema_path, 'w') as f:
            yaml.dump(schema_content, f)
        
        import utils
        original_get_path = utils.get_path
        
        def mock_get_path(path):
            if "drift_result.schema.yaml" in path:
                return str(schema_path)
            return original_get_path(path)
        
        utils.get_path = mock_get_path
        
        try:
            data = {
                "log_id": "550e8400-e29b-41d4-a716-446655440000",
                "drift_score": 0.85
            }
            
            with pytest.raises(SchemaValidationError, match="Missing required field"):
                validate_drift_result_schema(data)
        finally:
            utils.get_path = original_get_path
