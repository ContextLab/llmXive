"""
Contract tests for dataset and output JSON schemas.
Validates sample JSON files against the defined schemas using the jsonschema library.
"""
import json
import os
import pytest
from jsonschema import validate, ValidationError, Draft7Validator

# Path constants relative to project root
CONTRACTS_DIR = "contracts"
DATASET_SCHEMA_PATH = os.path.join(CONTRACTS_DIR, "dataset.schema.yaml")
OUTPUT_SCHEMA_PATH = os.path.join(CONTRACTS_DIR, "output.schema.yaml")

import yaml

def load_yaml_schema(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def test_dataset_schema_valid():
    """Test that a valid M4 series object passes the dataset schema."""
    schema = load_yaml_schema(DATASET_SCHEMA_PATH)
    valid_data = {
        "id": "M1",
        "frequency": "Monthly",
        "seasonality": 12,
        "values": [10.5, 11.2, 10.8, 12.1, 11.5]
    }
    
    # Validate
    validate(instance=valid_data, schema=schema)

def test_dataset_schema_invalid_missing_field():
    """Test that a dataset object missing a required field fails."""
    schema = load_yaml_schema(DATASET_SCHEMA_PATH)
    invalid_data = {
        "id": "M1",
        "frequency": "Monthly",
        # Missing seasonality and values
        "values": [10.5, 11.2]
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)

def test_dataset_schema_invalid_type():
    """Test that a dataset object with wrong type fails."""
    schema = load_yaml_schema(DATASET_SCHEMA_PATH)
    invalid_data = {
        "id": "M1",
        "frequency": 123,  # Should be string
        "seasonality": 12,
        "values": [10.5, 11.2]
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)

def test_output_schema_valid():
    """Test that a valid coverage result object passes the output schema."""
    schema = load_yaml_schema(OUTPUT_SCHEMA_PATH)
    valid_data = {
        "series_id": "M1",
        "model": "ARIMA",
        "horizon": 1,
        "nominal_coverage": 0.95,
        "empirical_coverage": 0.92,
        "deviation": 0.03
    }
    
    validate(instance=valid_data, schema=schema)

def test_output_schema_invalid_model():
    """Test that an output object with an invalid model name fails."""
    schema = load_yaml_schema(OUTPUT_SCHEMA_PATH)
    invalid_data = {
        "series_id": "M1",
        "model": "InvalidModel",  # Not in enum
        "horizon": 1,
        "nominal_coverage": 0.95,
        "empirical_coverage": 0.92,
        "deviation": 0.03
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)

def test_output_schema_invalid_horizon():
    """Test that an output object with horizon outside range fails."""
    schema = load_yaml_schema(OUTPUT_SCHEMA_PATH)
    invalid_data = {
        "series_id": "M1",
        "model": "ARIMA",
        "horizon": 20,  # Max is 12
        "nominal_coverage": 0.95,
        "empirical_coverage": 0.92,
        "deviation": 0.03
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)

def test_schemas_exist_and_loadable():
    """Verify that schema files exist and are valid YAML."""
    assert os.path.exists(DATASET_SCHEMA_PATH), f"Dataset schema not found at {DATASET_SCHEMA_PATH}"
    assert os.path.exists(OUTPUT_SCHEMA_PATH), f"Output schema not found at {OUTPUT_SCHEMA_PATH}"
    
    # Ensure they parse as valid YAML
    try:
        load_yaml_schema(DATASET_SCHEMA_PATH)
        load_yaml_schema(OUTPUT_SCHEMA_PATH)
    except yaml.YAMLError as e:
        pytest.fail(f"Schema file is not valid YAML: {e}")