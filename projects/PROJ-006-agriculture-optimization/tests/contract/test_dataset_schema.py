"""
Contract test skeleton for dataset schema (TDD).

This test validates that the analysis dataset conforms to the 
contracts/dataset.schema.yaml definition.

Note: This test will fail until T015-T022 are implemented and 
data/processed/analysis_dataset.csv exists.
"""
import os
import pytest
from pathlib import Path
import yaml
import jsonschema
import pandas as pd

# Path constants relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "analysis_dataset.csv"

def load_schema():
    """Load the dataset schema from YAML."""
    if not SCHEMA_PATH.exists():
        pytest.skip(f"Schema file not found: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def load_data():
    """Load the analysis dataset CSV."""
    if not DATA_PATH.exists():
        pytest.skip(f"Data file not found: {DATA_PATH}")
    return pd.read_csv(DATA_PATH)

@pytest.mark.contract
def test_schema_file_exists():
    """Assert that the schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"

@pytest.mark.contract
def test_schema_is_valid_yaml():
    """Assert that the schema file is valid YAML."""
    try:
        schema = load_schema()
        assert isinstance(schema, dict), "Schema must be a dictionary"
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in schema: {e}")

@pytest.mark.contract
def test_data_file_exists():
    """Assert that the analysis dataset exists."""
    assert DATA_PATH.exists(), f"Analysis dataset missing: {DATA_PATH}"

@pytest.mark.contract
def test_data_has_required_columns():
    """Assert that the dataset contains all required columns from the schema."""
    schema = load_schema()
    df = load_data()
    
    # Extract required columns from schema (assumes 'properties' or 'columns' key)
    # Adjust based on actual schema structure (e.g., jsonschema vs custom yaml)
    required_columns = []
    if 'properties' in schema:
        required_columns = list(schema['properties'].keys())
    elif 'columns' in schema:
        required_columns = [col['name'] for col in schema['columns']]
    
    missing = set(required_columns) - set(df.columns)
    assert not missing, f"Dataset missing required columns: {missing}"

@pytest.mark.contract
def test_data_passes_schema_validation():
    """Assert that the dataset validates against the schema."""
    schema = load_schema()
    df = load_data()
    
    # Convert dataframe to list of dicts for jsonschema validation
    records = df.to_dict(orient='records')
    
    # Basic validation: check types and nulls if schema defines them
    # This is a skeleton; full validation depends on schema structure
    if 'required' in schema:
        for field in schema['required']:
            if field in df.columns:
                assert not df[field].isnull().any(), f"Field '{field}' contains nulls"