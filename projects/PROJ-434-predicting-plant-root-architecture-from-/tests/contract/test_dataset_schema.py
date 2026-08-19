"""
Contract test for the merged dataset schema.
Verifies that the output of the US1 ingestion pipeline matches the schema defined in specs/001-predict-root-architecture/contracts/dataset.schema.yaml.
"""
import pytest
import pandas as pd
from pathlib import Path
import yaml

# Path to the schema definition file (created in T007a)
SCHEMA_PATH = Path("specs/001-predict-root-architecture/contracts/dataset.schema.yaml")

def load_schema():
    """Load the expected schema from the YAML file."""
    if not SCHEMA_PATH.exists():
        pytest.skip(f"Schema file not found at {SCHEMA_PATH}. Ensure T007a is complete.")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def test_merged_dataset_schema():
    """
    Verify that the merged dataset has the required columns, types, and constraints
    as defined in the contract schema.
    """
    data_path = Path("data/processed/merged_dataset.csv")
    if not data_path.exists():
        pytest.skip("Dataset not generated yet. Run T017 first.")
    
    df = pd.read_csv(data_path)
    schema = load_schema()
    required_fields = schema.get('required_fields', {})
    
    # 1. Check for presence of all required columns
    missing_columns = set(required_fields.keys()) - set(df.columns)
    assert not missing_columns, f"Missing required columns: {missing_columns}"

    # 2. Check for non-null values in critical columns (as per schema constraints)
    for col, constraints in required_fields.items():
        if constraints.get('nullable') is False:
            assert df[col].notnull().all(), f"Column '{col}' contains null values, but schema requires non-null."
        
        # Optional: Check dtype if specified in schema
        if 'dtype' in constraints:
            expected_dtype = constraints['dtype']
            if expected_dtype == 'float':
                assert pd.api.types.is_float_dtype(df[col]) or pd.api.types.is_integer_dtype(df[col]), \
                    f"Column '{col}' is not numeric, expected float/int."
            elif expected_dtype == 'string':
                assert pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]), \
                    f"Column '{col}' is not string-like."

def test_excluded_species_summary_schema():
    """
    Verify the schema of the excluded species summary.
    """
    data_path = Path("data/processed/excluded_species_summary.csv")
    if not data_path.exists():
        pytest.skip("Excluded species summary not generated yet. Run T017 first.")
    
    df = pd.read_csv(data_path)
    schema = load_schema()
    excluded_fields = schema.get('excluded_species_fields', {})
    
    required_cols = list(excluded_fields.keys())
    missing = set(required_cols) - set(df.columns)
    assert not missing, f"Missing columns in excluded species summary: {missing}"

    # Check that reason column is populated
    assert df['reason'].notnull().all(), "Column 'reason' in excluded species summary contains nulls."
    assert df['observation_count'].notnull().all(), "Column 'observation_count' in excluded species summary contains nulls."

def test_data_integrity_constraints():
    """
    Verify specific data integrity constraints mentioned in the task description
    (e.g., root_depth > 0, pH range).
    """
    data_path = Path("data/processed/merged_dataset.csv")
    if not data_path.exists():
        pytest.skip("Dataset not generated yet.")
    
    df = pd.read_csv(data_path)
    
    # Constraint: root_depth must be positive
    assert (df['root_depth'] > 0).all(), "Found root_depth values <= 0."
    
    # Constraint: pH must be between 3.0 and 9.0 (physically plausible)
    assert (df['soil_ph'] >= 3.0).all(), "Found soil_ph values < 3.0."
    assert (df['soil_ph'] <= 9.0).all(), "Found soil_ph values > 9.0."