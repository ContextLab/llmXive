"""
Tests for imputation methods in the causal inference pipeline.
Verifies that imputation methods produce complete dataframes without NaNs.
"""
import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock

from code.analysis.entities import SyntheticDataset, ImputationResult
from code.analysis.imputation import apply_mean_imputation, apply_knn_imputation, apply_mice_imputation


def test_apply_mean_imputation_no_missing():
    """Test that mean imputation returns original data if no missing values exist."""
    # Create a dataset with no missing values
    X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    T = np.array([0, 1, 0])
    Y = np.array([10.0, 20.0, 30.0])

    dataset = SyntheticDataset(
        X=X,
        T=T,
        Y=Y,
        ground_truth_ate=10.0,
        seed=42
    )

    result = apply_mean_imputation(dataset)

    assert result.imputed is False
    assert result.missing_count == 0
    assert result.imputed_count == 0
    # Verify data is unchanged
    np.testing.assert_array_equal(result.data.X, X)
    np.testing.assert_array_equal(result.data.T, T)
    np.testing.assert_array_equal(result.data.Y, Y)


def test_apply_mean_imputation_with_missing():
    """Test that mean imputation correctly fills missing values."""
    # Create a dataset with missing values
    X = np.array([[1.0, np.nan], [3.0, 4.0], [np.nan, 6.0]])
    T = np.array([0, 1, 0])
    Y = np.array([10.0, np.nan, 30.0])

    dataset = SyntheticDataset(
        X=X,
        T=T,
        Y=Y,
        ground_truth_ate=10.0,
        seed=42
    )

    result = apply_mean_imputation(dataset)

    assert result.imputed is True
    assert result.missing_count > 0
    # Verify no NaNs remain in numeric columns
    imputed_df = pd.DataFrame(result.data.X)
    assert not imputed_df.isnull().any().any()
    assert not np.isnan(result.data.T).any()
    assert not np.isnan(result.data.Y).any()

    # Check that imputed values are the mean of the non-missing values
    # Column 0: 1.0, 3.0 -> mean = 2.0
    # Column 1: 4.0, 6.0 -> mean = 5.0
    # Y: 10.0, 30.0 -> mean = 20.0
    assert result.data.X[0, 1] == 5.0
    assert result.data.X[2, 0] == 2.0
    assert result.data.Y[1] == 20.0


def test_apply_mean_imputation_all_missing_column():
    """Test behavior when an entire column is missing."""
    # Create a dataset where one column is all NaN
    X = np.array([[np.nan, 2.0], [np.nan, 4.0], [np.nan, 6.0]])
    T = np.array([0, 1, 0])
    Y = np.array([10.0, 20.0, 30.0])

    dataset = SyntheticDataset(
        X=X,
        T=T,
        Y=Y,
        ground_truth_ate=10.0,
        seed=42
    )

    # SimpleImputer with mean strategy cannot compute mean if all values are NaN
    # It will fill with 0.0 by default or raise an error depending on configuration.
    # We test that it runs and produces a result without NaNs in the final output
    # if the underlying library handles it, or we catch the specific error if it crashes.
    # For this test, we expect it to run without crashing, but the value might be 0.0.
    result = apply_mean_imputation(dataset)

    assert result.imputed is True
    # The result should not have NaNs if possible, or handle gracefully
    # If sklearn fills with 0, we accept that.
    # We verify the final arrays do not contain NaNs (unless the library explicitly fails)
    assert not pd.isna(result.data.X).any().any()
    assert not pd.isna(result.data.T).any()
    assert not pd.isna(result.data.Y).any()


def test_apply_mean_imputation_invalid_input():
    """Test that invalid input raises appropriate errors."""
    with pytest.raises((ValueError, TypeError)):
        apply_mean_imputation(None)


def test_apply_knn_imputation_no_missing():
    """Test that KNN imputation returns original data if no missing values exist."""
    X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    T = np.array([0, 1, 0])
    Y = np.array([10.0, 20.0, 30.0])

    dataset = SyntheticDataset(
        X=X,
        T=T,
        Y=Y,
        ground_truth_ate=10.0,
        seed=42
    )

    result = apply_knn_imputation(dataset)

    assert result.imputed is False
    assert result.missing_count == 0
    assert result.imputed_count == 0
    np.testing.assert_array_almost_equal(result.data.X, X)
    np.testing.assert_array_equal(result.data.T, T)
    np.testing.assert_array_equal(result.data.Y, Y)


def test_apply_knn_imputation_with_missing():
    """Test that KNN imputation fills missing values."""
    X = np.array([[1.0, np.nan], [3.0, 4.0], [5.0, 6.0]])
    T = np.array([0, 1, 0])
    Y = np.array([10.0, 20.0, 30.0])

    dataset = SyntheticDataset(
        X=X,
        T=T,
        Y=Y,
        ground_truth_ate=10.0,
        seed=42
    )

    result = apply_knn_imputation(dataset)

    assert result.imputed is True
    # Verify no NaNs remain
    assert not pd.isna(result.data.X).any().any()
    assert not pd.isna(result.data.T).any()
    assert not pd.isna(result.data.Y).any()


def test_apply_mice_imputation_no_missing():
    """Test that MICE imputation returns original data if no missing values exist."""
    X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    T = np.array([0, 1, 0])
    Y = np.array([10.0, 20.0, 30.0])

    dataset = SyntheticDataset(
        X=X,
        T=T,
        Y=Y,
        ground_truth_ate=10.0,
        seed=42
    )

    result = apply_mice_imputation(dataset)

    assert result.imputed is False
    assert result.missing_count == 0
    assert result.imputed_count == 0
    np.testing.assert_array_almost_equal(result.data.X, X)
    np.testing.assert_array_equal(result.data.T, T)
    np.testing.assert_array_equal(result.data.Y, Y)


def test_apply_mice_imputation_with_missing():
    """Test that MICE imputation fills missing values."""
    X = np.array([[1.0, np.nan], [3.0, 4.0], [5.0, 6.0]])
    T = np.array([0, 1, 0])
    Y = np.array([10.0, 20.0, 30.0])

    dataset = SyntheticDataset(
        X=X,
        T=T,
        Y=Y,
        ground_truth_ate=10.0,
        seed=42
    )

    result = apply_mice_imputation(dataset)

    assert result.imputed is True
    # Verify no NaNs remain
    assert not pd.isna(result.data.X).any().any()
    assert not pd.isna(result.data.T).any()
    assert not pd.isna(result.data.Y).any()


def test_all_imputation_methods_produce_no_nans():
    """Comprehensive test: all methods must produce dataframes without NaNs."""
    X = np.array([[1.0, np.nan, 3.0], [np.nan, 4.0, 6.0], [7.0, 8.0, np.nan]])
    T = np.array([0, 1, 0])
    Y = np.array([10.0, np.nan, 30.0])

    dataset = SyntheticDataset(
        X=X,
        T=T,
        Y=Y,
        ground_truth_ate=10.0,
        seed=42
    )

    methods = [
        ("Mean", apply_mean_imputation),
        ("KNN", apply_knn_imputation),
        ("MICE", apply_mice_imputation)
    ]

    for name, func in methods:
        result = func(dataset)
        # Check X
        assert not pd.isna(result.data.X).any().any(), f"{name} imputation left NaNs in X"
        # Check T
        assert not pd.isna(result.data.T).any(), f"{name} imputation left NaNs in T"
        # Check Y
        assert not pd.isna(result.data.Y).any(), f"{name} imputation left NaNs in Y"