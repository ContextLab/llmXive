"""
Contract test for the MgB2 dataset schema.
Verifies that the processed dataset contains the required columns
and that the data types conform to expectations.
"""

import pytest
import pandas as pd
from pathlib import Path

# Expected columns as per task specification
REQUIRED_COLUMNS = {
    "Tc",
    "impurities_atomic_pct",
    "temp_K",
    "pressure_GPa"
}

# Expected data types for numeric columns
EXPECTED_NUMERIC_COLUMNS = {
    "Tc",
    "impurities_atomic_pct",
    "temp_K",
    "pressure_GPa"
}

def get_processed_data_path():
    """
    Returns the path to the processed dataset.
    The path is relative to the project root.
    """
    return Path("data/processed/mgb2_clean.csv")

def test_dataset_schema_exists():
    """Test that the processed dataset file exists."""
    data_path = get_processed_data_path()
    assert data_path.exists(), f"Dataset file not found at {data_path}"

def test_dataset_schema_has_required_columns():
    """
    Contract test: Verify the dataset contains the required columns.
    Columns: Tc, impurities_atomic_pct, temp_K, pressure_GPa
    """
    data_path = get_processed_data_path()
    
    # Load the dataset
    df = pd.read_csv(data_path)
    
    # Check that all required columns are present
    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    assert not missing_columns, (
        f"Dataset is missing required columns: {missing_columns}. "
        f"Found columns: {list(df.columns)}"
    )

def test_dataset_schema_numeric_columns_are_numeric():
    """
    Contract test: Verify that expected numeric columns contain numeric data.
    """
    data_path = get_processed_data_path()
    df = pd.read_csv(data_path)
    
    for col in EXPECTED_NUMERIC_COLUMNS:
        if col in df.columns:
            # Check if the column is numeric (int or float)
            if not pd.api.types.is_numeric_dtype(df[col]):
                # Try to see if it can be converted
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pytest.fail(
                        f"Column '{col}' is not numeric and cannot be converted. "
                        f"Current dtype: {df[col].dtype}"
                    )

def test_dataset_schema_no_nulls_in_target_columns():
    """
    Contract test: Verify that critical target columns do not contain null values.
    Specifically Tc and impurities_atomic_pct as per US1 requirements.
    """
    data_path = get_processed_data_path()
    df = pd.read_csv(data_path)
    
    critical_columns = ["Tc", "impurities_atomic_pct"]
    
    for col in critical_columns:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            assert null_count == 0, (
                f"Column '{col}' contains {null_count} null values. "
                "Critical columns must not have nulls."
            )

def test_dataset_schema_row_count():
    """
    Contract test: Verify the dataset has a non-zero number of rows.
    """
    data_path = get_processed_data_path()
    df = pd.read_csv(data_path)
    
    assert len(df) > 0, "Dataset must contain at least one row."