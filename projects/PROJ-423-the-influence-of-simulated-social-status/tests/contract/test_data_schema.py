"""
Contract test: Validate output CSV columns and data types against data-model.md.

This test ensures that the data generation and preprocessing pipeline produces
files that strictly adhere to the defined schema.
"""
import os
import pytest
import pandas as pd
from pathlib import Path

# Expected columns based on data-model.md and task descriptions
REQUIRED_COLUMNS = [
    "participant_id",
    "status_level",
    "observed_behavior",
    "risk_taking_score"
]

@pytest.fixture
def processed_data_path():
    """Locate the processed data file."""
    # Check standard output location first
    path = Path("data/processed/cleaned_data.csv")
    if path.exists():
        return path
    
    # Fallback to raw if processed doesn't exist yet (for early pipeline tests)
    path = Path("data/raw/synthetic_data.csv")
    if path.exists():
        return path
    
    # Return the processed path regardless, pytest will handle the missing file
    return Path("data/processed/cleaned_data.csv")

def test_csv_columns_exist(processed_data_path):
    """Verify that all required columns are present in the CSV."""
    if not processed_data_path.exists():
        pytest.skip("Data file not found. Run generation pipeline first.")
    
    df = pd.read_csv(processed_data_path)
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    assert not missing_cols, f"Missing required columns: {missing_cols}"

def test_data_types(processed_data_path):
    """Verify data types match expectations (string categories, numeric scores)."""
    if not processed_data_path.exists():
        pytest.skip("Data file not found. Run generation pipeline first.")
    
    df = pd.read_csv(processed_data_path)
    
    # participant_id should be string or int (object or int64)
    assert df["participant_id"].dtype in ["object", "int64", "int32"], \
        f"participant_id has unexpected type: {df['participant_id'].dtype}"
    
    # status_level and observed_behavior should be categorical or string
    assert df["status_level"].dtype in ["object", "category"], \
        f"status_level has unexpected type: {df['status_level'].dtype}"
    
    assert df["observed_behavior"].dtype in ["object", "category"], \
        f"observed_behavior has unexpected type: {df['observed_behavior'].dtype}"
    
    # risk_taking_score should be numeric
    assert pd.api.types.is_numeric_dtype(df["risk_taking_score"]), \
        f"risk_taking_score is not numeric: {df['risk_taking_score'].dtype}"

def test_no_null_values_in_required_columns(processed_data_path):
    """Verify that required columns do not contain null values."""
    if not processed_data_path.exists():
        pytest.skip("Data file not found. Run generation pipeline first.")
    
    df = pd.read_csv(processed_data_path)
    
    for col in REQUIRED_COLUMNS:
        null_count = df[col].isnull().sum()
        assert null_count == 0, f"Column '{col}' contains {null_count} null values"

def test_status_level_values(processed_data_path):
    """Verify status_level contains only valid categorical values."""
    if not processed_data_path.exists():
        pytest.skip("Data file not found. Run generation pipeline first.")
    
    df = pd.read_csv(processed_data_path)
    valid_status_values = {"High", "Low", "Medium"}
    
    # Check if the column is categorical and get categories, or just unique values
    if hasattr(df["status_level"], 'cat'):
        actual_values = set(df["status_level"].cat.categories)
    else:
        actual_values = set(df["status_level"].unique())
    
    invalid_values = actual_values - valid_status_values
    assert not invalid_values, f"Invalid status_level values found: {invalid_values}"

def test_observed_behavior_values(processed_data_path):
    """Verify observed_behavior contains only valid categorical values."""
    if not processed_data_path.exists():
        pytest.skip("Data file not found. Run generation pipeline first.")
    
    df = pd.read_csv(processed_data_path)
    valid_behavior_values = {"Risky", "Conservative"}
    
    # Check if the column is categorical and get categories, or just unique values
    if hasattr(df["observed_behavior"], 'cat'):
        actual_values = set(df["observed_behavior"].cat.categories)
    else:
        actual_values = set(df["observed_behavior"].unique())
    
    invalid_values = actual_values - valid_behavior_values
    assert not invalid_values, f"Invalid observed_behavior values found: {invalid_values}"