"""
Unit tests for PCA/L1 reduction logic in code/pca_reduction.py.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from pca_reduction import apply_pca, apply_l1_regularization, process_high_dimensional_features

@pytest.fixture
def dummy_data():
    """Generate dummy high-dimensional data for testing."""
    np.random.seed(42)
    n_samples = 100
    n_features = 6000  # > 5000 to trigger reduction
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f"feature_{i}" for i in range(n_features)]
    )
    y = pd.Series(np.random.randn(n_samples))
    
    return X, y

def test_pca_reduction(dummy_data):
    X, y = dummy_data
    n_components = 0.95
    
    X_reduced, pca_model, scaler = apply_pca(X, n_components=n_components)
    
    # Check dimensions
    assert X_reduced.shape[0] == X.shape[0]
    assert X_reduced.shape[1] < X.shape[1]
    assert X_reduced.shape[1] > 0
    
    # Check column names
    assert all(col.startswith("PC") for col in X_reduced.columns)
    
    # Check variance retained
    assert sum(pca_model.explained_variance_ratio_) >= n_components

def test_l1_reduction(dummy_data):
    X, y = dummy_data
    alpha = 0.01
    
    X_reduced, coef, lasso_model, scaler = apply_l1_regularization(X, y, alpha=alpha)
    
    # Check dimensions
    assert X_reduced.shape[0] == X.shape[0]
    assert X_reduced.shape[1] <= X.shape[1]
    assert X_reduced.shape[1] > 0
    
    # Check that coefficients match
    assert len(coef) == X.shape[1]
    assert np.sum(coef != 0) == X_reduced.shape[1]

def test_process_high_dimensional_features_pca(dummy_data):
    X, y = dummy_data
    X_val = X.copy()
    X_test = X.copy()
    
    results = process_high_dimensional_features(
        X_train=X,
        X_val=X_val,
        X_test=X_test,
        y_train=y,
        feature_type="pca",
        variance_threshold=0.95
    )
    
    assert "X_train" in results
    assert "X_val" in results
    assert "X_test" in results
    assert results["metadata"]["method"] == "pca"
    assert results["metadata"]["original_features"] == 6000
    assert results["metadata"]["reduced_features"] < 6000

def test_process_high_dimensional_features_l1(dummy_data):
    X, y = dummy_data
    X_val = X.copy()
    X_test = X.copy()
    
    results = process_high_dimensional_features(
        X_train=X,
        X_val=X_val,
        X_test=X_test,
        y_train=y,
        feature_type="l1",
        l1_alpha=0.01
    )
    
    assert "X_train" in results
    assert "X_val" in results
    assert "X_test" in results
    assert results["metadata"]["method"] == "l1"
    assert results["metadata"]["original_features"] == 6000
    assert results["metadata"]["reduced_features"] <= 6000

def test_skip_reduction_if_features_low():
    """Test that reduction is skipped if features <= 5000."""
    np.random.seed(42)
    n_samples = 100
    n_features = 100
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f"feature_{i}" for i in range(n_features)]
    )
    y = pd.Series(np.random.randn(n_samples))
    
    results = process_high_dimensional_features(
        X_train=X,
        X_val=None,
        X_test=None,
        y_train=y,
        feature_type="pca"
    )
    
    assert results["metadata"]["method"] == "none"
    assert results["metadata"]["original_features"] == 100
    assert results["metadata"]["reduced_features"] == 100