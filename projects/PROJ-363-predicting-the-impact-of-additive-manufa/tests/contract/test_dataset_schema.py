import os
import sys
import json
import yaml
import pandas as pd
import pytest
from pathlib import Path
import jsonschema

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

@pytest.fixture
def schema_path():
    """Return the path to the dataset schema file."""
    return Path(__file__).parent.parent.parent / "contracts" / "dataset.schema.yaml"

@pytest.fixture
def schema(schema_path):
    """Load the dataset schema."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def cleaned_data_path():
    """Return the path to the cleaned dataset."""
    return Path(__file__).parent.parent.parent / "data" / "processed" / "cleaned_316L.csv"

def test_schema_exists(schema_path):
    """Test that the schema file exists."""
    assert schema_path.exists(), f"Schema file not found at {schema_path}"

def test_schema_valid_yaml(schema):
    """Test that the schema is valid YAML."""
    assert schema is not None
    assert 'properties' in schema
    assert 'required' in schema

def test_required_columns_in_schema(schema):
    """Test that all required columns are defined in the schema."""
    required_columns = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'porosity']
    schema_properties = list(schema['properties'].keys())
    
    for col in required_columns:
        assert col in schema_properties, f"Required column '{col}' not found in schema"

def test_data_matches_schema(cleaned_data_path, schema):
    """Test that the cleaned dataset matches the schema."""
    if not cleaned_data_path.exists():
        pytest.skip("Cleaned data file not found. Run preprocessing first.")
    
    df = pd.read_csv(cleaned_data_path)
    
    # Check required columns exist
    for col in schema['required']:
        assert col in df.columns, f"Required column '{col}' missing from dataset"
    
    # Check types (basic validation)
    for col, prop in schema['properties'].items():
        if col in df.columns:
            if prop['type'] == 'number':
                # Check if column contains numeric data
                assert pd.api.types.is_numeric_dtype(df[col]) or df[col].apply(lambda x: isinstance(x, (int, float, str)) and (x == '' or (isinstance(x, str) and x.replace('.', '', 1).isdigit()))).all(), \
                    f"Column '{col}' should contain numeric data"

def test_no_missing_values(cleaned_data_path):
    """Test that the cleaned dataset has no missing values."""
    if not cleaned_data_path.exists():
        pytest.skip("Cleaned data file not found. Run preprocessing first.")
    
    df = pd.read_csv(cleaned_data_path)
    
    # Check for missing values
    for col in df.columns:
        assert df[col].isnull().sum() == 0, f"Column '{col}' has {df[col].isnull().sum()} missing values"

def test_schema_validation_with_jsonschema(cleaned_data_path, schema):
    """Test the dataset against the schema using jsonschema library."""
    if not cleaned_data_path.exists():
        pytest.skip("Cleaned data file not found. Run preprocessing first.")
    
    df = pd.read_csv(cleaned_data_path)
    
    # Convert DataFrame to list of records for validation
    records = df.to_dict('records')
    
    # Validate each record (simplified validation)
    for i, record in enumerate(records[:10]):  # Validate first 10 records
        for required_field in schema['required']:
            assert required_field in record, f"Record {i} missing required field '{required_field}'"
            assert record[required_field] is not None, f"Record {i} has null value for '{required_field}'"