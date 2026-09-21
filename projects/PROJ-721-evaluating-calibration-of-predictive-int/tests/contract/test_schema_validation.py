"""
Contract tests to validate that generated JSON data conforms to the defined schemas.
These tests ensure that the data produced by the pipeline matches the expected structure.
"""
import json
import os
import pytest
import yaml
from jsonschema import validate, ValidationError

# Paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SCHEMAS_DIR = os.path.join(PROJECT_ROOT, "contracts")

def load_schema(schema_name: str) -> dict:
    """Load a JSON Schema from the contracts directory."""
    schema_path = os.path.join(SCHEMAS_DIR, schema_name)
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_dataset_schema_valid():
    """Test that a valid M4 series sample conforms to dataset.schema.yaml."""
    schema = load_schema("dataset.schema.yaml")
    
    # Valid sample data
    valid_data = {
        "id": "M4_1001",
        "frequency": "Monthly",
        "seasonality": 12,
        "values": [10.5, 11.2, 10.8, 12.1, 11.5, 11.9, 12.3, 12.0, 11.8, 12.5, 12.1, 12.4]
    }

    try:
        validate(instance=valid_data, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Valid data failed schema validation: {e.message}")

def test_dataset_schema_invalid_missing_field():
    """Test that data missing a required field fails validation."""
    schema = load_schema("dataset.schema.yaml")
    
    invalid_data = {
        "id": "M4_1001",
        "frequency": "Monthly",
        # Missing 'seasonality' and 'values'
    }

    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)

def test_dataset_schema_invalid_type():
    """Test that data with incorrect types fails validation."""
    schema = load_schema("dataset.schema.yaml")
    
    invalid_data = {
        "id": "M4_1001",
        "frequency": "Monthly",
        "seasonality": "twelve",  # Should be integer
        "values": [10.5, 11.2]
    }

    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)

def test_output_schema_valid():
    """Test that a valid coverage result sample conforms to output.schema.yaml."""
    schema = load_schema("output.schema.yaml")
    
    valid_data = {
        "series_id": "M4_1001",
        "model": "ARIMA",
        "horizon": 1,
        "nominal_coverage": 0.95,
        "empirical_coverage": 0.94,
        "deviation": 0.01
    }

    try:
        validate(instance=valid_data, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Valid data failed schema validation: {e.message}")

def test_output_schema_invalid_coverage_range():
    """Test that coverage values outside [0, 1] fail validation."""
    schema = load_schema("output.schema.yaml")
    
    invalid_data = {
        "series_id": "M4_1001",
        "model": "ARIMA",
        "horizon": 1,
        "nominal_coverage": 1.5,  # Invalid: > 1
        "empirical_coverage": 0.94,
        "deviation": 0.01
    }

    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)

def test_output_schema_invalid_horizon_type():
    """Test that horizon as a string fails validation."""
    schema = load_schema("output.schema.yaml")
    
    invalid_data = {
        "series_id": "M4_1001",
        "model": "ARIMA",
        "horizon": "one",  # Should be integer
        "nominal_coverage": 0.95,
        "empirical_coverage": 0.94,
        "deviation": 0.01
    }

    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)