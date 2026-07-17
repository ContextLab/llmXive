import pytest
import pandas as pd
import numpy as np
from code.analysis import run_kfold_cross_validation
from code.synthetic_data import generate_synthetic_dataset

@pytest.fixture
def synthetic_regression_data():
    """Generate a synthetic dataset suitable for regression and CV."""
    # Generate data with known relationship
    n_samples = 200
    np.random.seed(42)
    
    # Features
    X1 = np.random.randn(n_samples)
    X2 = np.random.randn(n_samples)
    X3 = np.random.randn(n_samples)
    
    # Target with linear relationship + noise
    y = 2.5 * X1 + 1.5 * X2 - 0.5 * X3 + np.random.randn(n_samples) * 0.5
    
    df = pd.DataFrame({
        'feature_1': X1,
        'feature_2': X2,
        'feature_3': X3,
        'target': y
    })
    return df

def test_kfold_cross_validation_runs(synthetic_regression_data):
    """Test that k-fold CV runs without error and returns expected structure."""
    features = ['feature_1', 'feature_2', 'feature_3']
    target = 'target'
    k = 5
    
    result = run_kfold_cross_validation(synthetic_regression_data, target, features, k)
    
    assert 'k' in result
    assert 'mean_r2' in result
    assert 'std_r2' in result
    assert 'mean_rmse' in result
    assert 'std_rmse' in result
    assert 'fold_scores' in result
    assert len(result['fold_scores']) == k
    
    # Check fold details structure
    for fold in result['fold_scores']:
        assert 'fold' in fold
        assert 'r2' in fold
        assert 'rmse' in fold

def test_kfold_cv_r2_stability(synthetic_regression_data):
    """Test that R² variation is reasonable for a well-behaved synthetic dataset."""
    features = ['feature_1', 'feature_2', 'feature_3']
    target = 'target'
    k = 5
    
    result = run_kfold_cross_validation(synthetic_regression_data, target, features, k)
    
    # For synthetic data with strong signal, R² should be high and stable
    assert result['mean_r2'] > 0.5, f"Expected high R², got {result['mean_r2']}"
    assert result['std_r2'] < 0.2, f"Expected stable R², got std {result['std_r2']}"

def test_kfold_cv_different_k(synthetic_regression_data):
    """Test that CV works with different k values."""
    features = ['feature_1', 'feature_2', 'feature_3']
    target = 'target'
    
    for k in [3, 5, 10]:
        result = run_kfold_cross_validation(synthetic_regression_data, target, features, k)
        assert result['k'] == k
        assert len(result['fold_scores']) == k
        assert result['mean_r2'] > 0 # Should explain some variance

def test_kfold_cv_with_small_dataset():
    """Test CV behavior with a very small dataset."""
    n_samples = 20
    np.random.seed(42)
    X = np.random.randn(n_samples, 2)
    y = X[:, 0] + X[:, 1] + np.random.randn(n_samples) * 0.1
    
    df = pd.DataFrame({
        'f1': X[:, 0],
        'f2': X[:, 1],
        'target': y
    })
    
    # k=5 on 20 samples -> 4 samples per fold
    result = run_kfold_cross_validation(df, 'target', ['f1', 'f2'], k=5)
    
    assert result['k'] == 5
    assert len(result['fold_scores']) == 5
    # Should still run, though variance might be higher
    assert result['mean_r2'] > -1.0 # R² can be negative for poor models, but not extremely so

def test_kfold_cv_feature_mismatch(synthetic_regression_data):
    """Test error handling when feature is missing."""
    features = ['feature_1', 'feature_2', 'missing_feature']
    target = 'target'
    
    with pytest.raises(KeyError):
        run_kfold_cross_validation(synthetic_regression_data, target, features, k=5)