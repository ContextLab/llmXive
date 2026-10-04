"""
Contract test for T021: Bonferroni corrected correlations schema.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_path


@pytest.fixture
def corrected_correlations_path():
    return get_path("processed", "correlations_corrected.csv")


def test_bonferroni_schema_exists(corrected_correlations_path):
    """Verify the output file exists."""
    assert os.path.exists(corrected_correlations_path), \
        f"Output file {corrected_correlations_path} does not exist. T021 has not run."


def test_bonferroni_schema_columns(corrected_correlations_path):
    """Verify the output file has the required columns."""
    df = pd.read_csv(corrected_correlations_path)
    
    required_columns = [
        'band', 
        'r_value', 
        'p_value', 
        'n', 
        'p_value_adj', 
        'threshold', 
        'is_significant'
    ]
    
    missing = [c for c in required_columns if c not in df.columns]
    assert not missing, f"Missing required columns: {missing}"


def test_bonferroni_schema_types(corrected_correlations_path):
    """Verify data types are correct."""
    df = pd.read_csv(corrected_correlations_path)
    
    # Check numeric columns
    numeric_cols = ['r_value', 'p_value', 'n', 'p_value_adj', 'threshold']
    for col in numeric_cols:
        assert pd.api.types.is_numeric_dtype(df[col]), \
            f"Column {col} must be numeric"
    
    # Check boolean column
    assert df['is_significant'].dtype == bool, \
        "Column is_significant must be boolean"
    
    # Check string column
    assert df['band'].dtype == object or df['band'].dtype.name == 'string', \
        "Column band must be string-like"


def test_bonferroni_schema_values(corrected_correlations_path):
    """Verify logical constraints on values."""
    df = pd.read_csv(corrected_correlations_path)
    
    # P-values must be between 0 and 1
    assert (df['p_value'] >= 0).all() and (df['p_value'] <= 1).all(), \
        "Raw p-values must be between 0 and 1"
    
    # Adjusted p-values must be between 0 and 1
    assert (df['p_value_adj'] >= 0).all() and (df['p_value_adj'] <= 1).all(), \
        "Adjusted p-values must be between 0 and 1"
    
    # Threshold should be consistent (0.05 / 6)
    expected_threshold = 0.05 / 6
    assert abs(df['threshold'].iloc[0] - expected_threshold) < 1e-9, \
        f"Threshold should be {expected_threshold}"
    
    # is_significant should be True only if p_value_adj < 0.05
    # We check a few rows to ensure consistency
    significant_rows = df[df['is_significant'] == True]
    if not significant_rows.empty:
        assert (significant_rows['p_value_adj'] < 0.05).all(), \
            "Significant rows must have p_value_adj < 0.05"
    
    non_significant_rows = df[df['is_significant'] == False]
    if not non_significant_rows.empty:
        assert (non_significant_rows['p_value_adj'] >= 0.05).all(), \
            "Non-significant rows must have p_value_adj >= 0.05"


def test_bonferroni_schema_band_count(corrected_correlations_path):
    """Verify we have results for all 6 bands."""
    df = pd.read_csv(corrected_correlations_path)
    expected_bands = {'delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma'}
    actual_bands = set(df['band'].unique())
    
    assert expected_bands.issubset(actual_bands), \
        f"Missing bands: {expected_bands - actual_bands}. Expected 6 bands."