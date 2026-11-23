"""
Unit tests for PCA and L1 regularization logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import functions to test
from pca_reduction import (
    apply_pca, 
    apply_l1_regularization, 
    process_high_dimensional_features
)

@pytest.fixture
def mock_high_dim_data():
    """Generate mock high-dimensional data for testing."""
    n_samples = 100
    n_features = 6000  # Exceeds 5000 threshold
    
    # Create random features with some correlation
    np.random.seed(42)
    X = np.random.randn(n_samples, n_features)
    # Add some structure to make PCA meaningful
    X[:, :10] += np.random.randn(n_samples, 1) * 5 
    
    X_df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(n_features)])
    y = pd.Series(np.random.randn(n_samples), name='target')
    
    return X_df, y

@pytest.fixture
def mock_low_dim_data():
    """Generate mock low-dimensional data."""
    n_samples = 50
    n_features = 10
    
    np.random.seed(42)
    X = np.random.randn(n_samples, n_features)
    X_df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(n_features)])
    y = pd.Series(np.random.randn(n_samples), name='target')
    
    return X_df, y

def test_pca_reduction(mock_high_dim_data):
    """Test that PCA reduces dimensionality and preserves variance."""
    X, y = mock_high_dim_data
    original_features = X.shape[1]
    
    X_pca, pca, scaler = apply_pca(X, variance_threshold=0.95)
    
    # Check that features were reduced
    assert X_pca.shape[1] < original_features, "PCA did not reduce dimensions"
    assert X_pca.shape[0] == X.shape[0], "Sample count changed"
    
    # Check variance preserved
    assert pca.explained_variance_ratio_.sum() >= 0.95, "Variance threshold not met"
    
    # Check output is DataFrame
    assert isinstance(X_pca, pd.DataFrame)
    assert all(col.startswith('PC') for col in X_pca.columns)

def test_l1_regularization(mock_high_dim_data):
    """Test that L1 regularization selects a subset of features."""
    X, y = mock_high_dim_data
    original_features = X.shape[1]
    
    X_selected, lasso, mask = apply_l1_regularization(X, y)
    
    # Check that features were selected
    assert X_selected.shape[1] <= original_features, "L1 selected more features than input"
    assert X_selected.shape[0] == X.shape[0], "Sample count changed"
    
    # Check that at least one feature is selected (unless data is perfect noise)
    assert X_selected.shape[1] > 0, "L1 selected no features"
    
    # Check output is DataFrame
    assert isinstance(X_selected, pd.DataFrame)

def test_process_high_dimensional_threshold(mock_high_dim_data, mock_low_dim_data):
    """Test that reduction is only applied when threshold is exceeded."""
    X_high, y_high = mock_high_dim_data
    X_low, y_low = mock_low_dim_data
    
    # High dimension should trigger reduction
    X_processed_high, method_high = process_high_dimensional_features(
        X_high, y_high, threshold=5000
    )
    assert method_high in ['pca', 'l1'], f"Expected reduction method, got {method_high}"
    assert X_processed_high.shape[1] < X_high.shape[1], "High dim data not reduced"
    
    # Low dimension should not trigger reduction
    X_processed_low, method_low = process_high_dimensional_features(
        X_low, y_low, threshold=5000
    )
    assert method_low == 'none', f"Expected 'none' for low dim, got {method_low}"
    assert X_processed_low.shape[1] == X_low.shape[1], "Low dim data was modified"

def test_pca_column_naming():
    """Test that PCA output has correct column naming."""
    np.random.seed(42)
    X = pd.DataFrame(np.random.randn(20, 100), columns=[f'f{i}' for i in range(100)])
    y = pd.Series(np.random.randn(20))
    
    X_pca, _, _ = apply_pca(X, n_components=5)
    
    expected_cols = ['PC1', 'PC2', 'PC3', 'PC4', 'PC5']
    assert list(X_pca.columns) == expected_cols, "PCA columns not named correctly"
