"""
Unit tests for Null Model Comparison (T024).
"""
import pytest
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from models.null_comparison import (
    predict_mean_null_model, 
    calculate_null_model_metrics, 
    run_cross_fold_comparison
)

def test_predict_mean_null_model():
    """Test that null model predicts the mean of training data."""
    X_train = np.array([[1], [2], [3]])
    y_train = np.array([2.0, 4.0, 6.0])
    X_test = np.array([[5], [6]])
    y_test = np.array([10.0, 12.0]) # True values don't matter for prediction logic

    predictions, mean_val = predict_mean_null_model(X_train, y_train, X_test, y_test)
    
    assert mean_val == 4.0
    assert np.all(predictions == 4.0)
    assert len(predictions) == len(y_test)

def test_calculate_null_model_metrics():
    """Test metric calculation for null model."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([3.0, 3.0, 3.0, 3.0, 3.0]) # Mean is 3.0

    metrics = calculate_null_model_metrics(y_true, y_pred)

    # R2 for constant prediction is 0 if mean is used correctly? 
    # R2 = 1 - SS_res/SS_tot. SS_res = sum((y - mean)^2). SS_tot = sum((y - mean)^2). R2 = 0.
    assert abs(metrics['r2']) < 1e-6
    assert metrics['rmse'] > 0
    assert metrics['mae'] > 0

def test_run_cross_fold_comparison():
    """Test the cross-fold comparison logic."""
    # Generate simple linear data
    np.random.seed(42)
    X = np.random.rand(100, 2)
    y = 3 * X[:, 0] + 2 * X[:, 1] + np.random.normal(0, 0.1, 100)

    model = LinearRegression()
    model.fit(X, y)

    results = run_cross_fold_comparison(X, y, "LinearRegression", model, n_splits=3)

    assert 'fold_metrics' in results
    assert 'statistical_test' in results
    assert 'summary' in results
    
    # Check that trained RMSE is generally lower than null RMSE
    trained_rmses = results['fold_metrics']['trained_rmse']
    null_rmses = results['fold_metrics']['null_rmse']
    
    # It's possible for a fold to be worse by chance, but mean should be better
    assert np.mean(trained_rmses) < np.mean(null_rmses), "Trained model should outperform null model on average"
    
    # Check statistical test structure
    assert 'p_value' in results['statistical_test']
    assert 'is_significant' in results['statistical_test']
    
    # Check summary
    assert 'improvement_pct' in results['summary']
    assert results['summary']['improvement_pct'] > -100 # Should be a valid percentage
    
    # Check confidence intervals structure
    assert 'confidence_intervals' in results
    assert 'r2' in results['confidence_intervals']
    assert 'ci_95_lower' in results['confidence_intervals']['r2']
    assert 'ci_95_upper' in results['confidence_intervals']['r2']