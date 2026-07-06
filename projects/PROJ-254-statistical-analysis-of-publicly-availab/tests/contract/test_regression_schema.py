"""
Contract test for regression output schema.

Validates that the regression output file adheres to the schema defined in
tests/contract/schemas/regression_schema.yaml.
"""
import json
import os
import pytest
import yaml
from pathlib import Path

# Ensure the test can find the schema relative to its location
BASE_DIR = Path(__file__).parent
SCHEMA_PATH = BASE_DIR / "schemas" / "regression_schema.yaml"
OUTPUT_PATH = Path(__file__).parent.parent.parent / "data" / "derived" / "regression_results.json"


def load_schema():
    """Load the YAML schema definition."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_regression_output():
    """Load the generated regression results JSON."""
    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(
            f"Regression output file not found at {OUTPUT_PATH}. "
            "Ensure regression analysis has been run."
        )
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_schema(data, schema, path="root"):
    """
    Recursively validate data against a JSON schema definition.
    
    Supports 'type', 'required', and 'properties' keys.
    """
    if schema.get("type") == "object":
        if not isinstance(data, dict):
            raise AssertionError(f"{path}: Expected object, got {type(data).__name__}")
        
        required_fields = schema.get("required", [])
        properties = schema.get("properties", {})
        
        for field in required_fields:
            if field not in data:
                raise AssertionError(f"{path}: Missing required field '{field}'")
        
        for field, value in data.items():
            if field in properties:
                validate_schema(value, properties[field], f"{path}.{field}")
            else:
                # Optional fields not in schema are allowed unless strict mode is on
                # For this contract test, we only validate defined fields
                pass

    elif schema.get("type") == "number":
        if not isinstance(data, (int, float)):
            raise AssertionError(f"{path}: Expected number, got {type(data).__name__}")
    
    elif schema.get("type") == "string":
        if not isinstance(data, str):
            raise AssertionError(f"{path}: Expected string, got {type(data).__name__}")
    
    elif schema.get("type") == "array":
        if not isinstance(data, list):
            raise AssertionError(f"{path}: Expected array, got {type(data).__name__}")
        items_schema = schema.get("items", {})
        for i, item in enumerate(data):
            validate_schema(item, items_schema, f"{path}[{i}]")


def test_regression_schema_validation():
    """
    Contract test: Validates that regression_results.json matches the schema.
    
    This test ensures that the output of the regression pipeline (T027)
    strictly adheres to the expected structure defined in the contract.
    """
    schema = load_schema()
    data = load_regression_output()
    
    try:
        validate_schema(data, schema)
    except AssertionError as e:
        pytest.fail(f"Schema validation failed: {e}")
    
    # Additional specific checks if needed beyond generic schema
    # e.g., checking that p-value is between 0 and 1
    if "slope" in data and "p_value" in data:
        if not (0.0 <= data["p_value"] <= 1.0):
            pytest.fail(f"p_value {data['p_value']} is not in range [0, 1]")
    
    assert True, "Regression output schema validation passed."
