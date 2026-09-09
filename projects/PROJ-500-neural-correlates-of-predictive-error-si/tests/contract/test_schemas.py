"""
Contract tests for data schemas (T012, T025).
Validates that data artifacts conform to defined YAML schemas.
"""
import json
import os
import pytest
from pathlib import Path
import yaml

# Project root is assumed to be the parent of 'code'
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

def load_schema(schema_name: str) -> dict:
    """Load a schema from the contracts directory."""
    schema_path = CONTRACTS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_data_against_schema(data: dict, schema: dict) -> bool:
    """
    Simple validation of data against a schema.
    Checks for required keys and basic type constraints.
    Note: This is a lightweight validator; for production, use jsonschema.
    """
    # Check required properties
    required = schema.get("required", [])
    for key in required:
        if key not in data:
            raise ValueError(f"Missing required field: {key}")
    
    # Check properties types
    properties = schema.get("properties", {})
    for key, value in data.items():
        if key in properties:
            prop_def = properties[key]
            prop_type = prop_def.get("type")
            
            if prop_type == "object":
                if not isinstance(value, dict):
                    raise ValueError(f"Field '{key}' must be an object/dict")
            elif prop_type == "number":
                if not isinstance(value, (int, float)):
                    raise ValueError(f"Field '{key}' must be a number")
            elif prop_type == "integer":
                if not isinstance(value, int):
                    raise ValueError(f"Field '{key}' must be an integer")
            elif prop_type == "string":
                if not isinstance(value, str):
                    raise ValueError(f"Field '{key}' must be a string")
            elif prop_type == "array":
                if not isinstance(value, list):
                    raise ValueError(f"Field '{key}' must be an array")
            
            # Check constraints
            if "minimum" in prop_def:
                if isinstance(value, (int, float)) and value < prop_def["minimum"]:
                    raise ValueError(f"Field '{key}' value {value} is below minimum {prop_def['minimum']}")
            if "maximum" in prop_def:
                if isinstance(value, (int, float)) and value > prop_def["maximum"]:
                    raise ValueError(f"Field '{key}' value {value} is above maximum {prop_def['maximum']}")
    
    return True

# --- T009a Tests ---
def test_aligned_data_schema_exists():
    """Verify that the aligned_data schema file exists."""
    schema_path = CONTRACTS_DIR / "aligned_data.schema.yaml"
    assert schema_path.exists(), f"Schema file missing: {schema_path}"

def test_aligned_data_schema_valid():
    """Verify that the aligned_data schema is valid YAML and has required fields."""
    schema = load_schema("aligned_data.schema.yaml")
    assert "required" in schema
    assert "properties" in schema
    # Specific fields check based on T009a description
    required_fields = ["subject_id", "block_id", "mmn_amplitude", "source_window_start_trial", "analysis_mode"]
    for field in required_fields:
        assert field in schema.get("properties", {}), f"Missing property {field} in aligned_data schema"

# --- T009b Tests ---
def test_model_output_schema_exists():
    """Verify that the model_output schema file exists."""
    schema_path = CONTRACTS_DIR / "model_output.schema.yaml"
    assert schema_path.exists(), f"Schema file missing: {schema_path}"

def test_model_output_schema_valid():
    """Verify that the model_output schema is valid YAML and has required fields."""
    schema = load_schema("model_output.schema.yaml")
    assert "required" in schema, "Schema missing 'required' list"
    assert "properties" in schema, "Schema missing 'properties' dict"
    
    # Specific fields check based on T009b description
    required_fields = ["coefficients", "p_values", "fdr_p_values", "permutation_p_value"]
    for field in required_fields:
        assert field in schema.get("properties", {}), f"Missing property {field} in model_output schema"
    
    # Validate structure of nested objects
    coeffs_def = schema["properties"]["coefficients"]
    assert coeffs_def.get("type") == "object"
    
    perm_def = schema["properties"]["permutation_p_value"]
    assert perm_def.get("type") == "number"
    assert perm_def.get("minimum") == 0
    assert perm_def.get("maximum") == 1