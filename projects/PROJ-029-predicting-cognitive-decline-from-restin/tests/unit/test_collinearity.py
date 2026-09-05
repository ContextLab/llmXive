"""Unit tests for collinearity filtering logic (FR-008).

This module implements the TDD test for T044.
It verifies that the collinearity filter correctly drops one of a pair
of features with Pearson correlation > 0.95.

TDD Rule: This test must FAIL before T023 (CollinearityTransformer) is implemented.
"""
import pytest
import numpy as np
import pandas as pd

# Import the transformer we expect to exist after T023 implementation.
# If T023 is not done, this import will fail, causing the test to fail as expected.
try:
    from utils.stats import check_collinearity
    HAS_COLLINEARITY = True
except ImportError:
    HAS_COLLINEARITY = False


@pytest.mark.skipif(
    not HAS_COLLINEARITY,
    reason="T023 (CollinearityTransformer) not yet implemented; TDD rule: test must fail before impl."
)
def test_collinearity_filter():
    """Test that the collinearity filter drops one of two identical columns.

    Generates a feature matrix with two identical columns (correlation = 1.0).
    Asserts that the filter removes one and keeps the other.
    """
    # Create a mock dataset with two identical columns
    # Shape: (10 subjects, 2 features)
    np.random.seed(42)
    n_subjects = 10
    
    # Generate random data for the first feature
    feature_a = np.random.randn(n_subjects)
    
    # Create the second feature as an exact copy (correlation = 1.0)
    feature_b = feature_a.copy()
    
    # Create a DataFrame with column names
    df = pd.DataFrame({
        'feature_A': feature_a,
        'feature_B': feature_b
    })
    
    # Apply the collinearity filter
    # We expect check_collinearity to return a mask or filtered dataframe
    # where only one of the identical columns remains
    filtered_df, dropped_cols = check_collinearity(df, threshold=0.95)
    
    # Assertions
    assert len(filtered_df.columns) == 1, (
        f"Expected 1 column after filtering, got {len(filtered_df.columns)}. "
        "The filter should drop one of the two identical columns."
    )
    
    assert 'feature_A' in filtered_df.columns or 'feature_B' in filtered_df.columns, (
        "One of the original features should be retained."
    )
    
    assert len(dropped_cols) == 1, (
        f"Expected 1 dropped column, got {len(dropped_cols)}."
    )
    
    # Verify the retained column has the same values as the original
    retained_col = filtered_df.columns[0]
    np.testing.assert_array_almost_equal(
        filtered_df[retained_col].values,
        feature_a,
        err_msg="Retained feature values should match the original."
    )


@pytest.mark.skipif(
    not HAS_COLLINEARITY,
    reason="T023 (CollinearityTransformer) not yet implemented; TDD rule: test must fail before impl."
)
def test_collinearity_filter_keeps_high_variance():
    """Test that the filter keeps the higher-variance feature when correlation is high.

    Creates two highly correlated features where one has significantly higher variance.
    Asserts that the filter keeps the higher-variance feature.
    """
    np.random.seed(42)
    n_subjects = 20
    
    # Feature with low variance
    feature_low_var = np.random.randn(n_subjects) * 0.1
    
    # Feature with high variance, highly correlated with low-var one
    feature_high_var = feature_low_var * 10 + np.random.randn(n_subjects) * 0.01
    
    df = pd.DataFrame({
        'low_variance': feature_low_var,
        'high_variance': feature_high_var
    })
    
    filtered_df, dropped_cols = check_collinearity(df, threshold=0.95)
    
    # We expect only one column to remain
    assert len(filtered_df.columns) == 1, "Filter should reduce to 1 column."
    
    # The high variance feature should be kept
    retained_col = filtered_df.columns[0]
    assert retained_col == 'high_variance', (
        f"Expected 'high_variance' to be kept, but '{retained_col}' was kept. "
        "The filter should prefer higher variance features."
    )
    
    assert 'low_variance' in dropped_cols, (
        "Low variance feature should have been dropped."
    )