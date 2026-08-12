"""
Unit tests for code/research/validate_schema.py
"""
import pytest
import yaml
import json
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from research.validate_schema import (
    load_yaml_schema,
    validate_schema_structure,
    validate_with_jsonschema,
    OUTPUT_SCHEMA_PATH
)


@pytest.fixture
def valid_schema_dict():
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "metrics": {
                "type": "object",
                "properties": {
                    "balanced_accuracy": {"type": "number"}
                },
                "required": ["balanced_accuracy"]
            }
        }
    }


@pytest.fixture
def invalid_schema_dict():
    # Missing $schema
    return {
        "type": "object",
        "properties": {}
    }


@pytest.fixture
def valid_sample_data():
    return {
        "metrics": {
            "balanced_accuracy": 0.85,
            "roc_auc": 0.92,
            "permutation_p_value": 0.03
        },
        "shap_analysis": {
            "top_features": [
                {"feature_name": "metabolite_A", "shap_value": 0.5}
            ],
            "collinearity_vif": [
                {"feature_name": "metabolite_A", "vif_value": 1.2}
            ]
        }
    }


def test_load_yaml_schema_exists(tmp_path):
    """Test loading a valid YAML file."""
    schema_file = tmp_path / "test_schema.yaml"
    schema_content = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object"
    }
    with open(schema_file, 'w') as f:
        yaml.dump(schema_content, f)
    
    loaded = load_yaml_schema(schema_file)
    assert loaded == schema_content


def test_load_yaml_schema_missing_file(tmp_path):
    """Test loading a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_yaml_schema(tmp_path / "non_existent.yaml")


def test_load_yaml_schema_invalid_yaml(tmp_path):
    """Test loading invalid YAML raises YAMLError."""
    schema_file = tmp_path / "invalid.yaml"
    with open(schema_file, 'w') as f:
        f.write("invalid: yaml: content: [unclosed")
    
    with pytest.raises(yaml.YAMLError):
        load_yaml_schema(schema_file)


def test_validate_schema_structure_valid(valid_schema_dict):
    """Test validation of a structurally valid schema."""
    assert validate_schema_structure(valid_schema_dict) is True


def test_validate_schema_structure_missing_key(invalid_schema_dict):
    """Test validation fails when required keys are missing."""
    assert validate_schema_structure(invalid_schema_dict) is False


def test_validate_schema_structure_wrong_type(tmp_path):
    """Test validation fails if root type is not object."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "array"
    }
    assert validate_schema_structure(schema) is False


def test_validate_with_jsonschema_valid(tmp_path, valid_schema_dict, valid_sample_data):
    """Test full validation with valid schema and data."""
    schema_file = tmp_path / "valid_schema.yaml"
    with open(schema_file, 'w') as f:
        yaml.dump(valid_schema_dict, f)
    
    # This should not raise and return True
    result = validate_with_jsonschema(schema_file, valid_sample_data)
    assert result is True


def test_validate_with_jsonschema_invalid_data(tmp_path, valid_schema_dict):
    """Test validation fails with invalid sample data."""
    schema_file = tmp_path / "valid_schema.yaml"
    with open(schema_file, 'w') as f:
        yaml.dump(valid_schema_dict, f)
    
    invalid_data = {"metrics": {"balanced_accuracy": "not_a_number"}}
    result = validate_with_jsonschema(schema_file, invalid_data)
    assert result is False


def test_validate_with_jsonschema_invalid_schema(tmp_path, invalid_schema_dict):
    """Test validation fails if the schema itself is invalid JSON Schema."""
    schema_file = tmp_path / "invalid_schema.yaml"
    with open(schema_file, 'w') as f:
        yaml.dump(invalid_schema_dict, f)
    
    result = validate_with_jsonschema(schema_file)
    assert result is False


def test_output_schema_exists():
    """Verify the actual output schema file exists in the project."""
    assert OUTPUT_SCHEMA_PATH.exists(), f"Output schema file not found at {OUTPUT_SCHEMA_PATH}"


def test_output_schema_valid_json_schema():
    """Verify the actual output schema is valid JSON Schema."""
    result = validate_with_jsonschema(OUTPUT_SCHEMA_PATH)
    assert result is True, "The actual output.schema.yaml failed validation."