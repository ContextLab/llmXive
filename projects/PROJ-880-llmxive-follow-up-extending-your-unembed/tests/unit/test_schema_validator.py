"""
Unit tests for the schema validator module.
"""
import json
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from schema_validator import (
    validate_json_against_schema,
    validate_output_file
)


class TestValidateJsonObject:
    """Unit tests for JSON object validation."""
    
    def test_empty_object_with_no_required(self):
        """Test that an empty object passes if no fields are required."""
        data = {}
        schema = {
            "type": "object",
            "properties": {
                "optional_field": {"type": "string"}
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert is_valid
        assert len(errors) == 0
    
    def test_nested_object_validation(self):
        """Test validation of nested objects."""
        data = {
            "outer": {
                "inner": "value",
                "number": 42
            }
        }
        
        schema = {
            "type": "object",
            "properties": {
                "outer": {
                    "type": "object",
                    "required": ["inner", "number"],
                    "properties": {
                        "inner": {"type": "string"},
                        "number": {"type": "number"}
                    }
                }
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert is_valid
        assert len(errors) == 0
    
    def test_nested_object_missing_required(self):
        """Test validation failure on nested object with missing required field."""
        data = {
            "outer": {
                "inner": "value"
                # Missing "number"
            }
        }
        
        schema = {
            "type": "object",
            "properties": {
                "outer": {
                    "type": "object",
                    "required": ["inner", "number"],
                    "properties": {
                        "inner": {"type": "string"},
                        "number": {"type": "number"}
                    }
                }
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert not is_valid
        assert any("number" in error for error in errors)


class TestValidateArrayTypes:
    """Unit tests for array type validation."""
    
    def test_array_of_strings(self):
        """Test validation of an array of strings."""
        data = {
            "items": ["a", "b", "c"]
        }
        
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert is_valid
        assert len(errors) == 0
    
    def test_array_of_objects(self):
        """Test validation of an array of objects."""
        data = {
            "items": [
                {"id": 1, "name": "first"},
                {"id": 2, "name": "second"}
            ]
        }
        
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "name"],
                        "properties": {
                            "id": {"type": "number"},
                            "name": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert is_valid
        assert len(errors) == 0
    
    def test_empty_array(self):
        """Test validation of an empty array."""
        data = {
            "items": []
        }
        
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert is_valid
        assert len(errors) == 0


class TestTypeValidation:
    """Unit tests for type validation."""
    
    def test_all_basic_types(self):
        """Test validation of all basic JSON types."""
        data = {
            "string_field": "text",
            "number_field": 42,
            "float_field": 3.14,
            "boolean_field": True,
            "null_field": None
        }
        
        schema = {
            "type": "object",
            "properties": {
                "string_field": {"type": "string"},
                "number_field": {"type": "number"},
                "float_field": {"type": "number"},
                "boolean_field": {"type": "boolean"},
                "null_field": {"type": "null"}
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert is_valid
        assert len(errors) == 0
    
    def test_string_instead_of_number(self):
        """Test validation failure when string is provided instead of number."""
        data = {
            "value": "42"
        }
        
        schema = {
            "type": "object",
            "properties": {
                "value": {"type": "number"}
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert not is_valid
        assert any("number" in error for error in errors)
    
    def test_number_instead_of_string(self):
        """Test validation failure when number is provided instead of string."""
        data = {
            "value": 42
        }
        
        schema = {
            "type": "object",
            "properties": {
                "value": {"type": "string"}
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert not is_valid
        assert any("string" in error for error in errors)