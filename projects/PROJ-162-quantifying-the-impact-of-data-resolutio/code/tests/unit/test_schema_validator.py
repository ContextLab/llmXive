"""
Unit tests for src/schema_validator.py
"""

import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust import path based on project structure
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.schema_validator import (
    validate_json,
    validate_file,
    SchemaValidationError,
    _load_schema
)


class TestSchemaValidator:
    """Tests for schema validation logic."""

    def test_valid_json_against_schema(self):
        """Test that valid data passes validation."""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "value": {"type": "number"}
            },
            "required": ["id", "value"]
        }

        valid_data = {"id": "test-123", "value": 42.5}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema, f)
            schema_path = f.name

        try:
            result = validate_json(valid_data, schema_path)
            assert result is True
        finally:
            os.unlink(schema_path)

    def test_invalid_json_missing_required_field(self):
        """Test that data missing a required field fails."""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"}
            },
            "required": ["id"]
        }

        invalid_data = {"other_field": "value"}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema, f)
            schema_path = f.name

        try:
            with pytest.raises(SchemaValidationError):
                validate_json(invalid_data, schema_path)
        finally:
            os.unlink(schema_path)

    def test_invalid_json_wrong_type(self):
        """Test that data with wrong type fails."""
        schema = {
            "type": "object",
            "properties": {
                "count": {"type": "integer"}
            }
        }

        invalid_data = {"count": "not_an_integer"}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema, f)
            schema_path = f.name

        try:
            with pytest.raises(SchemaValidationError):
                validate_json(invalid_data, schema_path)
        finally:
            os.unlink(schema_path)

    def test_load_yaml_schema(self):
        """Test loading a schema from a YAML file."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(schema, f)
            schema_path = f.name

        try:
            loaded = _load_schema(schema_path)
            assert loaded == schema
        finally:
            os.unlink(schema_path)

    def test_file_not_found_schema(self):
        """Test error when schema file is missing."""
        with pytest.raises(FileNotFoundError):
            _load_schema("/nonexistent/path/schema.json")

    def test_file_not_found_data(self):
        """Test error when data file is missing."""
        schema = {"type": "object"}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema, f)
            schema_path = f.name

        try:
            with pytest.raises(FileNotFoundError):
                validate_file("/nonexistent/data.json", schema_path)
        finally:
            os.unlink(schema_path)

    def test_validate_file_json(self):
        """Test validate_file with a JSON data file."""
        schema = {
            "type": "object",
            "properties": {"status": {"type": "string"}},
            "required": ["status"]
        }
        data = {"status": "ok"}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as sf:
            json.dump(schema, sf)
            schema_path = sf.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as df:
            json.dump(data, df)
            data_path = df.name

        try:
            assert validate_file(data_path, schema_path) is True
        finally:
            os.unlink(schema_path)
            os.unlink(data_path)

    def test_validate_file_yaml(self):
        """Test validate_file with a YAML data file."""
        schema = {
            "type": "object",
            "properties": {"active": {"type": "boolean"}},
            "required": ["active"]
        }
        data = {"active": True}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as sf:
            json.dump(schema, sf)
            schema_path = sf.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as df:
            import yaml
            yaml.dump(data, df)
            data_path = df.name

        try:
            assert validate_file(data_path, schema_path) is True
        finally:
            os.unlink(schema_path)
            os.unlink(data_path)


def test_convenience_functions():
    """Integration test for the public API."""
    schema = {
        "type": "object",
        "properties": {
            "resolution": {"type": "integer", "minimum": 100},
            "snr": {"type": "number"}
        },
        "required": ["resolution", "snr"]
    }

    valid_data = {"resolution": 1024, "snr": 8.5}
    invalid_data = {"resolution": "high", "snr": 8.5}

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(schema, f)
        schema_path = f.name

    try:
        # Test valid
        assert validate_json(valid_data, schema_path) is True

        # Test invalid
        with pytest.raises(SchemaValidationError):
            validate_json(invalid_data, schema_path)

    finally:
        os.unlink(schema_path)