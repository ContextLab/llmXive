"""
Unit tests for preprocessing module.
"""

import pytest
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

from preprocessing import (
    apply_log_transformation,
    apply_zscore_normalization,
    apply_knn_imputation,
    ROOT_METRICS,
    NUTRIENT_COLUMNS
)

@pytest.fixture
def sample_root_data():
    """Sample DataFrame with root metrics."""
    return pd.DataFrame({
        'species': ['A', 'B', 'C', 'D'],
        'root_length': [10.0, 0.0, -5.0, 100.0],  # Includes zero and negative
        'branching_density': [5.0, 2.0, 0.0, 8.0],
        'surface_area': [20.0, 10.0, 5.0, 50.0],
        'phosphorus': [10.0, 20.0, 15.0, 30.0],
        'nitrogen': [5.0, 10.0, 8.0, 15.0],
        'potassium': [100.0, 200.0, 150.0, 300.0],
    })

@pytest.fixture
def sample_nutrient_data():
    """Sample DataFrame with nutrients only."""
    return pd.DataFrame({
        'species': ['A', 'B', 'C'],
        'phosphorus': [10.0, 20.0, 30.0],
        'nitrogen': [5.0, 10.0, 15.0],
        'potassium': [100.0, 200.0, 300.0],
    })

@pytest.fixture
def sample_missing_data():
    """Sample DataFrame with missing values."""
    return pd.DataFrame({
        'species': ['A', 'B', 'C', 'D'],
        'root_length': [10.0, np.nan, 20.0, 30.0],
        'branching_density': [5.0, 2.0, np.nan, 8.0],
        'phosphorus': [10.0, 20.0, np.nan, 30.0],
        'nitrogen': [np.nan, 10.0, 15.0, 20.0],
    })

def test_log_transformation_positive_values(sample_root_data):
    """Test log transformation on positive values."""
    result = apply_log_transformation(sample_root_data, ROOT_METRICS)
    
    # Check that transformed values are positive (log of positive number > 0 if num > 1)
    # Since we use log1p, log1p(x) > 0 for x > 0
    for col in ROOT_METRICS:
        assert (result[col] > 0).all(), f"Log transformed values in {col} should be positive"
        
def test_log_transformation_handles_zeros(sample_root_data):
    """Test that log transformation handles zeros correctly."""
    # Original data has 0.0 in root_length
    result = apply_log_transformation(sample_root_data, ROOT_METRICS)
    
    # log1p(0) = 0, but we add MIN_LOG_VALUE before log, so log1p(MIN_LOG_VALUE) > 0
    # The zero should have been adjusted
    assert result.loc[1, 'root_length'] > 0, "Zero value should have been adjusted for log transform"
    
def test_log_transformation_handles_negatives(sample_root_data):
    """Test that log transformation handles negative values correctly."""
    # Original data has -5.0 in root_length
    result = apply_log_transformation(sample_root_data, ROOT_METRICS)
    
    # Negative value should have been adjusted to MIN_LOG_VALUE
    assert result.loc[2, 'root_length'] > 0, "Negative value should have been adjusted for log transform"
    
def test_zscore_normalization(sample_nutrient_data):
    """Test z-score normalization."""
    result, scaler = apply_zscore_normalization(sample_nutrient_data, NUTRIENT_COLUMNS)
    
    assert scaler is not None, "Scaler should be returned"
    
    # Check that normalized values have mean ~0 and std ~1
    for col in NUTRIENT_COLUMNS:
        if col in result.columns:
            mean = result[col].mean()
            std = result[col].std()
            assert np.isclose(mean, 0, atol=1e-6), f"Mean of {col} should be ~0"
            assert np.isclose(std, 1, atol=1e-6), f"Std of {col} should be ~1"
            
def test_zscore_normalization_missing_columns(sample_nutrient_data):
    """Test z-score normalization with missing columns."""
    # Remove phosphorus column
    df = sample_nutrient_data.drop(columns=['phosphorus'])
    result, scaler = apply_zscore_normalization(df, NUTRIENT_COLUMNS)
    
    # Should still work with remaining columns
    assert 'nitrogen' in result.columns
    assert 'potassium' in result.columns
    assert 'phosphorus' not in result.columns
    
def test_knn_imputation(sample_missing_data):
    """Test KNN imputation."""
    result = apply_knn_imputation(sample_missing_data, k=3)
    
    # Check no missing values remain in numeric columns
    numeric_cols = result.select_dtypes(include=[np.number]).columns
    assert result[numeric_cols].isnull().sum().sum() == 0, "All missing values should be imputed"
    
    # Check that non-missing values are preserved
    assert result.loc[0, 'root_length'] == 10.0
    assert result.loc[2, 'root_length'] == 20.0
    
def test_knn_imputation_no_missing():
    """Test KNN imputation with no missing values."""
    df = pd.DataFrame({
        'species': ['A', 'B', 'C'],
        'root_length': [10.0, 20.0, 30.0],
        'nitrogen': [5.0, 10.0, 15.0],
    })
    
    result = apply_knn_imputation(df, k=3)
    
    # Should return unchanged data
    pd.testing.assert_frame_equal(result, df)
    
def test_knn_imputation_fallback():
    """Test KNN imputation fallback when KNN fails."""
    # Create a scenario where KNN might fail (e.g., all NaN in a column)
    df = pd.DataFrame({
        'species': ['A', 'B', 'C'],
        'root_length': [np.nan, np.nan, np.nan],  # All NaN
        'nitrogen': [5.0, 10.0, 15.0],
    })
    
    # This should not raise an error, but use fallback
    result = apply_knn_imputation(df, k=3)
    
    # Check no missing values remain
    assert result['root_length'].isnull().sum() == 0
    # Fallback should use mean
    assert result['root_length'].iloc[0] == 0.0  # mean of [nan, nan, nan] is nan, but fallback handles it
    
def test_log_transformation_missing_columns(sample_root_data):
    """Test log transformation with missing columns."""
    # Remove root_length column
    df = sample_root_data.drop(columns=['root_length'])
    result = apply_log_transformation(df, ROOT_METRICS)
    
    # Should handle missing columns gracefully
    assert 'branching_density' in result.columns
    assert 'surface_area' in result.columns
    # root_length should not be in result since it was dropped
    assert 'root_length' not in result.columns