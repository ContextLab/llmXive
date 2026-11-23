import pytest
import pandas as pd
import numpy as np
from models.train import train_random_forest, calculate_metric

@pytest.fixture
def sample_data():
    """Generate a simple synthetic dataset for testing."""
    np.random.seed(42)
    n_samples = 100
    n_features = 5
    X = pd.DataFrame(
        np.random.rand(n_samples, n_features),
        columns=[f"feature_{i}" for i in range(n_features)]
    )
    # Create a target with some linear relationship + noise
    y = pd.Series(
        2 * X["feature_0"] + 3 * X["feature_1"] + np.random.normal(0, 0.1, n_samples)
    )
    return X, y

def test_train_random_forest_returns_model_and_metrics(sample_data):
    """Test that train_random_forest returns a model and a valid metrics dict."""
    X, y = sample_data
    model, metrics = train_random_forest(X, y, cv=3)

    # Check model type
    from sklearn.ensemble import RandomForestRegressor
    assert isinstance(model, RandomForestRegressor)

    # Check metrics structure
    assert isinstance(metrics, dict)
    assert "r2" in metrics
    assert "rmse" in metrics
    assert "mean_absolute_error" in metrics
    assert "model_type" in metrics
    assert "cv_folds" in metrics
    assert "training_time_seconds" in metrics

    # Check metric types
    assert isinstance(metrics["r2"], float)
    assert isinstance(metrics["rmse"], float)
    assert isinstance(metrics["mean_absolute_error"], float)

    # Check metric constraints
    assert metrics["model_type"] == "RandomForestRegressor"
    assert metrics["cv_folds"] == 3
    assert metrics["training_time_seconds"] >= 0

    # R2 should be reasonable (can be negative but usually close to 1 for this synthetic data)
    # We don't assert a specific value, just that it's a number
    assert isinstance(metrics["r2"], (int, float))

def test_train_random_forest_cv_param(sample_data):
    """Test that the cv parameter is respected."""
    X, y = sample_data
    _, metrics = train_random_forest(X, y, cv=5)
    assert metrics["cv_folds"] == 5

    _, metrics = train_random_forest(X, y, cv=2)
    assert metrics["cv_folds"] == 2