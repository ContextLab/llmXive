"""
Contract test for merged CSV schema validation.
Validates that data/processed/merged_monthly.csv conforms to contracts/dataset.schema.yaml.
"""
import pandas as pd
import yaml
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SCHEMA_FILE = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
MERGED_FILE = DATA_PROCESSED_DIR / "merged_monthly.csv"

def load_schema():
    """Load the dataset schema from YAML."""
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_FILE}")
    with open(SCHEMA_FILE, 'r') as f:
        return yaml.safe_load(f)

def test_merged_csv_exists():
    """Test that the merged CSV file exists."""
    assert MERGED_FILE.exists(), f"Merged CSV file not found: {MERGED_FILE}. Run preprocessing (T017) first."

def test_merged_csv_schema():
    """Test that the merged CSV file conforms to the schema."""
    if not MERGED_FILE.exists():
        pytest.skip("Merged CSV file not found. Run preprocessing first.")
    
    df = pd.read_csv(MERGED_FILE)
    schema = load_schema()
    
    # Extract required fields from the schema properties
    # The schema provided in T013 uses 'properties' for required fields
    required_fields = schema.get('properties', {}).keys()
    
    # Check for missing columns
    missing_cols = [col for col in required_fields if col not in df.columns]
    assert not missing_cols, f"Missing required columns defined in schema: {missing_cols}"
    
    # Check for NaN in required columns
    for col in required_fields:
        if col in df.columns and df[col].isna().any():
            count = df[col].isna().sum()
            raise AssertionError(f"NaN values found in required column '{col}' ({count} missing)")

def test_data_types():
    """Test that data types match the schema definitions (number -> float)."""
    if not MERGED_FILE.exists():
        pytest.skip("Merged CSV file not found. Run preprocessing first.")
    
    df = pd.read_csv(MERGED_FILE)
    schema = load_schema()
    properties = schema.get('properties', {})
    
    for col, definition in properties.items():
        if col in df.columns:
            expected_type = definition.get('type')
            if expected_type == 'number':
                # Pandas CSV reader might read as object if mixed, but should be float/numeric
                if not pd.api.types.is_numeric_dtype(df[col]):
                    # Allow object if it contains numeric strings, but prefer numeric
                    try:
                        pd.to_numeric(df[col], errors='raise')
                    except (ValueError, TypeError):
                        raise AssertionError(f"Column '{col}' is expected to be numeric (type: {expected_type}) but contains non-numeric values.")
            elif expected_type == 'string':
                # Pandas default for strings is object or string
                if not pd.api.types.is_string_dtype(df[col]) and not pd.api.types.is_object_dtype(df[col]):
                    raise AssertionError(f"Column '{col}' is expected to be string (type: {expected_type}) but is {df[col].dtype}")

def test_row_count_minimum():
    """Test that the dataset contains a reasonable number of rows (min 12 for 1 year)."""
    if not MERGED_FILE.exists():
        pytest.skip("Merged CSV file not found. Run preprocessing first.")
    
    df = pd.read_csv(MERGED_FILE)
    assert len(df) >= 12, f"Dataset has only {len(df)} rows; expected at least 12 (1 year of monthly data)."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])