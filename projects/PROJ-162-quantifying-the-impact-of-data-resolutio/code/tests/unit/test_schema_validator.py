"""
Unit tests for the schema validator module.
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.schema_validator import (
    SchemaValidationError,
    SchemaValidator,
    get_validator,
    validate_data,
    validate_and_save
)
from src.config import get_contract_path


class TestSchemaValidator:
    """Tests for the SchemaValidator class."""

    def test_schema_not_found(self):
        """Test that SchemaValidationError is raised when schema file doesn't exist."""
        with pytest.raises(SchemaValidationError, match="Schema file not found"):
            SchemaValidator("nonexistent_schema")

    def test_valid_json_schema(self):
        """Test loading a valid JSON schema."""
        # Create a temporary schema file
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "test_schema.json"
            schema_content = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                },
                "required": ["name"]
            }

            with open(schema_path, 'w') as f:
                json.dump(schema_content, f)

            # Mock get_contract_path to return our temp file
            with patch('src.schema_validator.get_contract_path', return_value=schema_path):
                validator = SchemaValidator("test_schema")
                assert validator.schema == schema_content

    def test_validate_valid_data(self):
        """Test validation of data that conforms to schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "test_schema.json"
            schema_content = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                },
                "required": ["name"]
            }

            with open(schema_path, 'w') as f:
                json.dump(schema_content, f)

            with patch('src.schema_validator.get_contract_path', return_value=schema_path):
                validator = SchemaValidator("test_schema")
                valid_data = {"name": "John", "age": 30}
                assert validator.validate(valid_data) is True

    def test_validate_invalid_data(self):
        """Test validation of data that violates schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "test_schema.json"
            schema_content = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                },
                "required": ["name"]
            }

            with open(schema_path, 'w') as f:
                json.dump(schema_content, f)

            with patch('src.schema_validator.get_contract_path', return_value=schema_path):
                validator = SchemaValidator("test_schema")
                # Missing required 'name' field
                invalid_data = {"age": 30}
                with pytest.raises(SchemaValidationError, match="Schema validation failed"):
                    validator.validate(invalid_data)

    def test_validate_list_of_records(self):
        """Test validation of a list of records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "test_schema.json"
            schema_content = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"}
                },
                "required": ["name"]
            }

            with open(schema_path, 'w') as f:
                json.dump(schema_content, f)

            with patch('src.schema_validator.get_contract_path', return_value=schema_path):
                validator = SchemaValidator("test_schema")
                valid_data = [
                    {"name": "John"},
                    {"name": "Jane"}
                ]
                assert validator.validate(valid_data) is True

    def test_validate_list_with_invalid_record(self):
        """Test validation fails if any record in list is invalid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "test_schema.json"
            schema_content = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"}
                },
                "required": ["name"]
            }

            with open(schema_path, 'w') as f:
                json.dump(schema_content, f)

            with patch('src.schema_validator.get_contract_path', return_value=schema_path):
                validator = SchemaValidator("test_schema")
                # One record missing 'name'
                invalid_data = [
                    {"name": "John"},
                    {"age": 30}
                ]
                with pytest.raises(SchemaValidationError, match="Schema validation failed"):
                    validator.validate(invalid_data)


def test_convenience_functions():
    """Test the convenience functions get_validator, validate_data, validate_and_save."""

    # Test get_validator
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_path = Path(tmpdir) / "test_schema.json"
        schema_content = {
            "type": "object",
            "properties": {
                "value": {"type": "number"}
            },
            "required": ["value"]
        }

        with open(schema_path, 'w') as f:
            json.dump(schema_content, f)

        with patch('src.schema_validator.get_contract_path', return_value=schema_path):
            # Test get_validator
            validator = get_validator("test_schema")
            assert isinstance(validator, SchemaValidator)

            # Test validate_data
            assert validate_data({"value": 42}, "test_schema") is True
            with pytest.raises(SchemaValidationError):
                validate_data({"value": "not_a_number"}, "test_schema")

            # Test validate_and_save
            output_path = Path(tmpdir) / "output.json"
            result_path = validate_and_save(
                {"value": 100},
                output_path,
                "test_schema"
            )
            assert result_path.exists()
            assert result_path == output_path

            # Verify content
            with open(result_path, 'r') as f:
                saved_data = json.load(f)
            assert saved_data == {"value": 100}

    # Test validate_and_save with CSV
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_path = Path(tmpdir) / "test_schema.json"
        schema_content = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "number"}
            },
            "required": ["name", "value"]
        }

        with open(schema_path, 'w') as f:
            json.dump(schema_content, f)

        with patch('src.schema_validator.get_contract_path', return_value=schema_path):
            output_path = Path(tmpdir) / "output.csv"
            result_path = validate_and_save(
                [
                    {"name": "Item1", "value": 10},
                    {"name": "Item2", "value": 20}
                ],
                output_path,
                "test_schema"
            )
            assert result_path.exists()
            assert result_path.suffix == '.csv'