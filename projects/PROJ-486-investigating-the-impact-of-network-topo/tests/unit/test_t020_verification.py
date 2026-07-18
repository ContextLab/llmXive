"""
Test for T020: Verify output CSV matches acceptance scenario.

Checks that data/processed/correlation_results.csv contains:
- raw_p, adjusted_p_value, is_significant, vif_value, collinearity_warning columns
- collinearity_warning is True (boolean) if vif_value > 5
"""
import os
import pandas as pd
import pytest

RESULTS_PATH = "data/processed/correlation_results.csv"

REQUIRED_COLUMNS = [
    "raw_p",
    "adjusted_p_value",
    "is_significant",
    "vif_value",
    "collinearity_warning"
]

def test_output_csv_columns_exist():
    """Verify all required columns are present in the output CSV."""
    assert os.path.exists(RESULTS_PATH), f"Output file {RESULTS_PATH} does not exist."
    
    df = pd.read_csv(RESULTS_PATH)
    
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    assert not missing_cols, f"Missing required columns: {missing_cols}"

def test_collinearity_warning_logic():
    """
    Verify that collinearity_warning is True (boolean) if vif_value > 5.
    Also ensures it is False otherwise.
    """
    assert os.path.exists(RESULTS_PATH), f"Output file {RESULTS_PATH} does not exist."
    
    df = pd.read_csv(RESULTS_PATH)
    
    # Check column types
    assert df["collinearity_warning"].dtype == bool, \
        "collinearity_warning must be a boolean column."
    
    # Verify logic: if vif_value > 5, then collinearity_warning must be True
    high_vif_mask = df["vif_value"] > 5
    if high_vif_mask.any():
        high_vif_warnings = df.loc[high_vif_mask, "collinearity_warning"]
        assert all(high_vif_warnings), \
            "collinearity_warning must be True for all rows where vif_value > 5."
    
    # Verify logic: if vif_value <= 5, then collinearity_warning must be False
    low_vif_mask = df["vif_value"] <= 5
    if low_vif_mask.any():
        low_vif_warnings = df.loc[low_vif_mask, "collinearity_warning"]
        assert not any(low_vif_warnings), \
            "collinearity_warning must be False for all rows where vif_value <= 5."

def test_is_significant_logic():
    """
    Verify that is_significant is derived correctly from adjusted_p_value.
    Standard threshold is 0.05.
    """
    assert os.path.exists(RESULTS_PATH), f"Output file {RESULTS_PATH} does not exist."
    
    df = pd.read_csv(RESULTS_PATH)
    
    # Check column types
    assert df["is_significant"].dtype == bool, \
        "is_significant must be a boolean column."
    
    # Verify logic: is_significant should be True if adjusted_p_value < 0.05
    expected_significant = df["adjusted_p_value"] < 0.05
    assert all(df["is_significant"] == expected_significant), \
        "is_significant must match (adjusted_p_value < 0.05)."
