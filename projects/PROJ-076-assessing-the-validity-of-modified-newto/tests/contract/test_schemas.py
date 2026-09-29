"""
Contract tests for dataset schemas.
Validates that data conforms to the defined schema in contracts/dataset.schema.yaml.
"""
import os
import pytest
import pandas as pd
import yaml
from pathlib import Path

SCHEMA_PATH = Path("contracts/dataset.schema.yaml")

def load_schema():
    """Load the JSON schema from file."""
    if not SCHEMA_PATH.exists():
        pytest.skip(f"Schema file not found: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def validate_dataframe(df: pd.DataFrame, schema: dict):
    """Validate a dataframe against a schema."""
    required_columns = schema.get('required_columns', [])
    for col in required_columns:
        if col not in df.columns:
            raise AssertionError(f"Missing required column: {col}")
    
    # Check types if defined
    types = schema.get('column_types', {})
    for col, expected_type in types.items():
        if col in df.columns:
            # Simple type check
            if expected_type == 'float':
                if not pd.api.types.is_float_dtype(df[col]):
                    raise AssertionError(f"Column {col} should be float")
            elif expected_type == 'int':
                if not pd.api.types.is_integer_dtype(df[col]):
                    raise AssertionError(f"Column {col} should be int")
            elif expected_type == 'str':
                if not pd.api.types.is_string_dtype(df[col]):
                    raise AssertionError(f"Column {col} should be str")

@pytest.fixture
def sample_galaxy_data():
    """Create a sample dataframe for testing."""
    return pd.DataFrame({
        'galaxy_name': ['NGC1234', 'NGC5678'],
        'radial_distance': [1.0, 2.0, 3.0, 4.0],
        'velocity': [100.0, 150.0, 180.0, 200.0],
        'uncertainty': [5.0, 5.0, 5.0, 5.0],
        'inclination': [45.0, 60.0]
    })

def test_schema_loading():
    """Test that schema can be loaded."""
    schema = load_schema()
    assert schema is not None
    assert 'required_columns' in schema

def test_galaxy_data_validation(sample_galaxy_data):
    """Test validation of galaxy data."""
    schema = load_schema()
    validate_dataframe(sample_galaxy_data, schema)
    # If no exception, it passed
    assert True
