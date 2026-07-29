"""
Unit tests for cleaning strategies (T014, T015, T016, T019).
"""
"""Unit tests for core cleaning logic: outlier removal, imputation, and categorical recoding."""

import pytest
import pandas as pd
import numpy as np
from cleaning import (
    apply_iqr_outlier_removal,
    apply_mean_imputation,
    apply_median_imputation,
    apply_categorical_recoding
)

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

def test_apply_categorical_recoding_factor_encoding():
    """
    Verify apply_categorical_recoding produces factor-encoded columns.
    Validates against FR-002 (outlier removal context) and FR-003 (imputation context)
    by ensuring the function returns a tuple (df, metadata) as per the unified contract.
    """
    data = {
        'id': [1, 2, 3, 4, 5],
        'category': ['A', 'B', 'A', 'C', 'B'],
        'value': [10.0, 20.0, 30.0, 40.0, 50.0]
    }
    df = pd.DataFrame(data)
    
    # Apply recoding
    result = apply_categorical_recoding(df)
    
    # Check return type is tuple (df, metadata)
    assert isinstance(result, tuple), "Function must return (cleaned_df, metadata)"
    assert len(result) == 2, "Tuple must contain dataframe and metadata dict"
    
    cleaned_df, metadata = result
    
    # Verify metadata exists and has expected keys
    assert isinstance(metadata, dict), "Metadata must be a dictionary"
    assert 'recoded_columns' in metadata, "Metadata must list recoded columns"
    assert 'rows_processed' in metadata, "Metadata must include rows processed"
    
    # Verify rows processed count
    assert metadata['rows_processed'] == 5, "Should process all 5 rows"
    
    # Verify the 'category' column was recoded (should be numeric now)
    assert 'category' in metadata['recoded_columns'], "Category column should be in recoded list"
    assert cleaned_df['category'].dtype in [np.int64, np.int32, 'int64', 'int32'], \
        f"Recoded column should be numeric, got {cleaned_df['category'].dtype}"
    
    # Verify values are valid integers (0-based or 1-based encoding)
    unique_vals = cleaned_df['category'].unique()
    assert all(isinstance(v, (int, np.integer)) for v in unique_vals), \
        "All recoded values must be integers"
    
    # Verify no NaN in recoded column
    assert cleaned_df['category'].isna().sum() == 0, "Recoded column should have no missing values"

def test_apply_categorical_recoding_empty_dataframe():
    """Test recoding on an empty dataframe."""
    df = pd.DataFrame({'A': [], 'B': []})
    result = apply_categorical_recoding(df)
    
    cleaned_df, metadata = result
    assert len(cleaned_df) == 0, "Empty dataframe should remain empty"
    assert metadata['rows_processed'] == 0, "Metadata should reflect 0 rows"

def test_apply_categorical_recoding_no_categorical_cols():
    """Test recoding when no categorical columns exist."""
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [4.0, 5.0, 6.0]})
    result = apply_categorical_recoding(df)
    
    cleaned_df, metadata = result
    assert len(metadata['recoded_columns']) == 0, "No columns should be recoded"
    assert metadata['rows_processed'] == 3, "Rows should still be processed"