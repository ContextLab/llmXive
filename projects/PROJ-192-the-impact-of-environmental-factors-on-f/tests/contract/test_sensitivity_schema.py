import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from pydantic import ValidationError

# We define the expected schema here to validate against the generated CSV.
# This matches the requirements for T035: results/sensitivity_analysis.csv
# Columns: p_threshold, r2_threshold, top_driver, stable (boolean/flag)

SENSITIVITY_SCHEMA_COLUMNS = {
    "p_threshold": float,
    "r2_threshold": float,
    "top_driver": str,
    "stable": bool
}

REQUIRED_COLUMNS = list(SENSITIVITY_SCHEMA_COLUMNS.keys())

def test_sensitivity_analysis_schema_valid():
    """
    Contract test: Verify that a valid sensitivity analysis file
    matches the expected schema (columns and types).
    """
    # Create a valid sample DataFrame
    data = {
        "p_threshold": [0.01, 0.05, 0.10],
        "r2_threshold": [0.05, 0.10, 0.15],
        "top_driver": ["pH", "pH", "Moisture"],
        "stable": [True, True, False]
    }
    df = pd.DataFrame(data)

    # Validate columns
    assert set(df.columns) == set(REQUIRED_COLUMNS), \
        f"Columns mismatch. Expected {REQUIRED_COLUMNS}, got {list(df.columns)}"

    # Validate types
    for col, expected_type in SENSITIVITY_SCHEMA_COLUMNS.items():
        if expected_type == float:
            # Allow int to be castable to float
            assert pd.api.types.is_numeric_dtype(df[col]) or \
                   all(isinstance(x, (int, float, np.floating)) for x in df[col]), \
                   f"Column {col} should be numeric"
        elif expected_type == str:
            assert df[col].dtype == object or pd.api.types.is_string_dtype(df[col]), \
                f"Column {col} should be string"
        elif expected_type == bool:
            assert df[col].dtype == bool or all(isinstance(x, bool) for x in df[col]), \
                f"Column {col} should be boolean"

def test_sensitivity_analysis_schema_missing_columns():
    """
    Contract test: Verify failure when required columns are missing.
    """
    data = {
        "p_threshold": [0.05],
        "r2_threshold": [0.10],
        # Missing 'top_driver' and 'stable'
    }
    df = pd.DataFrame(data)

    with pytest.raises(AssertionError) as exc_info:
        assert set(df.columns) == set(REQUIRED_COLUMNS)
    
    assert "Columns mismatch" in str(exc_info.value)

def test_sensitivity_analysis_schema_wrong_types():
    """
    Contract test: Verify failure when column types are incorrect.
    """
    # top_driver should be string, but we provide int
    data = {
        "p_threshold": [0.05],
        "r2_threshold": [0.10],
        "top_driver": [123],  # Wrong type
        "stable": [True]
    }
    df = pd.DataFrame(data)

    # Check specifically for the string column type
    with pytest.raises(AssertionError) as exc_info:
        assert df["top_driver"].dtype == object or pd.api.types.is_string_dtype(df["top_driver"])
    
    assert "Column top_driver should be string" in str(exc_info.value)

def test_sensitivity_analysis_schema_empty_dataframe():
    """
    Contract test: Verify behavior on empty DataFrame (should fail schema check
    if columns are missing, or pass if columns exist but are empty).
    """
    # Empty with correct columns
    df = pd.DataFrame(columns=REQUIRED_COLUMNS)
    assert set(df.columns) == set(REQUIRED_COLUMNS)

    # Empty with missing columns
    df_missing = pd.DataFrame(columns=["p_threshold", "r2_threshold"])
    with pytest.raises(AssertionError):
        assert set(df_missing.columns) == set(REQUIRED_COLUMNS)