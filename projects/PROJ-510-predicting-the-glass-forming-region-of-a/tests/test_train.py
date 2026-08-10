import pytest
import os
import json
import numpy as np
from sklearn.dummy import DummyRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import pandas as pd

# Import functions from the module under test
# Note: Assuming the test runner is executed from the project root
# and code/ is in the PYTHONPATH.
try:
    from code.train import generate_null_distribution, train_model, load_data
except ImportError:
    # Fallback for different execution contexts
    from train import generate_null_distribution, train_model, load_data

@pytest.fixture
def sample_data():
    """Create a small synthetic dataset for testing logic (not for final results)."""
    rng = np.random.RandomState(42)
    X = rng.randn(100, 3)
    y = 2 * X[:, 0] + 0.5 * X[:, 1] + rng.randn(100) * 0.1
    return X, y

def test_generate_null_distribution_structure(sample_data):
    """Test that generate_null_distribution returns the expected structure."""
    X, y = sample_data
    result = generate_null_distribution(X, y, n_bootstrap=10, random_state=42)
    
    assert isinstance(result, dict)
    assert "n_bootstrap" in result
    assert result["n_bootstrap"] == 10
    assert "strategy" in result
    assert result["strategy"] == "mean"
    assert "rmse_mean" in result
    assert "rmse_std" in result
    assert "rmse_percentiles" in result
    assert "raw_rmse_values" in result
    assert len(result["raw_rmse_values"]) == 10
    assert isinstance(result["raw_rmse_values"][0], float)

def test_generate_null_distribution_reproducibility(sample_data):
    """Test that the function produces reproducible results with the same seed."""
    X, y = sample_data
    result1 = generate_null_distribution(X, y, n_bootstrap=50, random_state=42)
    result2 = generate_null_distribution(X, y, n_bootstrap=50, random_state=42)
    
    assert result1["rmse_mean"] == result2["rmse_mean"]
    assert result1["raw_rmse_values"] == result2["raw_rmse_values"]

def test_generate_null_distribution_values(sample_data):
    """Test that the RMSE values are positive and reasonable."""
    X, y = sample_data
    result = generate_null_distribution(X, y, n_bootstrap=20, random_state=42)
    
    raw_values = np.array(result["raw_rmse_values"])
    assert np.all(raw_values > 0), "RMSE values must be positive"
    assert result["rmse_mean"] > 0
    assert result["rmse_std"] >= 0

def test_dummy_regressor_consistency(sample_data):
    """Verify that the null distribution aligns with manual DummyRegressor calculation."""
    X, y = sample_data
    rng = np.random.RandomState(42)
    
    # Manual calculation for one bootstrap sample
    indices = rng.choice(len(y), size=len(y), replace=True)
    X_boot = X[indices]
    y_boot = y[indices]
    
    dummy = DummyRegressor(strategy='mean')
    dummy.fit(X_boot, y_boot)
    y_pred = dummy.predict(X_boot)
    manual_rmse = np.sqrt(mean_squared_error(y_boot, y_pred))
    
    # Get the first value from the function (it should use the same seed)
    # Note: The function resets the seed at the start, so the first iteration matches.
    result = generate_null_distribution(X, y, n_bootstrap=1, random_state=42)
    function_rmse = result["raw_rmse_values"][0]
    
    # Allow for small floating point differences if any, though they should be identical
    assert np.isclose(manual_rmse, function_rmse), "Manual and function RMSE should match"

def test_null_distribution_size(sample_data):
    """Ensure the output list size matches n_bootstrap."""
    X, y = sample_data
    n_boot = 150
    result = generate_null_distribution(X, y, n_bootstrap=n_boot, random_state=42)
    assert len(result["raw_rmse_values"]) == n_boot