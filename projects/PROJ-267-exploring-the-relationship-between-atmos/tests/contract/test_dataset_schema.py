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
    
    required_columns = schema.get('required_columns', [])
    missing_cols = [col for col in required_columns if col not in df.columns]
    assert not missing_cols, f"Missing required columns: {missing_cols}"
    
    # Check for NaN in required columns
    for col in required_columns:
        if df[col].isna().any():
            count = df[col].isna().sum()
            raise AssertionError(f"NaN values found in required column '{col}' ({count} missing)")

def test_data_types():
    """Test that data types match the schema definitions."""
    if not MERGED_FILE.exists():
        pytest.skip("Merged CSV file not found. Run preprocessing first.")
    
    df = pd.read_csv(MERGED_FILE)
    schema = load_schema()
    types = schema.get('types', {})
    
    for col, expected_type in types.items():
        if col in df.columns:
            if expected_type == 'float':
                assert pd.api.types.is_float_dtype(df[col]), f"Column '{col}' is not float (got {df[col].dtype})"
            elif expected_type == 'integer':
                assert pd.api.types.is_integer_dtype(df[col]), f"Column '{col}' is not integer (got {df[col].dtype})"
            elif expected_type == 'string':
                assert pd.api.types.is_string_dtype(df[col]), f"Column '{col}' is not string (got {df[col].dtype})"

def test_row_count_minimum():
    """Test that the dataset contains a reasonable number of rows (min 12 for 1 year)."""
    if not MERGED_FILE.exists():
        pytest.skip("Merged CSV file not found. Run preprocessing first.")
    
    df = pd.read_csv(MERGED_FILE)
    assert len(df) >= 12, f"Dataset has only {len(df)} rows; expected at least 12 (1 year of monthly data)."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])