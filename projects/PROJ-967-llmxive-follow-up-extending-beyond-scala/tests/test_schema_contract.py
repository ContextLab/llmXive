"""
Unit tests for the dataset schema contract validation.
Tests that T001d requirements are satisfied.
"""
import pytest
import yaml
import tempfile
from pathlib import Path
import sys
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.validate_schema_contract import (
    validate_schema,
    load_schema,
    validate_schema_structure,
    validate_fields,
    REQUIRED_FIELDS,
    REQUIRED_FIELD_TYPES
)

class TestSchemaContract:
    """Test cases for schema contract validation."""
    
    @pytest.fixture
    def valid_schema(self):
        """Create a valid schema for testing."""
        schema = {
            "version": "1.0",
            "description": "Test schema",
            "fields": {
                "prompt": {"type": "str", "required": True},
                "image_path": {"type": "str", "required": True},
                "teacher_logits": {
                    "type": "list[float]",
                    "required": True,
                    "length": 4,
                    "dimensions": ["Alignment", "Realism", "Aesthetics", "Plausibility"]
                },
                "student_scalar": {"type": "float", "required": True},
                "human_annotations": {
                    "type": "dict",
                    "required": True,
                    "keys": {
                        "Alignment": "float",
                        "Realism": "float",
                        "Aesthetics": "float",
                        "Plausibility": "float"
                    }
                },
                "primary_dimension": {
                    "type": "str",
                    "required": True,
                    "allowed_values": ["Alignment", "Realism", "Aesthetics", "Plausibility"]
                }
            },
            "validation_rules": [],
            "metadata": {}
        }
        return schema
    
    @pytest.fixture
    def temp_schema_file(self, valid_schema):
        """Create a temporary schema file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_schema, f)
            temp_path = Path(f.name)
        yield temp_path
        temp_path.unlink()
    
    def test_valid_schema_loads(self, temp_schema_file):
        """Test that a valid schema can be loaded."""
        schema = load_schema(temp_schema_file)
        assert schema is not None
        assert "fields" in schema
    
    def test_valid_schema_structure(self, valid_schema):
        """Test that a valid schema passes structure validation."""
        assert validate_schema_structure(valid_schema) is True
    
    def test_valid_schema_fields(self, valid_schema):
        """Test that a valid schema passes field validation."""
        assert validate_fields(valid_schema) is True
    
    def test_missing_top_level_key(self, valid_schema):
        """Test that missing top-level keys raise an error."""
        del valid_schema["version"]
        with pytest.raises(ValueError, match="missing required top-level keys"):
            validate_schema_structure(valid_schema)
    
    def test_missing_required_field(self, valid_schema):
        """Test that missing required fields raise an error."""
        del valid_schema["fields"]["prompt"]
        with pytest.raises(ValueError, match="missing required fields"):
            validate_fields(valid_schema)
    
    def test_wrong_field_type(self, valid_schema):
        """Test that wrong field types raise an error."""
        valid_schema["fields"]["prompt"]["type"] = "int"
        with pytest.raises(ValueError, match="has type 'int', expected 'str'"):
            validate_fields(valid_schema)
    
    def test_wrong_teacher_logits_length(self, valid_schema):
        """Test that wrong teacher_logits length raises an error."""
        valid_schema["fields"]["teacher_logits"]["length"] = 5
        with pytest.raises(ValueError, match="teacher_logits must have length 4"):
            validate_fields(valid_schema)
    
    def test_missing_human_annotation_dims(self, valid_schema):
        """Test that missing human annotation dimensions raise an error."""
        valid_schema["fields"]["human_annotations"]["keys"] = {"Alignment": "float"}
        with pytest.raises(ValueError, match="must contain dimensions"):
            validate_fields(valid_schema)
    
    def test_wrong_primary_dimension_values(self, valid_schema):
        """Test that wrong primary_dimension allowed_values raise an error."""
        valid_schema["fields"]["primary_dimension"]["allowed_values"] = ["Alignment"]
        with pytest.raises(ValueError, match="allowed_values must be"):
            validate_fields(valid_schema)
    
    def test_full_validation(self, temp_schema_file):
        """Test full schema validation end-to-end."""
        assert validate_schema(temp_schema_file) is True
    
    def test_required_fields_exist(self):
        """Verify that all required fields are defined in constants."""
        expected = {"prompt", "image_path", "teacher_logits", "student_scalar", 
                   "human_annotations", "primary_dimension"}
        assert REQUIRED_FIELDS == expected
    
    def test_required_types_match(self):
        """Verify that required field types are correctly defined."""
        expected = {
            "prompt": "str",
            "image_path": "str",
            "teacher_logits": "list[float]",
            "student_scalar": "float",
            "human_annotations": "dict",
            "primary_dimension": "str"
        }
        assert REQUIRED_FIELD_TYPES == expected
        
if __name__ == "__main__":
    pytest.main([__file__, "-v"])