"""
Unit tests for the schema validation utilities.
"""
import json
import yaml
import pytest
import os
import tempfile
from pathlib import Path

from .schema_validator import validate_json_schema, validate_yaml_schema, load_schema


class TestSchemaValidator:
    """Tests for the schema validation utilities."""

    def test_load_schema_valid(self):
        """Test loading a valid JSON schema file."""
        schema_content = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema_content, f)
            schema_path = f.name
        
        try:
            schema = load_schema(schema_path)
            assert schema["type"] == "object"
            assert "name" in schema["properties"]
        finally:
            os.unlink(schema_path)

    def test_load_schema_invalid_path(self):
        """Test loading a non-existent schema file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_schema("/nonexistent/path/schema.json")

    def test_validate_json_schema_valid(self):
        """Test validating data against a valid JSON schema."""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "value": {"type": "string"}
            },
            "required": ["id", "value"]
        }
        
        data = {"id": 123, "value": "test"}
        
        # Should not raise
        result = validate_json_schema(data, schema)
        assert result is True

    def test_validate_json_schema_invalid_type(self):
        """Test validating data with wrong type fails."""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "count": {"type": "integer"}
            }
        }
        
        data = {"count": "not_an_integer"}
        
        with pytest.raises(ValueError):
            validate_json_schema(data, schema)

    def test_validate_json_schema_missing_required(self):
        """Test validating data with missing required field fails."""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "required": ["name"]
        }
        
        data = {}
        
        with pytest.raises(ValueError):
            validate_json_schema(data, schema)

    def test_validate_yaml_schema_valid(self):
        """Test validating data against a valid YAML schema."""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "config": {"type": "string"},
                "version": {"type": "integer"}
            },
            "required": ["config"]
        }
        
        data = {"config": "production", "version": 1}
        
        result = validate_yaml_schema(data, schema)
        assert result is True

    def test_validate_yaml_schema_invalid(self):
        """Test validating invalid data against schema fails."""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "threshold": {"type": "number"}
            }
        }
        
        data = {"threshold": "high"}
        
        with pytest.raises(ValueError):
            validate_yaml_schema(data, schema)

    def test_validate_json_file(self):
        """Test validating a JSON file against a schema."""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "status": {"type": "string", "enum": ["completed", "failed"]}
            },
            "required": ["task_id", "status"]
        }
        
        data = {"task_id": "T005", "status": "completed"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            data_path = f.name
        
        try:
            result = validate_json_schema(data, schema)
            assert result is True
        finally:
            os.unlink(data_path)

    def test_validate_yaml_file(self):
        """Test validating a YAML file against a schema."""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "active": {"type": "boolean"}
            },
            "required": ["name"]
        }
        
        data = {"name": "test_project", "active": True}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(data, f)
            data_path = f.name
        
        try:
            result = validate_yaml_schema(data, schema)
            assert result is True
        finally:
            os.unlink(data_path)
