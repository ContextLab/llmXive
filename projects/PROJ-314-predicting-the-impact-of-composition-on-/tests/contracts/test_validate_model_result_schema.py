"""
Unit tests for model_result schema validation.
"""
import pytest
import yaml
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.contracts.validate_model_result_schema import (
    load_yaml_schema,
    validate_model_result_schema,
    REQUIRED_FIELDS
)

class TestLoadYamlSchema:
    def test_load_existing_schema(self, tmp_path):
        """Test loading an existing schema file."""
        schema_content = {
            "type": "object",
            "properties": {
                "model_type": {"type": "string"},
                "mae": {"type": "number"}
            }
        }
        schema_file = tmp_path / "test_schema.yaml"
        with open(schema_file, 'w') as f:
            yaml.dump(schema_content, f)
        
        result = load_yaml_schema(schema_file)
        assert result == schema_content

    def test_load_nonexistent_schema(self, tmp_path):
        """Test loading a non-existent schema file raises FileNotFoundError."""
        schema_file = tmp_path / "nonexistent.yaml"
        
        with pytest.raises(FileNotFoundError):
            load_yaml_schema(schema_file)

class TestValidateModelResultSchema:
    def test_valid_schema_with_all_fields(self, tmp_path):
        """Test validation passes with all required fields."""
        schema_content = {
            "type": "object",
            "properties": {
                "model_type": {"type": "string"},
                "mae": {"type": "number"},
                "r_squared": {"type": "number"},
                "feature_importance_ranking": {"type": "array"},
                "cv_stability_scores": {"type": "array"}
            }
        }
        schema_file = tmp_path / "valid_schema.yaml"
        with open(schema_file, 'w') as f:
            yaml.dump(schema_content, f)
        
        assert validate_model_result_schema(schema_file) is True

    def test_missing_required_field(self, tmp_path):
        """Test validation fails when a required field is missing."""
        schema_content = {
            "type": "object",
            "properties": {
                "model_type": {"type": "string"},
                "mae": {"type": "number"}
                # Missing r_squared, feature_importance_ranking, cv_stability_scores
            }
        }
        schema_file = tmp_path / "invalid_schema.yaml"
        with open(schema_file, 'w') as f:
            yaml.dump(schema_content, f)
        
        with pytest.raises(ValueError) as exc_info:
            validate_model_result_schema(schema_file)
        
        assert "Missing required fields" in str(exc_info.value)
        assert "r_squared" in str(exc_info.value)

    def test_schema_without_properties_key(self, tmp_path):
        """Test validation handles schema without 'properties' key."""
        # Schema with fields at root level (non-standard but handled)
        schema_content = {
            "model_type": {"type": "string"},
            "mae": {"type": "number"},
            "r_squared": {"type": "number"},
            "feature_importance_ranking": {"type": "array"},
            "cv_stability_scores": {"type": "array"}
        }
        schema_file = tmp_path / "root_level_schema.yaml"
        with open(schema_file, 'w') as f:
            yaml.dump(schema_content, f)
        
        assert validate_model_result_schema(schema_file) is True

    def test_schema_with_type_object_no_properties(self, tmp_path):
        """Test validation fails for 'type: object' without properties."""
        schema_content = {
            "type": "object"
        }
        schema_file = tmp_path / "empty_object_schema.yaml"
        with open(schema_file, 'w') as f:
            yaml.dump(schema_content, f)
        
        with pytest.raises(ValueError) as exc_info:
            validate_model_result_schema(schema_file)
        
        assert "missing 'properties'" in str(exc_info.value)

    def test_non_dict_schema(self, tmp_path):
        """Test validation fails for non-dictionary schema."""
        schema_file = tmp_path / "invalid_type.yaml"
        with open(schema_file, 'w') as f:
            f.write("just a string")
        
        with pytest.raises(ValueError) as exc_info:
            validate_model_result_schema(schema_file)
        
        assert "Schema must be a dictionary" in str(exc_info.value)

    def test_non_dict_properties(self, tmp_path):
        """Test validation fails when properties is not a dictionary."""
        schema_content = {
            "type": "object",
            "properties": ["model_type", "mae"]
        }
        schema_file = tmp_path / "list_properties.yaml"
        with open(schema_file, 'w') as f:
            yaml.dump(schema_content, f)
        
        with pytest.raises(ValueError) as exc_info:
            validate_model_result_schema(schema_file)
        
        assert "'properties' must be a dictionary" in str(exc_info.value)

class TestRequiredFields:
    def test_required_fields_set(self):
        """Test that REQUIRED_FIELDS contains all expected fields."""
        expected_fields = {
            "model_type",
            "mae",
            "r_squared",
            "feature_importance_ranking",
            "cv_stability_scores"
        }
        assert REQUIRED_FIELDS == expected_fields
        assert len(REQUIRED_FIELDS) == 5