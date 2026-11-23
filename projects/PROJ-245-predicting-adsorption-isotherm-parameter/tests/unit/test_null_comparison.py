import pytest
import numpy as np
import json
from pathlib import Path
from sklearn.metrics import mean_squared_error, r2_score

from models.null_comparison import calculate_null_model_metrics, run_cross_fold_comparison

def test_calculate_null_model_metrics():
    """Test basic metric calculation."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.1, 2.1, 2.9, 4.1, 5.0]) # Slight error
    y_null_pred = np.array([3.0, 3.0, 3.0, 3.0, 3.0]) # Mean of y_true = 3.0

    metrics = calculate_null_model_metrics(y_true, y_pred, y_null_pred)

    assert "main_rmse" in metrics
    assert "null_rmse" in metrics
    assert "rmse_improvement_pct" in metrics
    
    # Check that main RMSE is lower than null RMSE (better prediction)
    assert metrics["main_rmse"] < metrics["null_rmse"]
    
    # Check improvement is positive
    assert metrics["rmse_improvement_pct"] > 0

def test_run_cross_fold_comparison_structure():
    """Test that the cross-fold comparison returns expected structure."""
    # Create simple synthetic data for testing
    np.random.seed(42)
    X = np.random.rand(100, 3)
    y = X[:, 0] + X[:, 1] + np.random.normal(0, 0.1, 100)

    results = run_cross_fold_comparison(X, y, n_splits=3)

    assert "fold_rmse_main" in results
    assert "fold_rmse_null" in results
    assert "t_statistic" in results
    assert "p_value" in results
    assert "is_significant" in results
    assert "r2_ci_main" in results
    assert "r2_ci_null" in results
    
    # Check types
    assert isinstance(results["fold_rmse_main"], list)
    assert isinstance(results["is_significant"], bool)
    assert isinstance(results["r2_ci_main"], dict)
    
    # Check CI structure
    assert "lower" in results["r2_ci_main"]
    assert "upper" in results["r2_ci_main"]