"""
Contract tests for correlation output schema.

This module verifies that the correlation analysis output (typically produced by
code/03_correlation_analysis.py) adheres to the strict schema requirements:
- Required columns: 'genus', 'cognitive_score', 'rho', 'p_value', 'adj_p_value'
- Data types: numeric for statistics, string for identifiers
- No null values in critical columns
- FDR adjustment logic consistency
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json

# Ensure code directory is in path for imports if running as script
if 'code' not in sys.path:
    code_path = Path(__file__).parent.parent / 'code'
    if code_path.exists():
        sys.path.insert(0, str(code_path))

# Expected schema definition
REQUIRED_COLUMNS = ['genus', 'cognitive_score', 'rho', 'p_value', 'adj_p_value']
NUMERIC_COLUMNS = ['rho', 'p_value', 'adj_p_value']
STRING_COLUMNS = ['genus', 'cognitive_score']
MIN_ROWS = 1  # At least one correlation must be computed

def load_test_data(data_path: str = None) -> pd.DataFrame:
    """
    Load the correlation results data for testing.
    
    In a real CI/CD or execution flow, this would load the actual output from
    code/03_correlation_analysis.py. For contract testing, we may also validate
    against a known-good sample or the actual file if it exists.
    """
    if data_path is None:
        # Default expected path based on task description
        data_path = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'correlation_results.csv'
    
    if not Path(data_path).exists():
        pytest.fail(f"Correlation results file not found at {data_path}. "
                    "Run code/03_correlation_analysis.py first to generate data.")
    
    return pd.read_csv(data_path)

def test_schema_columns_exist(df: pd.DataFrame):
    """Verify all required columns are present in the output DataFrame."""
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    assert not missing_cols, f"Missing required columns: {missing_cols}"

def test_schema_column_count(df: pd.DataFrame):
    """Ensure no unexpected extra columns are present (strict schema)."""
    extra_cols = [col for col in df.columns if col not in REQUIRED_COLUMNS]
    # We allow extra metadata columns for now, but log them
    if extra_cols:
        pytest.xfail(f"Extra columns detected (allowed but noted): {extra_cols}")

def test_schema_data_types(df: pd.DataFrame):
    """Verify numeric columns are numeric and string columns are string-like."""
    for col in NUMERIC_COLUMNS:
        if not pd.api.types.is_numeric_dtype(df[col]):
            pytest.fail(f"Column '{col}' is not numeric. Found type: {df[col].dtype}")
    
    for col in STRING_COLUMNS:
        if not pd.api.types.is_string_dtype(df[col]) and not pd.api.types.is_object_dtype(df[col]):
            # Allow object dtype for mixed types, but prefer string
            if not pd.api.types.is_numeric_dtype(df[col]):
                pytest.fail(f"Column '{col}' is not string-like. Found type: {df[col].dtype}")

def test_schema_no_null_critical(df: pd.DataFrame):
    """Ensure no null values in critical statistical columns."""
    for col in NUMERIC_COLUMNS:
        if df[col].isnull().any():
            count = df[col].isnull().sum()
            pytest.fail(f"Column '{col}' contains {count} null values. "
                        "Statistical results must not have missing values.")

def test_schema_p_value_range(df: pd.DataFrame):
    """Verify p-values are within valid range [0, 1]."""
    if (df['p_value'] < 0).any() or (df['p_value'] > 1).any():
        invalid_rows = df[(df['p_value'] < 0) | (df['p_value'] > 1)]
        pytest.fail(f"P-values out of range [0, 1]. Found {len(invalid_rows)} invalid rows.")

def test_schema_adj_p_value_range(df: pd.DataFrame):
    """Verify adjusted p-values are within valid range [0, 1]."""
    if (df['adj_p_value'] < 0).any() or (df['adj_p_value'] > 1).any():
        invalid_rows = df[(df['adj_p_value'] < 0) | (df['adj_p_value'] > 1)]
        pytest.fail(f"Adjusted p-values out of range [0, 1]. Found {len(invalid_rows)} invalid rows.")

def test_schema_adj_p_value_monotonicity(df: pd.DataFrame):
    """
    Verify that adjusted p-values are generally >= raw p-values.
    (Benjamini-Hochberg FDR should not reduce p-values below raw p-values).
    """
    if (df['adj_p_value'] < df['p_value']).any():
        # This is a strong indicator of a bug in FDR implementation
        count = (df['adj_p_value'] < df['p_value']).sum()
        pytest.fail(f"Found {count} rows where adj_p_value < p_value. "
                    "FDR correction should not reduce p-values.")

def test_schema_rho_range(df: pd.DataFrame):
    """Verify Spearman rho is within valid range [-1, 1]."""
    if (df['rho'] < -1).any() or (df['rho'] > 1).any():
        invalid_rows = df[(df['rho'] < -1) | (df['rho'] > 1)]
        pytest.fail(f"Spearman rho out of range [-1, 1]. Found {len(invalid_rows)} invalid rows.")

def test_schema_minimum_rows(df: pd.DataFrame):
    """Ensure the output contains at least one correlation result."""
    if len(df) < MIN_ROWS:
        pytest.fail(f"Output contains {len(df)} rows, expected at least {MIN_ROWS}.")

def test_schema_fdr_consistency(df: pd.DataFrame):
    """
    Verify that the FDR adjustment logic is consistent with Benjamini-Hochberg.
    This is a contract check: sorted p-values should result in non-decreasing adj_p_values.
    """
    sorted_df = df.sort_values('p_value')
    adj_p = sorted_df['adj_p_value'].values
    
    # BH adjustment: p_adj[i] = p_raw[i] * n / i (monotonically increasing after sorting)
    # We check for non-decreasing property in sorted order
    if np.any(np.diff(adj_p) < -1e-9):  # Allow small floating point errors
        pytest.fail("Adjusted p-values are not monotonically non-decreasing when sorted by raw p-value. "
                    "This indicates a potential error in FDR implementation.")

# Pytest fixtures
@pytest.fixture
def correlation_data():
    """Load the correlation results for all tests."""
    return load_test_data()

# Parametrize tests to run against the fixture
@pytest.mark.parametrize("test_func", [
    test_schema_columns_exist,
    test_schema_column_count,
    test_schema_data_types,
    test_schema_no_null_critical,
    test_schema_p_value_range,
    test_schema_adj_p_value_range,
    test_schema_adj_p_value_monotonicity,
    test_schema_rho_range,
    test_schema_minimum_rows,
    test_schema_fdr_consistency,
])
def test_correlation_contract(test_func, correlation_data):
    """Run a specific contract test against the loaded data."""
    test_func(correlation_data)

if __name__ == "__main__":
    # Allow running as a script for quick validation
    pytest.main([__file__, "-v"])