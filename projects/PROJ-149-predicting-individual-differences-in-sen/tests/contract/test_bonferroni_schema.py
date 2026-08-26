"""
Contract test for T021: Bonferroni corrected correlations schema.
Validates data/processed/correlations_corrected.csv.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from config import get_path

REQUIRED_COLUMNS = {
    'band', 'r_value', 'p_value', 'n', 
    'bonferroni_p_value', 'is_significant'
}

BONFERRONI_ALPHA = 0.05 / 6  # ~0.00833


def test_corrections_file_exists():
    """Ensure the output file is created."""
    path = get_path("processed", "correlations_corrected.csv")
    assert os.path.exists(path), f"Output file missing: {path}"


def test_schema_columns():
    """Ensure all required columns are present."""
    path = get_path("processed", "correlations_corrected.csv")
    df = pd.read_csv(path)
    
    assert set(df.columns).issuperset(REQUIRED_COLUMNS), (
        f"Missing columns. Expected {REQUIRED_COLUMNS}, got {set(df.columns)}"
    )


def test_bonferroni_calculation():
    """Verify the Bonferroni calculation is correct."""
    path = get_path("processed", "correlations_corrected.csv")
    df = pd.read_csv(path)
    
    # Check that bonferroni_p_value is p_value * 6 (capped at 1.0)
    expected_p = (df['p_value'] * 6).clip(upper=1.0)
    assert all(df['bonferroni_p_value'].round(5) == expected_p.round(5)), (
        "Bonferroni p-value calculation incorrect."
    )


def test_significance_flag():
    """Verify the significance flag logic."""
    path = get_path("processed", "correlations_corrected.csv")
    df = pd.read_csv(path)
    
    # Check that is_significant matches bonferroni_p_value < alpha
    expected_sig = df['bonferroni_p_value'] < BONFERRONI_ALPHA
    assert all(df['is_significant'] == expected_sig), (
        "Significance flag logic incorrect."
    )


def test_no_nulls():
    """Ensure no null values in critical columns."""
    path = get_path("processed", "correlations_corrected.csv")
    df = pd.read_csv(path)
    
    critical_cols = ['p_value', 'bonferroni_p_value', 'is_significant', 'r_value']
    for col in critical_cols:
        assert not df[col].isnull().any(), f"Null values found in column: {col}"
