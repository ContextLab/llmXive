"""
Contract test: Validate model output schema against contracts/model_output.schema.yaml.

This test verifies that the analysis pipeline produces a JSON output containing
all required keys with correct types as defined in the schema.
"""
import os
import json
import pytest
import yaml
from pathlib import Path

# Path to the schema file
SCHEMA_PATH = Path("contracts/model_output.schema.yaml")
OUTPUT_PATH = Path("data/processed/model_output.json")

@pytest.fixture
def schema():
    """Load the JSON schema from the YAML file."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}. Run T024b-SchemaDef first.")
    
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def model_output():
    """Locate and load the model output file."""
    if not OUTPUT_PATH.exists():
        pytest.skip(f"Model output not found at {OUTPUT_PATH}. Run analysis pipeline first.")
    
    with open(OUTPUT_PATH, "r") as f:
        return json.load(f)

def test_schema_file_exists(schema):
    """Verify that the schema file is valid YAML and loads correctly."""
    assert schema is not None
    assert "required" in schema
    assert "properties" in schema

def test_model_output_contains_required_keys(model_output, schema):
    """Validate that model output JSON contains all required keys defined in the schema."""
    required_keys = schema.get("required", [])
    for key in required_keys:
        assert key in model_output, f"Missing required key in model output: {key}"

def test_model_output_types_match_schema(model_output, schema):
    """Validate that the types of values in model output match the schema definitions."""
    properties = schema.get("properties", {})
    
    # Check coefficients
    if "coefficients" in properties:
        assert isinstance(model_output.get("coefficients"), dict), \
            "coefficients must be a dict"
        # Verify all values are numeric
        for k, v in model_output["coefficients"].items():
            assert isinstance(v, (int, float)), \
                f"Value for coefficient '{k}' must be numeric, got {type(v)}"

    # Check p_values
    if "p_values" in properties:
        assert isinstance(model_output.get("p_values"), dict), \
            "p_values must be a dict"
        for k, v in model_output["p_values"].items():
            assert isinstance(v, (int, float)), \
                f"Value for p_value '{k}' must be numeric, got {type(v)}"

    # Check vif
    if "vif" in properties:
        assert isinstance(model_output.get("vif"), dict), \
            "vif must be a dict"
        for k, v in model_output["vif"].items():
            assert isinstance(v, (int, float)), \
                f"Value for VIF '{k}' must be numeric, got {type(v)}"

    # Check ci_width
    if "ci_width" in properties:
        ci_width = model_output.get("ci_width")
        assert isinstance(ci_width, (int, float)), \
            f"ci_width must be numeric, got {type(ci_width)}"
        assert ci_width >= 0, "ci_width must be non-negative"

    # Check model_type
    if "model_type" in properties:
        model_type = model_output.get("model_type")
        assert isinstance(model_type, str), \
            f"model_type must be a string, got {type(model_type)}"
        # Validate allowed values if specified in schema (optional)
        # For now, we just ensure it's a string as per requirement

def test_no_additional_properties(model_output, schema):
    """Ensure model output does not contain keys not defined in the schema (if strict)."""
    if schema.get("additionalProperties") is False:
        allowed_keys = set(schema.get("properties", {}).keys())
        actual_keys = set(model_output.keys())
        extra_keys = actual_keys - allowed_keys
        assert not extra_keys, f"Model output contains unexpected keys: {extra_keys}"