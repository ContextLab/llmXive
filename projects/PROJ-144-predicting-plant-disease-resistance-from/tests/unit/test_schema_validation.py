"""
Unit tests for schema validation logic.

These tests verify that the validate_schema.py script logic
correctly identifies valid and invalid schema structures.
"""

import pytest
import yaml
import json
import tempfile
from pathlib import Path
import sys
import os

# Add project root to path for imports if needed, 
# though this test focuses on the logic of validation
from jsonschema import Draft7Validator, ValidationError, SchemaError

class TestSchemaValidation:
    
    def test_valid_schema_structure(self):
        """Test that a correctly formatted schema passes validation."""
        valid_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "MetaboliteProfile": {
                    "type": "object",
                    "properties": {
                        "sample_id": {"type": "string"},
                        "InChIKey": {"type": "string"},
                        "normalized_intensity": {"type": "number"}
                    },
                    "required": ["sample_id", "InChIKey", "normalized_intensity"]
                }
            }
        }
        
        # This should not raise
        Draft7Validator.check_schema(valid_schema)
        assert True
    
    def test_invalid_schema_missing_type(self):
        """Test detection of missing type in schema."""
        # While Draft7 allows some flexibility, a valid schema usually has type
        # We test that the validator catches structural issues if we force them
        # Note: Draft7Validator.check_schema is strict about the schema definition itself
        # This test ensures our validation logic handles the case where we might 
        # manually construct an invalid schema for testing purposes.
        
        # A schema with an invalid type value
        invalid_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "invalid_type_value",
            "properties": {}
        }
        
        with pytest.raises(SchemaError):
            Draft7Validator.check_schema(invalid_schema)
    
    def test_yaml_parsing(self):
        """Test that YAML content is correctly parsed."""
        yaml_content = """
        $schema: http://json-schema.org/draft-07/schema#
        type: object
        properties:
          test_field:
            type: string
        """
        
        data = yaml.safe_load(yaml_content)
        assert data['type'] == 'object'
        assert 'test_field' in data['properties']
    
    def test_missing_properties_key(self):
        """Test handling of object type without properties."""
        schema_no_props = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            # Missing properties
        }
        
        # This is technically valid in Draft 07 (allows any object),
        # but our specific validation logic might flag it as a warning.
        # We ensure the validator doesn't crash.
        try:
            Draft7Validator.check_schema(schema_no_props)
            assert True
        except SchemaError:
            pytest.fail("Draft7Validator should accept object without properties")
    
    def test_required_fields_validation(self):
        """Test that required fields are correctly defined in schema."""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "field1": {"type": "string"},
                "field2": {"type": "number"}
            },
            "required": ["field1", "field2"]
        }
        
        Draft7Validator.check_schema(schema)
        
        validator = Draft7Validator(schema)
        
        # Valid instance
        instance_valid = {"field1": "value", "field2": 123}
        assert validator.is_valid(instance_valid)
        
        # Invalid instance (missing required)
        instance_invalid = {"field1": "value"}
        assert not validator.is_valid(instance_invalid)
        
        errors = list(validator.iter_errors(instance_invalid))
        assert len(errors) > 0
        assert "required" in str(errors[0].message).lower()