"""
Unit tests for T030: Performance metric calculation (RMSE, R², AIC).
"""
import pytest
import numpy as np
import math
from code.validation_metrics import (
    calculate_rmse, 
    calculate_r2, 
    calculate_aic, 
    calculate_metrics_for_fold,
    aggregate_metrics_across_folds
)

def test_calculate_rmse_basic():
    """Test basic RMSE calculation."""
    y_true = np.array([1, 2, 3, 4, 5])
    y_pred = np.array([1, 2, 3, 4, 5])
    assert calculate_rmse(y_true, y_pred) == 0.0

def test_calculate_rmse_error():
    """Test RMSE with prediction errors."""
    y_true = np.array([1, 2, 3, 4, 5])
    y_pred = np.array([1.1, 2.1, 2.9, 4.1, 5.1])
    # Manual calculation: sqrt(mean((0.1)^2 * 5)) = sqrt(0.05) ≈ 0.2236
    expected = np.sqrt(np.mean((y_true - y_pred) ** 2))
    assert abs(calculate_rmse(y_true, y_pred) - expected) < 1e-6

def test_calculate_rmse_mismatched_length():
    """Test that RMSE raises error for mismatched lengths."""
    with pytest.raises(ValueError):
        calculate_rmse(np.array([1, 2, 3]), np.array([1, 2]))

def test_calculate_r2_perfect():
    """Test R² for perfect predictions."""
    y_true = np.array([1, 2, 3, 4, 5])
    y_pred = np.array([1, 2, 3, 4, 5])
    assert calculate_r2(y_true, y_pred) == 1.0

def test_calculate_r2_worse_than_mean():
    """Test R² for predictions worse than mean (should be negative)."""
    y_true = np.array([1, 2, 3, 4, 5])
    y_pred = np.array([5, 4, 3, 2, 1]) # Perfectly inverse
    r2 = calculate_r2(y_true, y_pred)
    # SS_res is large, SS_tot is fixed. R2 = 1 - (SS_res/SS_tot)
    # SS_tot = sum((y - mean)^2) = 10
    # SS_res = sum((y - y_pred)^2) = sum((y - (6-y))^2) = sum((2y-6)^2)
    # y=1: (2-6)^2=16, y=2: (4-6)^2=4, y=3:0, y=4:4, y=5:16 -> sum=40
    # R2 = 1 - 40/10 = -3
    assert r2 < 0

def test_calculate_r2_constant_prediction():
    """Test R² when predictions are constant (mean of y)."""
    y_true = np.array([1, 2, 3, 4, 5])
    y_pred = np.array([3, 3, 3, 3, 3]) # Mean of y_true
    r2 = calculate_r2(y_true, y_pred)
    assert abs(r2 - 0.0) < 1e-6

def test_calculate_aic():
    """Test AIC calculation."""
    n = 100
    rss = 10.0
    k = 3
    # AIC = n*ln(RSS/n) + 2k = 100*ln(0.1) + 6
    expected = n * np.log(rss / n) + 2 * k
    assert abs(calculate_aic(n, rss, k) - expected) < 1e-6

def test_calculate_aic_zero_rss():
    """Test AIC with zero RSS (should return NaN)."""
    result = calculate_aic(10, 0.0, 3)
    assert math.isnan(result)

def test_calculate_metrics_for_fold():
    """Test full metric calculation for a single fold."""
    fold_data = {
        'y_true': [1, 2, 3, 4, 5],
        'y_pred': [1.1, 2.2, 2.8, 4.1, 4.9],
        'model_type': 'OLS',
        'fold_index': 0,
        'n_params': 3
    }
    metrics = calculate_metrics_for_fold(fold_data)
    
    assert metrics['model_type'] == 'OLS'
    assert metrics['fold_index'] == 0
    assert 'rmse' in metrics
    assert 'r2' in metrics
    assert 'aic' in metrics
    assert not np.isnan(metrics['rmse'])
    assert not np.isnan(metrics['r2'])
    assert not np.isnan(metrics['aic'])

def test_aggregate_metrics_across_folds():
    """Test aggregation of metrics across multiple folds."""
    fold_metrics = [
        {'model_type': 'OLS', 'fold_index': 0, 'rmse': 1.0, 'r2': 0.9, 'aic': 100.0},
        {'model_type': 'OLS', 'fold_index': 1, 'rmse': 2.0, 'r2': 0.8, 'aic': 110.0},
        {'model_type': 'Spatial Lag', 'fold_index': 0, 'rmse': 0.5, 'r2': 0.95, 'aic': 90.0},
    ]
    
    aggregated = aggregate_metrics_across_folds(fold_metrics)
    
    assert 'OLS' in aggregated
    assert 'Spatial Lag' in aggregated
    
    # Check OLS aggregation
    ols_stats = aggregated['OLS']
    assert ols_stats['n_folds'] == 2
    assert ols_stats['rmse_mean'] == 1.5
    assert ols_stats['r2_mean'] == 0.85
    assert ols_stats['aic_mean'] == 105.0

def test_aggregate_metrics_empty():
    """Test aggregation with empty list."""
    aggregated = aggregate_metrics_across_folds([])
    assert aggregated == {}