import pytest
import pandas as pd
import jsonschema
import yaml
from pathlib import Path
import os


@pytest.fixture
def schema():
    """Load the dataset schema from the contracts directory."""
    schema_path = Path("contracts/dataset.schema.yaml")
    if not schema_path.exists():
        pytest.fail(f"Schema file not found at {schema_path}. Ensure T004 and T018 have completed successfully.")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


@pytest.fixture
def cleaned_data():
    """Load the actual processed dataset from disk."""
    data_path = Path("data/processed/cleaned_316L.csv")
    if not data_path.exists():
        pytest.fail(f"Processed dataset not found at {data_path}. Run T012 (download) and T018 (preprocess/save) first.")
    
    df = pd.read_csv(data_path)
    
    # Verify no NaN values exist (as per US1 requirements)
    if df.isnull().any().any():
        pytest.fail("Dataset contains null values, which violates US1 requirements (median imputation should have resolved this).")
        
    return df


def test_required_columns_exist(schema, cleaned_data):
    """Validate that all required columns defined in the schema exist in the dataset."""
    required_cols = schema.get("required_columns", [])
    missing_cols = []
    
    for col in required_cols:
        if col not in cleaned_data.columns:
            missing_cols.append(col)
    
    if missing_cols:
        pytest.fail(f"Missing required columns: {missing_cols}. Expected: {required_cols}, Found: {list(cleaned_data.columns)}")


def test_column_types_numeric(schema, cleaned_data):
    """Validate that defined columns are numeric."""
    column_defs = schema.get("column_definitions", {})
    numeric_cols = [
        col for col, props in column_defs.items() 
        if props.get("type") == "numeric"
    ]
    
    for col in numeric_cols:
        if col in cleaned_data.columns:
            if not pd.api.types.is_numeric_dtype(cleaned_data[col]):
                pytest.fail(f"Column '{col}' is not numeric. Found dtype: {cleaned_data[col].dtype}")


def test_value_ranges(schema, cleaned_data):
    """Validate that values fall within defined constraints."""
    constraints = schema.get("constraints", {}).get("value_ranges", {})
    
    for col, (min_val, max_val) in constraints.items():
        if col in cleaned_data.columns:
            col_data = cleaned_data[col]
            
            if min_val is not None and (col_data < min_val).any():
                pytest.fail(f"Column '{col}' has values below minimum {min_val}. Min found: {col_data.min()}")
            
            if max_val is not None and (col_data > max_val).any():
                pytest.fail(f"Column '{col}' has values above maximum {max_val}. Max found: {col_data.max()}")


def test_no_null_values(cleaned_data):
    """Ensure the dataset contains no null values."""
    null_counts = cleaned_data.isnull().sum()
    if null_counts.any():
        pytest.fail(f"Dataset contains null values in columns: {null_counts[null_counts > 0].to_dict()}")


def test_degenerate_dataset_check(schema, cleaned_data):
    """Validate that porosity has non-zero variance (not degenerate)."""
    if "porosity" not in cleaned_data.columns:
        pytest.fail("Porosity column missing, cannot check variance.")
    
    variance = cleaned_data["porosity"].var()
    # Use a small epsilon for float comparison if min_variance is 0
    min_variance = schema.get("constraints", {}).get("porosity_variance", {}).get("min_variance", 0.0)
    
    if variance <= min_variance:
        pytest.fail(f"Dataset is degenerate: porosity variance ({variance}) is zero or near-zero (min allowed: {min_variance}).")