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

def test_apply_iqr_outlier_removal():
    """Test IQR outlier removal."""
    data = {
        'A': [1, 2, 3, 4, 5, 100],  # 100 is an outlier
        'B': [10, 20, 30, 40, 50, 60]
    }
    df = pd.DataFrame(data)
    
    cleaned_df, metadata = apply_iqr_outlier_removal(df, k=1.5)
    
    assert 'rows_removed' in metadata
    assert 'missing_values_remaining' in metadata
    assert metadata['rows_removed'] >= 1  # At least the outlier should be removed
    assert len(cleaned_df) < len(df)

def test_apply_mean_imputation():
    """Test mean imputation."""
    data = {
        'A': [1, 2, np.nan, 4, 5],
        'B': [10, 20, 30, 40, 50]
    }
    df = pd.DataFrame(data)
    
    cleaned_df, metadata = apply_mean_imputation(df, columns=['A'])
    
    assert metadata['rows_removed'] == 0
    assert metadata['missing_values_remaining'] == 0
    assert not cleaned_df['A'].isnull().any()

def test_apply_median_imputation():
    """Test median imputation."""
    data = {
        'A': [1, 2, np.nan, 4, 5],
        'B': [10, 20, 30, 40, 50]
    }
    df = pd.DataFrame(data)
    
    cleaned_df, metadata = apply_median_imputation(df, columns=['A'])
    
    assert metadata['rows_removed'] == 0
    assert metadata['missing_values_remaining'] == 0
    assert not cleaned_df['A'].isnull().any()

def test_apply_knn_imputation():
    """Test KNN imputation."""
    data = {
        'A': [1, 2, np.nan, 4, 5],
        'B': [10, 20, 30, 40, 50]
    }
    df = pd.DataFrame(data)
    
    cleaned_df, metadata = apply_knn_imputation(df, columns=['A'], k=2)
    
    assert metadata['rows_removed'] == 0
    assert not cleaned_df['A'].isnull().any()

def test_apply_categorical_recoding():
    """Test categorical recoding."""
    data = {
        'A': ['x', 'y', 'x', 'z', 'y'],
        'B': [1, 2, 3, 4, 5]
    }
    df = pd.DataFrame(data)
    
    cleaned_df, metadata = apply_categorical_recoding(df)
    
    assert 'encoded_columns' in metadata
    assert 'A' in metadata['encoded_columns']
    assert cleaned_df['A'].dtype in [int, np.int64, np.int32]
