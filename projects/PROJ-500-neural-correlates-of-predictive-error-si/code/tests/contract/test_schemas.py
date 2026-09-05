import json
import os
import pytest
from pathlib import Path
import yaml

def load_schema(schema_path: Path) -> dict:
    """Load a JSON schema from YAML file."""
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_data_against_schema(data: dict, schema: dict) -> tuple[bool, list]:
    """Simple validation of data against schema (basic implementation)."""
    errors = []

    # Check required fields
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Check property types
    properties = schema.get("properties", {})
    for key, value in data.items():
        if key in properties:
            prop_schema = properties[key]
            expected_type = prop_schema.get("type")
            if expected_type == "string" and not isinstance(value, str):
                errors.append(f"Field '{key}' should be string, got {type(value)}")
            elif expected_type == "integer" and not isinstance(value, int):
                errors.append(f"Field '{key}' should be integer, got {type(value)}")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"Field '{key}' should be number, got {type(value)}")

    return len(errors) == 0, errors

def test_aligned_data_schema_exists():
    """Test that aligned_data schema file exists."""
    schema_path = Path("code/contracts/aligned_data.schema.yaml")
    assert schema_path.exists(), "aligned_data.schema.yaml not found"

def test_model_output_schema_exists():
    """Test that model_output schema file exists."""
    schema_path = Path("code/contracts/model_output.schema.yaml")
    assert schema_path.exists(), "model_output.schema.yaml not found"

def test_aligned_data_schema_valid():
    """Test that aligned_data schema is valid YAML."""
    schema_path = Path("code/contracts/aligned_data.schema.yaml")
    schema = load_schema(schema_path)
    assert "required" in schema
    assert "properties" in schema
    assert "subject_id" in schema["properties"]

def test_model_output_schema_valid():
    """Test that model_output schema is valid YAML."""
    schema_path = Path("code/contracts/model_output.schema.yaml")
    schema = load_schema(schema_path)
    assert "required" in schema
    assert "properties" in schema
    assert "coefficients" in schema["properties"]
