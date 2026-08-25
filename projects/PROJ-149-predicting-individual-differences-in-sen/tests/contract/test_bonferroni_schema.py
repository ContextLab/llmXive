"""
Contract test for T021 Bonferroni corrected correlations output.
Validates schema of data/processed/correlations_corrected.csv
"""
import os
import pytest
import pandas as pd
from pathlib import Path

# Import project config to get paths
try:
    from config import get_path
except ImportError:
    # Fallback for running tests from different directory
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))
    from config import get_path


CORRECTED_PATH = get_path("processed", "correlations_corrected.csv")


def test_bonferroni_output_exists():
    """Verify the corrected correlations file exists."""
    assert os.path.exists(CORRECTED_PATH), f"Output file not found: {CORRECTED_PATH}"


def test_bonferroni_schema_columns():
    """Verify all required columns are present."""
    df = pd.read_csv(CORRECTED_PATH)
    
    required_cols = {
        'band',           # Original band name
        'r_value',        # Original correlation coefficient
        'p_value',        # Original p-value
        'n',              # Sample size
        'bonferroni_p',   # Corrected p-value
        'significant'     # Boolean flag
    }
    
    missing = required_cols - set(df.columns)
    assert not missing, f"Missing required columns: {missing}"


def test_bonferroni_p_value_range():
    """Verify corrected p-values are in valid range [0, 1]."""
    df = pd.read_csv(CORRECTED_PATH)
    
    assert (df['bonferroni_p'] >= 0).all(), "Corrected p-values must be >= 0"
    assert (df['bonferroni_p'] <= 1).all(), "Corrected p-values must be <= 1"


def test_bonferroni_significant_flag_type():
    """Verify significant column contains boolean values."""
    df = pd.read_csv(CORRECTED_PATH)
    
    # Check that significant column is boolean or can be treated as such
    assert df['significant'].dtype == bool, "significant column must be boolean"


def test_bonferroni_significant_logic():
    """Verify significant flag matches bonferroni_p < 0.05 logic."""
    df = pd.read_csv(CORRECTED_PATH)
    
    expected_significant = df['bonferroni_p'] < 0.05
    pd.testing.assert_series_equal(
        df['significant'], 
        expected_significant, 
        check_names=False
    )


def test_bonferroni_no_nulls():
    """Verify no null values in critical columns."""
    df = pd.read_csv(CORRECTED_PATH)
    
    critical_cols = ['band', 'r_value', 'p_value', 'bonferroni_p', 'significant']
    for col in critical_cols:
        assert not df[col].isnull().any(), f"Null values found in column: {col}"


def test_bonferroni_band_count():
    """Verify we have exactly 6 bands (one per EEG band)."""
    df = pd.read_csv(CORRECTED_PATH)
    
    expected_bands = {'delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma'}
    actual_bands = set(df['band'].unique())
    
    assert actual_bands == expected_bands, f"Expected bands {expected_bands}, got {actual_bands}"
    assert len(df) == 6, f"Expected 6 rows (one per band), got {len(df)}"