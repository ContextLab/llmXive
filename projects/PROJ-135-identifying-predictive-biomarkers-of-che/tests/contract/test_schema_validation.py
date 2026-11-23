import os
import sys
import json
import yaml
from pathlib import Path
import pytest

from src.config import get_project_root

def load_schema(schema_name: str) -> dict:
    """Load a schema definition from the contracts directory."""
    project_root = get_project_root()
    schema_path = project_root / "specs" / "001-chemo-biomarker-discovery" / "contracts" / f"{schema_name}.schema.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_type(value: any, expected_type: str) -> bool:
    """Validate that a value matches the expected JSON Schema type."""
    if expected_type == "string":
        return isinstance(value, str)
    elif expected_type == "number":
        return isinstance(value, (int, float))
    elif expected_type == "integer":
        return isinstance(value, int)
    elif expected_type == "boolean":
        return isinstance(value, bool)
    elif expected_type == "array":
        return isinstance(value, list)
    elif expected_type == "object":
        return isinstance(value, dict)
    return False

def validate_required_fields(data: dict, required_fields: list) -> list:
    """Check if all required fields are present in the data."""
    missing = []
    for field in required_fields:
        if field not in data:
            missing.append(field)
    return missing

def validate_data_against_schema(data: dict, schema: dict) -> bool:
    """Validate a data object against a schema definition."""
    if schema.get("type") != "object" or not isinstance(data, dict):
        return False
    
    required = schema.get("required", [])
    missing = validate_required_fields(data, required)
    if missing:
        return False
    
    properties = schema.get("properties", {})
    for key, value in data.items():
        if key in properties:
            prop_schema = properties[key]
            if "type" in prop_schema:
                if not validate_type(value, prop_schema["type"]):
                    return False
            if prop_schema.get("type") == "array" and "items" in prop_schema:
                item_schema = prop_schema["items"]
                if "type" in item_schema:
                    if not all(validate_type(item, item_schema["type"]) for item in value):
                        return False
    return True

def test_schemas_exist():
    """Test that all required schema files exist."""
    schema_names = ["dataset", "model_output", "gene_panel"]
    for name in schema_names:
        schema_path = get_project_root() / "specs" / "001-chemo-biomarker-discovery" / "contracts" / f"{name}.schema.yaml"
        assert schema_path.exists(), f"Schema file missing: {schema_path}"

def test_schemas_load_valid_yaml():
    """Test that all schema files are valid YAML."""
    schema_names = ["dataset", "model_output", "gene_panel"]
    for name in schema_names:
        schema = load_schema(name)
        assert isinstance(schema, dict), f"Schema {name} did not load as a dictionary"
        assert "properties" in schema, f"Schema {name} missing 'properties' key"

def test_dataset_schema_structure():
    """Test the specific structure of the dataset schema."""
    schema = load_schema("dataset")
    assert "sample_id" in schema["properties"]
    assert "tumor_type" in schema["properties"]
    assert "response_label" in schema["properties"]
    assert "expression_vector" in schema["properties"]
    assert schema["properties"]["expression_vector"]["type"] == "array"

def test_model_output_schema_structure():
    """Test the specific structure of the model output schema."""
    schema = load_schema("model_output")
    assert "cancer_type" in schema["properties"]
    assert "alpha" in schema["properties"]
    assert "lambda" in schema["properties"]
    assert "coefficients" in schema["properties"]
    assert "cross_val_auc" in schema["properties"]

def test_meta_analysis_schema_structure():
    """Test the specific structure of the gene panel schema."""
    schema = load_schema("gene_panel")
    assert "gene_symbol" in schema["properties"]
    assert "meta_p_value" in schema["properties"]
    assert "log2FC_mean" in schema["properties"]
    assert "selected" in schema["properties"]
    assert schema["properties"]["selected"]["type"] == "boolean"

def test_sample_data_validation():
    """Test that sample data conforms to the dataset schema."""
    schema = load_schema("dataset")
    sample_data = {
        "sample_id": "TCGA-AB-1234",
        "tumor_type": "BRCA",
        "response_label": "Responder",
        "expression_vector": [1.2, 3.4, 5.6]
    }
    assert validate_data_against_schema(sample_data, schema)

def test_invalid_data_catches_error():
    """Test that invalid data is correctly rejected."""
    schema = load_schema("dataset")
    invalid_data = {
        "sample_id": 123,  # Should be string
        "tumor_type": "BRCA",
        "response_label": "Responder",
        "expression_vector": [1.2, 3.4, 5.6]
    }
    assert not validate_data_against_schema(invalid_data, schema)

    missing_field_data = {
        "sample_id": "TCGA-AB-1234",
        "tumor_type": "BRCA",
        # Missing response_label
        "expression_vector": [1.2, 3.4, 5.6]
    }
    assert not validate_data_against_schema(missing_field_data, schema)