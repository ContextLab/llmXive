import pytest
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from models.null_comparison import (
    predict_mean_null_model,
    calculate_null_model_metrics,
    compare_models_with_bootstrap,
    run_cross_fold_comparison
)

@pytest.fixture
def sample_data():
    """Create sample test data for unit tests."""
    np.random.seed(42)
    n_samples = 100
    
    X = pd.DataFrame({
        'feature1': np.random.randn(n_samples),
        'feature2': np.random.randn(n_samples),
        'feature3': np.random.randn(n_samples)
    })
    
    # Create a target with some signal
    y = 2 * X['feature1'] + 3 * X['feature2'] + np.random.randn(n_samples) * 0.5
    
    return X, y

def test_predict_mean_null_model(sample_data):
    """Test that null model predicts the mean of training targets."""
    X_train, y_train = sample_data
    X_test, y_test = sample_data  # Using same data for simplicity in test
    
    predictions, mean_target = predict_mean_null_model(X_train, y_train, X_test, y_test)
    
    # Check that predictions are all equal to mean
    assert np.allclose(predictions, mean_target)
    assert len(predictions) == len(y_test)
    assert np.isclose(mean_target, y_train.mean())

def test_calculate_null_model_metrics(sample_data):
    """Test metric calculation for null model."""
    X_train, y_train = sample_data
    X_test, y_test = sample_data
    
    predictions, _ = predict_mean_null_model(X_train, y_train, X_test, y_test)
    metrics = calculate_null_model_metrics(y_test, predictions)
    
    assert 'rmse' in metrics
    assert 'r2' in metrics
    assert 'mae' in metrics
    assert isinstance(metrics['rmse'], float)
    assert isinstance(metrics['r2'], float)
    assert isinstance(metrics['mae'], float)
    
    # R2 should be 0 for null model predicting mean
    assert np.isclose(metrics['r2'], 0.0, atol=0.01)

def test_compare_models_with_bootstrap(sample_data):
    """Test model comparison with bootstrap confidence intervals."""
    X, y = sample_data
    
    # Create a simple trained model
    model = LinearRegression()
    model.fit(X, y)
    y_pred_trained = model.predict(X)
    
    # Null model predictions
    y_pred_null, _ = predict_mean_null_model(X, y, X, y)
    
    # Compare models
    results = compare_models_with_bootstrap(y, y_pred_trained, y_pred_null, n_bootstrap=100, seed=42)
    
    assert 'rmse_trained' in results
    assert 'rmse_null' in results
    assert 'r2_trained' in results
    assert 'r2_null' in results
    assert 'r2_ci_trained' in results
    assert 'paired_t_test' in results
    assert 'meets_improvement_threshold' in results
    
    # Trained model should have lower RMSE than null
    assert results['rmse_trained'] < results['rmse_null']
    
    # CI should have lower < upper
    assert results['r2_ci_trained']['lower'] < results['r2_ci_trained']['upper']

def test_run_cross_fold_comparison(sample_data):
    """Test cross-fold comparison logic."""
    X, y = sample_data
    
    model = LinearRegression()
    
    results = run_cross_fold_comparison(X, y, model, n_splits=3, seed=42)
    
    assert 'n_folds' in results
    assert 'avg_rmse_trained' in results
    assert 'avg_rmse_null' in results
    assert 'rmse_reduction_pct' in results
    assert 'paired_t_test' in results
    assert 'r2_ci_trained' in results
    
    # Should have positive RMSE reduction
    assert results['rmse_reduction_pct'] > 0
    
    # Trained model should have better R2
    assert results['avg_r2_trained'] > results['avg_r2_null']

def test_null_model_with_constant_target():
    """Test null model behavior with constant target."""
    X = pd.DataFrame({'f1': [1, 2, 3, 4, 5]})
    y = pd.Series([10, 10, 10, 10, 10])
    
    predictions, mean_target = predict_mean_null_model(X, y, X, y)
    
    assert np.allclose(predictions, 10.0)
    assert np.isclose(mean_target, 10.0)

def test_comparison_with_no_improvement():
    """Test comparison when trained model doesn't improve over null."""
    # Create data where linear model won't help
    X = pd.DataFrame({'f1': [1, 2, 3, 4, 5]})
    y = pd.Series([1, 1, 1, 1, 1])  # Constant target
    
    model = LinearRegression()
    model.fit(X, y)
    y_pred_trained = model.predict(X)
    y_pred_null, _ = predict_mean_null_model(X, y, X, y)
    
    results = compare_models_with_bootstrap(y, y_pred_trained, y_pred_null, n_bootstrap=50, seed=42)
    
    # Both models should have similar performance
    assert np.isclose(results['rmse_trained'], results['rmse_null'], atol=0.1)
    assert np.isclose(results['r2_trained'], results['r2_null'], atol=0.1)