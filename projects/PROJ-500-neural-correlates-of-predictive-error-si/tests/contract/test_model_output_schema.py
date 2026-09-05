"""
Contract test for the model_output.schema.yaml.
Validates that the generated model output JSON conforms to the defined schema.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

# Import schema validation logic (using jsonschema if available, or manual check)
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

from src.utils.logging import get_logger

logger = get_logger(__name__)

SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "model_output.schema.yaml"

def load_schema():
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def generate_valid_sample_output():
    """Generates a sample output that should pass validation."""
    return {
        "coefficients": {
            "Intercept": 0.5,
            "Accuracy": 0.12,
            "Learning_Phase": -0.03
        },
        "p_values": {
            "Intercept": 0.001,
            "Accuracy": 0.045,
            "Learning_Phase": 0.12
        },
        "fdr_p_values": {
            "Intercept": 0.0015,
            "Accuracy": 0.067,
            "Learning_Phase": 0.18
        },
        "permutation_p_value": 0.042,
        "model_info": {
            "formula": "MMN_Amplitude ~ Accuracy + Learning_Phase + (1|Subject)",
            "n_observations": 1500,
            "n_groups": 30,
            "convergence": True,
            "aic": 1234.5,
            "bic": 1250.2
        }
    }

@pytest.fixture
def schema():
    return load_schema()

@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
def test_schema_loads_and_validates_valid_output(schema):
    """Test that a valid sample output passes the schema validation."""
    valid_output = generate_valid_sample_output()
    try:
        jsonschema.validate(instance=valid_output, schema=schema)
        logger.info("Valid output passed schema validation.")
    except jsonschema.ValidationError as e:
        pytest.fail(f"Valid output failed schema validation: {e.message}")

@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
def test_schema_rejects_missing_required_fields(schema):
    """Test that missing required fields cause validation failure."""
    invalid_output = {
        "coefficients": {"Intercept": 0.5},
        "p_values": {"Intercept": 0.001}
        # Missing fdr_p_values, permutation_p_value
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_output, schema=schema)

@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
def test_schema_rejects_invalid_types(schema):
    """Test that invalid types (e.g., string instead of number) cause failure."""
    invalid_output = generate_valid_sample_output()
    invalid_output["permutation_p_value"] = "not_a_number"
    
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_output, schema=schema)

@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
def test_schema_rejects_negative_p_values(schema):
    """Test that negative p-values are rejected."""
    invalid_output = generate_valid_sample_output()
    invalid_output["p_values"]["Accuracy"] = -0.05
    
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_output, schema=schema)

def test_schema_file_exists():
    """Ensure the schema file actually exists on disk."""
    assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"
    assert SCHEMA_PATH.stat().st_size > 0, "Schema file is empty"

def test_schema_is_valid_yaml():
    """Ensure the schema file is valid YAML."""
    try:
        load_schema()
    except yaml.YAMLError as e:
        pytest.fail(f"Schema file is not valid YAML: {e}")