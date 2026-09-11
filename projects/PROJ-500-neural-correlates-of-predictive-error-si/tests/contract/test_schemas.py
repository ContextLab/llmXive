import json
import os
import pytest
from pathlib import Path
import yaml

# Path to the schema files
SCHEMAS_DIR = Path(__file__).parent.parent.parent / "contracts"
ALIGNED_DATA_SCHEMA_PATH = SCHEMAS_DIR / "aligned_data.schema.yaml"
MODEL_OUTPUT_SCHEMA_PATH = SCHEMAS_DIR / "model_output.schema.yaml"

def load_schema(schema_path: Path) -> dict:
    """Load a JSON/YAML schema from disk."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    
    with open(schema_path, "r") as f:
        if schema_path.suffix in [".yaml", ".yml"]:
            return yaml.safe_load(f)
        else:
            return json.load(f)

def validate_data_against_schema(data: dict, schema: dict) -> bool:
    """
    Basic validation of data against a schema (without external jsonschema lib).
    Checks required fields and basic types.
    """
    # Check required fields
    required = schema.get("required", [])
    for field in required:
        if field not in data:
            raise AssertionError(f"Missing required field: {field}")
    
    # Check types of required fields
    properties = schema.get("properties", {})
    
    # Generic type checking based on schema type definitions
    for field in required:
        if field in data:
            value = data[field]
            prop_def = properties.get(field, {})
            expected_type = prop_def.get("type")
            
            if expected_type == "object":
                if not isinstance(value, dict):
                    raise AssertionError(f"{field} must be an object/dict")
            elif expected_type == "array":
                if not isinstance(value, list):
                    raise AssertionError(f"{field} must be an array/list")
            elif expected_type == "string":
                if not isinstance(value, str):
                    raise AssertionError(f"{field} must be a string")
            elif expected_type == "number":
                if not isinstance(value, (int, float)):
                    raise AssertionError(f"{field} must be a number")
            elif expected_type == "integer":
                if not isinstance(value, int):
                    raise AssertionError(f"{field} must be an integer")
            # Boolean check
            elif expected_type == "boolean":
                if not isinstance(value, bool):
                    raise AssertionError(f"{field} must be a boolean")

    return True

# --- Tests for T009a: aligned_data.schema.yaml ---

def test_aligned_data_schema_exists():
    """Verify that the aligned_data.schema.yaml file exists."""
    assert ALIGNED_DATA_SCHEMA_PATH.exists(), f"Schema file missing: {ALIGNED_DATA_SCHEMA_PATH}"

def test_aligned_data_schema_valid():
    """Verify that the aligned_data schema file is valid YAML/JSON."""
    try:
        schema = load_schema(ALIGNED_DATA_SCHEMA_PATH)
        assert "required" in schema, "Schema missing 'required' field"
        assert "properties" in schema, "Schema missing 'properties' field"
        
        # Verify specific required fields from T009a
        required_fields = ["subject_id", "block_id", "mmn_amplitude", "source_window_start_trial", "analysis_mode"]
        for field in required_fields:
            assert field in schema["required"], f"Required field '{field}' missing from schema"
            assert field in schema["properties"], f"Property definition for '{field}' missing from schema"
    except Exception as e:
        pytest.fail(f"Aligned data schema validation failed: {e}")

def test_aligned_data_sample_data_valid():
    """Test that a sample aligned data record conforms to the schema."""
    schema = load_schema(ALIGNED_DATA_SCHEMA_PATH)
    
    sample_data = {
        "subject_id": "sub-001",
        "block_id": 1,
        "mmn_amplitude": 2.34,
        "source_window_start_trial": 50,
        "analysis_mode": "error_signal",
        "accuracy": 0.85
    }
    
    try:
        validate_data_against_schema(sample_data, schema)
    except AssertionError as e:
        pytest.fail(f"Sample data failed aligned data schema validation: {e}")

# --- Tests for T009b: model_output.schema.yaml ---

def test_model_output_schema_exists():
    """Verify that the model_output.schema.yaml file exists."""
    assert MODEL_OUTPUT_SCHEMA_PATH.exists(), f"Schema file missing: {MODEL_OUTPUT_SCHEMA_PATH}"

def test_model_output_schema_valid():
    """Verify that the model_output schema file is valid YAML/JSON."""
    try:
        schema = load_schema(MODEL_OUTPUT_SCHEMA_PATH)
        assert "required" in schema, "Schema missing 'required' field"
        assert "properties" in schema, "Schema missing 'properties' field"
        
        # Verify specific required fields from T009b
        required_fields = ["coefficients", "p_values", "fdr_p_values", "permutation_p_value"]
        for field in required_fields:
            assert field in schema["required"], f"Required field '{field}' missing from schema"
            assert field in schema["properties"], f"Property definition for '{field}' missing from schema"
    except Exception as e:
        pytest.fail(f"Model output schema validation failed: {e}")

def test_model_output_sample_data_valid():
    """Test that a sample model output conforms to the schema."""
    schema = load_schema(MODEL_OUTPUT_SCHEMA_PATH)
    
    sample_data = {
        "coefficients": {
            "Intercept": 0.5,
            "Accuracy": 0.12,
            "Learning_Phase[T.Late]": -0.05
        },
        "p_values": {
            "Intercept": 0.001,
            "Accuracy": 0.042,
            "Learning_Phase[T.Late]": 0.089
        },
        "fdr_p_values": {
            "Intercept": 0.0015,
            "Accuracy": 0.063,
            "Learning_Phase[T.Late]": 0.089
        },
        "permutation_p_value": 0.032,
        "model_info": {
            "formula": "MMN_Amplitude ~ Accuracy + Learning_Phase + (1|Subject)",
            "n_observations": 1500,
            "n_groups": 20
        }
    }
    
    try:
        validate_data_against_schema(sample_data, schema)
    except AssertionError as e:
        pytest.fail(f"Sample data failed model output schema validation: {e}")