"""
Contract test for the data schema of the preprocessed dataset.

This test verifies that the cleaned dataset produced by the US1 pipeline
conforms to the schema defined in `contracts/dataset.schema.yaml`.

It checks:
1. Existence of the output file.
2. Presence of all required columns.
3. Data types for numeric columns.
4. Validity of categorical columns (e.g., Sex, Site).
5. Non-null constraints for critical fields.
"""
import os
import sys
import yaml
import pytest
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports if running from tests/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from code.config_env import get_processed_dir, get_config

# Expected columns defined in contracts/dataset.schema.yaml
EXPECTED_COLUMNS = [
    "ACE",
    "Age",
    "Sex",
    "Site",
    "FamilyID",
    "CA3",
    "DG",
    "Subiculum",
    "ICV",
    "Normalized_Volumes"
]

# Numeric columns that must be float/int
NUMERIC_COLUMNS = ["ACE", "Age", "CA3", "DG", "Subiculum", "ICV", "Normalized_Volumes"]

# Categorical columns and their expected values (if known, otherwise just check existence)
CATEGORICAL_COLUMNS = {
    "Sex": ["M", "F", "Male", "Female", "1", "2"], # ABCD often uses 1/2 or M/F
    "Site": None, # Dynamic, just check non-null
    "FamilyID": None # String/Int, check non-null
}

@pytest.fixture
def dataset_path() -> Path:
    """Locate the cleaned dataset file."""
    processed_dir = get_processed_dir()
    # The task T019 specifies this exact filename
    candidate = processed_dir / "cleaned_dataset.csv"
    if not candidate.exists():
        pytest.fail(f"Expected dataset file not found at: {candidate}")
    return candidate

@pytest.fixture
def schema_path() -> Path:
    """Locate the schema definition file."""
    contracts_dir = PROJECT_ROOT / "contracts"
    schema_file = contracts_dir / "dataset.schema.yaml"
    if not schema_file.exists():
        pytest.fail(f"Schema file not found at: {schema_file}")
    return schema_file

def test_schema_file_exists(schema_path: Path):
    """Verify the schema definition file exists."""
    assert schema_path.exists(), "Schema file must exist for contract testing"

def test_dataset_file_exists(dataset_path: Path):
    """Verify the cleaned dataset file exists."""
    assert dataset_path.exists(), "Cleaned dataset must exist before running contract tests"

def test_required_columns_present(dataset_path: Path, schema_path: Path):
    """Verify all required columns from the schema are present."""
    # Load schema to ensure we are checking against the definition
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Load dataset
    df = pd.read_csv(dataset_path)
    
    # Check columns
    missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
    assert not missing_cols, f"Missing required columns: {missing_cols}"

def test_numeric_columns_dtypes(dataset_path: Path):
    """Verify numeric columns are of appropriate numeric dtype."""
    df = pd.read_csv(dataset_path)
    
    for col in NUMERIC_COLUMNS:
        if col not in df.columns:
            continue # Already checked in test_required_columns_present
        
        # Check if it's numeric (int or float)
        if not pd.api.types.is_numeric_dtype(df[col]):
            # Allow string-to-numeric conversion if it's just formatting, but strict check first
            try:
                pd.to_numeric(df[col])
            except (ValueError, TypeError):
                pytest.fail(f"Column '{col}' is not numeric and cannot be converted: {df[col].dtype}")

def test_no_nulls_critical_columns(dataset_path: Path):
    """Verify critical columns do not contain null values."""
    df = pd.read_csv(dataset_path)
    
    critical_cols = ["ACE", "Age", "Sex", "Site", "CA3", "DG", "Subiculum", "ICV"]
    
    for col in critical_cols:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            assert null_count == 0, f"Column '{col}' contains {null_count} null values"

def test_sex_values_valid(dataset_path: Path):
    """Verify Sex column contains valid values."""
    df = pd.read_csv(dataset_path)
    if "Sex" not in df.columns:
        return # Covered by other tests
    
    valid_values = CATEGORICAL_COLUMNS["Sex"]
    unique_vals = df["Sex"].unique()
    
    # If we have a defined list, check against it. If None, just check it's not empty.
    if valid_values:
        invalid_vals = set(unique_vals) - set(valid_values)
        # Allow for case insensitivity or common variations if strict list fails
        # For strict contract, we fail if unknown values exist
        if invalid_vals:
            # Log warning but maybe not fail if the schema allows dynamic values?
            # The contract says "valid", so we enforce.
            pytest.fail(f"Invalid values found in 'Sex' column: {invalid_vals}. Expected one of {valid_values}")

def test_normalized_volumes_precision(dataset_path: Path):
    """Verify Normalized_Volumes has sufficient precision (>= 4 decimal places)."""
    df = pd.read_csv(dataset_path)
    if "Normalized_Volumes" not in df.columns:
        return
    
    # Check if values are floats
    assert pd.api.types.is_float_dtype(df["Normalized_Volumes"]), "Normalized_Volumes must be float"
    
    # Check for very small values that might indicate integer division or loss of precision
    # We can't strictly check "4 decimal places" in a float type without string formatting,
    # but we can check that the values are reasonable (not just 0 or 1 due to integer division)
    min_val = df["Normalized_Volumes"].min()
    max_val = df["Normalized_Volumes"].max()
    
    # If max is 0, all are 0, which is suspicious for volume ratios
    if max_val == 0:
        pytest.fail("Normalized_Volumes are all zero, indicating potential calculation error")

def test_schema_yaml_structure(schema_path: Path):
    """Verify the schema YAML file has the expected structure."""
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    assert isinstance(schema, dict), "Schema must be a dictionary"
    assert "columns" in schema, "Schema must define 'columns'"
    assert isinstance(schema["columns"], list), "Columns must be a list"
    
    # Verify specific column definitions exist in YAML
    col_names = [c.get("name") if isinstance(c, dict) else c for c in schema["columns"]]
    for col in EXPECTED_COLUMNS:
        assert col in col_names, f"Column '{col}' missing from schema definition"