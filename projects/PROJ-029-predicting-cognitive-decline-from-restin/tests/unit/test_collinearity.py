"""
Unit tests for collinearity filtering logic.

This test file implements T041: A unit test verifying that the collinearity 
filter correctly drops one of a pair of features with Pearson correlation > 0.95.

TDD Rule: This test is designed to FAIL before the implementation in 
code/04_train_model.py (specifically the CollinearityTransformer) is correct.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add the code directory to the path so we can import the transformer
# This is necessary because the test runner might not have the code/ directory in sys.path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.stats import check_collinearity, calculate_pearson_correlation
from sklearn.feature_selection import VarianceThreshold


def test_collinearity_filter_with_identical_columns():
    """
    Test that the collinearity filter correctly drops one of a pair of 
    features with Pearson correlation > 0.95.
    
    Implementation: Create a feature matrix with two identical columns.
    Assert that the filter removes one and keeps the other.
    """
    # Create a feature matrix with two identical columns
    # and some other random columns
    np.random.seed(42)
    n_samples = 100
    n_features = 5
    
    # Create base random data
    base_data = np.random.rand(n_samples, n_features)
    
    # Make column 0 and column 1 identical
    base_data[:, 1] = base_data[:, 0].copy()
    
    X = pd.DataFrame(base_data, columns=[f'feature_{i}' for i in range(n_features)])
    
    # Calculate correlation between the identical columns
    corr_val = calculate_pearson_correlation(X['feature_0'], X['feature_1'])
    assert abs(corr_val) > 0.95, "Test setup failed: correlation should be > 0.95"
    
    # Apply collinearity filter
    # The check_collinearity function should return a mask of features to keep
    keep_mask = check_collinearity(X, threshold=0.95)
    
    # Assert that one of the identical features is removed
    # The mask should have length equal to the number of features
    # and should be False for at least one of the identical columns
    assert len(keep_mask) == n_features, "Keep mask length should match number of features"
    
    # Check that not both identical features are kept
    # Since they are identical, one should be dropped
    identical_features_kept = keep_mask[0] and keep_mask[1]
    assert not identical_features_kept, "Collinearity filter failed: both identical features were kept"
    
    # Check that at least one feature is kept
    assert any(keep_mask), "Collinearity filter failed: all features were dropped"
    
    # Verify the logic: if correlation > threshold, drop the second one (or the one with lower variance)
    # In this case, since they are identical, variance is the same, so it should drop one consistently
    features_kept = X.columns[keep_mask]
    assert len(features_kept) < n_features, "Collinearity filter did not remove any features"
    
    # Specifically, one of feature_0 or feature_1 should be missing from the kept features
    assert ('feature_0' not in features_kept) or ('feature_1' not in features_kept), \
        "Collinearity filter failed: both identical features (feature_0 and feature_1) were kept"


def test_collinearity_filter_preserves_uncorrelated_features():
    """
    Test that the collinearity filter preserves features that are not highly correlated.
    """
    np.random.seed(42)
    n_samples = 100
    n_features = 3
    
    # Create uncorrelated random data
    X = pd.DataFrame(np.random.rand(n_samples, n_features), 
                    columns=[f'feature_{i}' for i in range(n_features)])
    
    # Apply collinearity filter
    keep_mask = check_collinearity(X, threshold=0.95)
    
    # All features should be kept since they are uncorrelated
    assert all(keep_mask), "Collinearity filter incorrectly dropped uncorrelated features"
    assert len(X.columns[keep_mask]) == n_features, "Not all uncorrelated features were preserved"


def test_collinearity_threshold_behavior():
    """
    Test that the filter behaves correctly with different thresholds.
    """
    np.random.seed(42)
    n_samples = 100
    
    # Create two columns with correlation ~0.9
    X = pd.DataFrame({
        'feature_0': np.random.rand(n_samples),
        'feature_1': np.random.rand(n_samples)
    })
    
    # Make them highly correlated but not identical
    X['feature_1'] = X['feature_0'] * 0.9 + np.random.rand(n_samples) * 0.1
    
    corr_val = calculate_pearson_correlation(X['feature_0'], X['feature_1'])
    
    # With threshold 0.95, both should be kept (correlation < 0.95)
    keep_mask_high = check_collinearity(X, threshold=0.95)
    assert all(keep_mask_high), "Features with correlation < 0.95 should be kept with threshold 0.95"
    
    # With threshold 0.8, one should be dropped (correlation > 0.8)
    keep_mask_low = check_collinearity(X, threshold=0.8)
    assert not all(keep_mask_low), "One feature should be dropped with threshold 0.8"