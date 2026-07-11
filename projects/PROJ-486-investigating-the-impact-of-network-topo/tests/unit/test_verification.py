"""
Test suite for T021a: Verification of correlation_results.csv schema.
Ensures the output file contains the required columns for collinearity analysis.
"""
import os
import pandas as pd
import pytest

# Path to the expected output file
OUTPUT_PATH = "data/processed/correlation_results.csv"

def test_correlation_results_schema():
    """
    Verify that data/processed/correlation_results.csv contains:
    - 'collinearity_warning' (boolean)
    - 'vif_value' (numeric)
    
    This validates the implementation of T015b and T020.
    """
    assert os.path.exists(OUTPUT_PATH), f"Output file not found: {OUTPUT_PATH}"
    
    df = pd.read_csv(OUTPUT_PATH)
    
    # Check for required columns
    required_columns = ['collinearity_warning', 'vif_value']
    
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Verify data types
    assert df['collinearity_warning'].dtype == bool, \
        f"Column 'collinearity_warning' must be boolean, got {df['collinearity_warning'].dtype}"
    
    assert pd.api.types.is_numeric_dtype(df['vif_value']), \
        f"Column 'vif_value' must be numeric, got {df['vif_value'].dtype}"
    
    # Verify logical consistency: if vif_value > 5, warning must be True
    # (This validates the logic implemented in T015b/T020)
    high_vif_mask = df['vif_value'] > 5
    if high_vif_mask.any():
        assert (df.loc[high_vif_mask, 'collinearity_warning'] == True).all(), \
            "All rows with VIF > 5 must have collinearity_warning = True"
    
    # If no high VIF exists, ensure warnings are False where VIF <= 5
    low_vif_mask = df['vif_value'] <= 5
    if low_vif_mask.any():
        assert (df.loc[low_vif_mask, 'collinearity_warning'] == False).all(), \
            "All rows with VIF <= 5 must have collinearity_warning = False"