"""
Unit tests for cleaning strategies (T014, T015, T016, T019).
"""
"""Unit tests for core cleaning logic: outlier removal, imputation, and p-value shifts."""

import pytest
import pandas as pd
import numpy as np
from cleaning import apply_iqr_outlier_removal, apply_mean_imputation, apply_median_imputation

def test_apply_median_imputation_zero_missing():
    """Test that apply_median_imputation results in zero missing values in target columns."""
    data = {
        'A': [1.0, 2.0, 3.0, 4.0, 5.0],
        'B': [10.0, 20.0, np.nan, 40.0, 50.0],
        'C': ['x', 'y', 'z', 'w', 'v']
    }
    df = pd.DataFrame(data)
    
    result = apply_median_imputation(df, ['B'])
    
    assert result['B'].isna().sum() == 0, "Missing values should be imputed"
    assert result['B'].iloc[2] == 30.0, "Median of [10, 20, 40, 50] is 30.0"

def test_apply_median_imputation_variance_reduction_flag():
    """Test that a warning is logged if variance reduction >= 20%."""
    import logging
    import io
    
    # Setup logging capture
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.WARNING)
    logger = logging.getLogger('cleaning')
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    
    try:
        # Create data where imputation will significantly reduce variance
        # Original values: 1, 100, 1, 100, 1 (median=1, var is high)
        # With a missing value replaced by 1, variance drops
        data = {
            'A': [1.0, 100.0, 1.0, 100.0, np.nan]
        }
        df = pd.DataFrame(data)
        
        result = apply_median_imputation(df, ['A'])
        
        log_contents = log_stream.getvalue()
        # Check if warning about variance reduction was logged
        assert "Variance reduction >= 20%" in log_contents, "Should log warning for significant variance reduction"
    finally:
        logger.removeHandler(handler)

def test_apply_median_imputation_empty_columns():
    """Test behavior when no columns are specified."""
    df = pd.DataFrame({'A': [1, 2, 3]})
    result = apply_median_imputation(df, [])
    assert result.equals(df), "Should return original dataframe if no columns specified"

def test_apply_median_imputation_non_numeric():
    """Test imputation on non-numeric column (should handle gracefully or skip variance check)."""
    data = {
        'A': ['x', 'y', np.nan, 'z']
    }
    df = pd.DataFrame(data)
    result = apply_median_imputation(df, ['A'])
    
    # Median of strings might be undefined or behave differently depending on pandas version
    # But it should not crash and should fill the NaN
    assert result['A'].isna().sum() == 0, "Should attempt to impute even if non-numeric"