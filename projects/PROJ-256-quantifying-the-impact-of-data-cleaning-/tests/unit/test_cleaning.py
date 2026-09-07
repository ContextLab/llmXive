"""
Unit tests for cleaning module.
"""
import pytest
import pandas as pd
import numpy as np
from code.cleaning import (
    apply_iqr_outlier_removal,
    apply_mean_imputation,
    apply_median_imputation,
    apply_knn_imputation,
    apply_categorical_recoding
)

def test_iqr_outlier_removal():
    """Test IQR outlier removal."""
    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5, 100],
        'y': [1, 2, 3, 4, 5, 6]
    })
    cleaned_df, metadata = apply_iqr_outlier_removal(df)
    assert 'rows_removed' in metadata
    assert 'missing_values_remaining' in metadata
    assert metadata['rows_removed'] > 0
    assert len(cleaned_df) < len(df)

def test_mean_imputation():
    """Test mean imputation."""
    df = pd.DataFrame({
        'x': [1, 2, np.nan, 4, 5],
        'y': [1, 2, 3, 4, 5]
    })
    cleaned_df, metadata = apply_mean_imputation(df)
    assert metadata['missing_values_remaining'] == 0
    assert not cleaned_df['x'].isna().any()

def test_categorical_recoding():
    """Test categorical recoding."""
    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'cat': ['A', 'B', 'A', 'B', 'C']
    })
    cleaned_df, metadata = apply_categorical_recoding(df)
    assert 'encoded_columns' in metadata
    assert 'cat' not in cleaned_df.columns or 'cat_A' in cleaned_df.columns
