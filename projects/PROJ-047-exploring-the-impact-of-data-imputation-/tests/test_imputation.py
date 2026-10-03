"""
Test suite for imputation methods.
Verifies that applied imputation methods produce complete DataFrames without NaNs.
"""
import pytest
import numpy as np
import pandas as pd
from typing import Dict, Any

# Import the functions from the project's analysis module
from analysis.imputation import (
    apply_mean_imputation,
    apply_knn_imputation,
    apply_mice_imputation
)
from analysis.entities import SyntheticDataset, ImputationResult

# Helper to create a mock SyntheticDataset with missing values
def create_mock_dataset_with_missing(n_samples: int = 100, missing_rate: float = 0.1) -> SyntheticDataset:
    """
    Creates a deterministic mock dataset with intentional missing values in X and Y.
    """
    np.random.seed(42)
    n_features = 5
    
    # Generate synthetic features
    X = np.random.randn(n_samples, n_features)
    T = np.random.binomial(1, 0.5, n_samples)
    Y = 0.5 * T + 0.2 * X[:, 0] + np.random.randn(n_samples) * 0.1
    
    # Introduce missing values (MNAR-like pattern for testing)
    # We will manually mask some values to simulate missingness
    mask = np.random.rand(n_samples, n_features) < missing_rate
    X_masked = X.copy()
    X_masked[mask] = np.nan
    
    # Also add missingness to Y
    y_mask = np.random.rand(n_samples) < (missing_rate * 0.5)
    Y_masked = Y.copy()
    Y_masked[y_mask] = np.nan

    # Construct a DataFrame mimicking the structure expected by imputation functions
    # The pipeline expects a dict-like structure or DataFrame with specific columns
    data_dict = {
        'X': X_masked,
        'T': T.astype(float), # Treatment is usually complete, but we cast to float for consistency
        'Y': Y_masked
    }
    
    # Convert to a single DataFrame for the imputation functions which expect tabular data
    # The imputation functions in the project take a 'data' argument which is expected to be a dict or DataFrame
    # Let's assume the format is a dict of arrays or a DataFrame where columns are features
    # Based on the import signature: `apply_mean_imputation(data)`
    
    # We will construct a DataFrame where X features are prefixed, plus T and Y
    df_data = pd.DataFrame(X_masked, columns=[f'X{i}' for i in range(n_features)])
    df_data['T'] = T.astype(float)
    df_data['Y'] = Y_masked
    
    return df_data

def test_mean_imputation_no_nans():
    """
    Test that apply_mean_imputation produces a DataFrame with no NaN values.
    """
    data = create_mock_dataset_with_missing()
    
    # Verify initial state has NaNs
    assert data.isnull().any().any(), "Test setup failed: No NaNs found in input data."
    
    result = apply_mean_imputation(data)
    
    # Verify result is a DataFrame
    assert isinstance(result, pd.DataFrame), "Result should be a pandas DataFrame."
    
    # Verify no NaNs remain
    assert not result.isnull().any().any(), "Mean imputation failed to fill all NaN values."
    
    # Verify shape is preserved
    assert result.shape == data.shape, "Shape changed after imputation."

def test_knn_imputation_no_nans():
    """
    Test that apply_knn_imputation produces a DataFrame with no NaN values.
    """
    data = create_mock_dataset_with_missing()
    
    # Verify initial state has NaNs
    assert data.isnull().any().any(), "Test setup failed: No NaNs found in input data."
    
    result = apply_knn_imputation(data, k=3) # Use small k for speed in tests
    
    # Verify result is a DataFrame
    assert isinstance(result, pd.DataFrame), "Result should be a pandas DataFrame."
    
    # Verify no NaNs remain
    assert not result.isnull().any().any(), "KNN imputation failed to fill all NaN values."
    
    # Verify shape is preserved
    assert result.shape == data.shape, "Shape changed after imputation."

def test_mice_imputation_no_nans():
    """
    Test that apply_mice_imputation produces a DataFrame with no NaN values.
    """
    data = create_mock_dataset_with_missing()
    
    # Verify initial state has NaNs
    assert data.isnull().any().any(), "Test setup failed: No NaNs found in input data."
    
    result = apply_mice_imputation(data)
    
    # Verify result is a DataFrame
    assert isinstance(result, pd.DataFrame), "Result should be a pandas DataFrame."
    
    # Verify no NaNs remain
    assert not result.isnull().any().any(), "MICE imputation failed to fill all NaN values."
    
    # Verify shape is preserved
    assert result.shape == data.shape, "Shape changed after imputation."

def test_imputation_preserves_columns():
    """
    Test that imputation methods preserve column names.
    """
    data = create_mock_dataset_with_missing()
    original_columns = list(data.columns)
    
    mean_res = apply_mean_imputation(data)
    knn_res = apply_knn_imputation(data)
    mice_res = apply_mice_imputation(data)
    
    assert list(mean_res.columns) == original_columns, "Mean imputation changed columns."
    assert list(knn_res.columns) == original_columns, "KNN imputation changed columns."
    assert list(mice_res.columns) == original_columns, "MICE imputation changed columns."

def test_imputation_on_complete_data():
    """
    Test that imputation methods handle data with no missing values gracefully.
    """
    np.random.seed(42)
    n_samples = 50
    n_features = 3
    X = np.random.randn(n_samples, n_features)
    T = np.random.binomial(1, 0.5, n_samples).astype(float)
    Y = np.random.randn(n_samples)
    
    df = pd.DataFrame(X, columns=[f'X{i}' for i in range(n_features)])
    df['T'] = T
    df['Y'] = Y
    
    # Ensure no NaNs
    assert not df.isnull().any().any()
    
    mean_res = apply_mean_imputation(df)
    knn_res = apply_knn_imputation(df)
    mice_res = apply_mice_imputation(df)
    
    # Results should be equal to input (within floating point tolerance for some methods)
    pd.testing.assert_frame_equal(mean_res, df)
    pd.testing.assert_frame_equal(knn_res, df)
    pd.testing.assert_frame_equal(mice_res, df)
    
    # Ensure no NaNs introduced
    assert not mean_res.isnull().any().any()
    assert not knn_res.isnull().any().any()
    assert not mice_res.isnull().any().any()