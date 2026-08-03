import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import tempfile
import os

# Mock the config to use temp directory for testing
import sys
from unittest.mock import patch, MagicMock

# We need to test the logic without running the full pipeline
# So we will mock the data loading functions and test compute_regression_residuals directly

@pytest.fixture
def sample_agg_df():
    return pd.DataFrame({
        'dataset_id': [1, 2, 3, 4, 5],
        'model_name': ['LR', 'LR', 'LR', 'LR', 'LR'],
        'mean_accuracy': [0.8, 0.85, 0.75, 0.9, 0.82],
        'cv_accuracy': [0.05, 0.04, 0.06, 0.03, 0.045], # All positive
        'mean_f1': [0.79, 0.84, 0.74, 0.89, 0.81],
        'cv_f1': [0.05, 0.04, 0.06, 0.03, 0.045]
    })

@pytest.fixture
def sample_props_df():
    return pd.DataFrame({
        'dataset_id': [1, 2, 3, 4, 5],
        'n_samples': [1000, 2000, 3000, 4000, 5000],
        'n_features': [10, 15, 20, 25, 30]
    })

def test_compute_regression_residuals_positive_cv(sample_agg_df, sample_props_df):
    """Test that residuals are computed correctly for positive CV values."""
    # Import the function
    from code.analyser import compute_regression_residuals
    
    # Ensure we don't try to write to disk in this test
    # The function only returns a dataframe, so it's safe
    
    result = compute_regression_residuals(sample_agg_df, sample_props_df)
    
    assert not result.empty
    assert 'residual' in result.columns
    assert 'dataset_id' in result.columns
    assert 'model_name' in result.columns
    
    # Check that residuals are numeric
    assert pd.api.types.is_numeric_dtype(result['residual'])
    
    # Check that we have entries for all valid datasets
    # With 5 points and 3 parameters (intercept, slope1, slope2), we should have residuals
    assert len(result) == 5

def test_compute_regression_residuals_zero_cv(sample_agg_df, sample_props_df):
    """Test that rows with zero CV are excluded."""
    sample_agg_df.loc[0, 'cv_accuracy'] = 0.0
    
    from code.analyser import compute_regression_residuals
    
    result = compute_regression_residuals(sample_agg_df, sample_props_df)
    
    # Row 0 should be excluded because log(0) is undefined
    assert 0 not in result['dataset_id'].values
    assert len(result) == 4

def test_compute_regression_residuals_insufficient_points(sample_agg_df, sample_props_df):
    """Test behavior with insufficient data points for regression."""
    # Only 2 points
    small_agg = sample_agg_df.head(2)
    
    from code.analyser import compute_regression_residuals
    
    # Should return empty or log warning
    result = compute_regression_residuals(small_agg, sample_props_df.head(2))
    
    # With 2 points and 3 parameters, regression fails or is underdetermined
    # The function should handle this gracefully
    # Depending on implementation, it might return empty
    assert isinstance(result, pd.DataFrame)
    
def test_compute_regression_residuals_log_transformation(sample_agg_df, sample_props_df):
    """Verify that the residuals are based on log-log transformation."""
    from code.analyser import compute_regression_residuals
    import numpy as np
    
    result = compute_regression_residuals(sample_agg_df, sample_props_df)
    
    # Check that log columns exist
    assert 'log_cv' in result.columns
    assert 'log_n_samples' in result.columns
    assert 'log_n_features' in result.columns
    
    # Verify values are actually log transformed
    # Original cv_accuracy for first row is 0.05
    # log(0.05) should be in log_cv
    first_row = result[result['dataset_id'] == 1].iloc[0]
    expected_log_cv = np.log(0.05)
    assert np.isclose(first_row['log_cv'], expected_log_cv)