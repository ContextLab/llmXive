"""
Unit tests for modeling module functionality.

Tests verify:
- Nested CV logic and alpha tuning on synthetic data
- Null model performance on permuted data
"""

import pytest
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import Ridge

# Import modeling module (will be implemented in T019)
try:
    from code.modeling import run_ridge_regression, generate_null_distribution
    MODELING_AVAILABLE = True
except ImportError:
    MODELING_AVAILABLE = False

@pytest.mark.skipif(not MODELING_AVAILABLE, reason="modeling module not yet implemented")
def test_nested_cv_logic():
    """Verify nested CV logic and alpha tuning on synthetic data."""
    # Create synthetic data with known correlation (r=0.3)
    np.random.seed(42)
    n_samples = 200
    X = np.random.normal(size=(n_samples, 5))
    # Create target with known relationship
    true_coef = np.array([0.3, 0.0, 0.0, 0.0, 0.0])
    y = X @ true_coef + np.random.normal(scale=1.0, size=n_samples)
    
    # Run ridge regression with nested CV
    results = run_ridge_regression(X, y, cv_folds=5)
    
    # Verify out-of-fold Pearson r falls within expected range (0.25-0.35)
    assert 0.25 <= results['pearson_r'] <= 0.35, f"Expected r in [0.25, 0.35], got {results['pearson_r']}"
    assert results['mae'] > 0, "MAE should be positive"

@pytest.mark.skipif(not MODELING_AVAILABLE, reason="modeling module not yet implemented")
def test_null_model_performance():
    """Verify null model performance is near zero on permuted data."""
    # Create synthetic data
    np.random.seed(42)
    n_samples = 200
    X = np.random.normal(size=(n_samples, 5))
    y = np.random.normal(size=n_samples)
    
    # Generate null distribution with permutation
    null_results = generate_null_distribution(X, y, n_permutations=100)
    
    # Null model should have near-zero performance
    assert abs(null_results['mean_null_mae']) < 0.1, \
        f"Null MAE should be near zero, got {null_results['mean_null_mae']}"

@pytest.mark.skipif(not MODELING_AVAILABLE, reason="modeling module not yet implemented")
def test_alpha_tuning():
    """Verify alpha tuning finds optimal regularization parameter."""
    np.random.seed(42)
    n_samples = 200
    X = np.random.normal(size=(n_samples, 5))
    y = X[:, 0] * 0.5 + np.random.normal(scale=0.5, size=n_samples)
    
    results = run_ridge_regression(X, y, cv_folds=5)
    
    # Optimal alpha should be in a reasonable range
    assert 0.001 <= results['optimal_alpha'] <= 100, \
        f"Optimal alpha should be in [0.001, 100], got {results['optimal_alpha']}"
