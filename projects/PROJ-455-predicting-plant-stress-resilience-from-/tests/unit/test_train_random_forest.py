"""
Unit tests for the Random Forest training functionality.
"""
import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error
import os
import json
import tempfile
import shutil

from code.models.train import train_random_forest, calculate_metric, get_top_features


@pytest.fixture
def sample_data():
    """Generate sample data for testing."""
    np.random.seed(42)
    n_samples = 100
    n_features = 10
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f"metabolite_{i}" for i in range(n_features)]
    )
    # Create a simple linear relationship with some noise
    y = 0.5 * X["metabolite_0"] + 0.3 * X["metabolite_1"] - 0.2 * X["metabolite_2"] + np.random.randn(n_samples) * 0.1
    
    return X, y


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_train_random_forest_returns_model_and_result(sample_data, temp_output_dir):
    """Test that train_random_forest returns a fitted model and result dict."""
    X, y = sample_data
    
    model, result = train_random_forest(
        X=X,
        y=y,
        cv=3,
        mode="individual",
        n_estimators=10,
        output_dir=temp_output_dir
    )
    
    # Check model type
    assert isinstance(model, RandomForestRegressor)
    
    # Check result is a dict
    assert isinstance(result, dict)
    
    # Check required keys in result
    required_keys = ["model_type", "metrics", "hyperparameters", "training_time_seconds", "sample_size"]
    for key in required_keys:
        assert key in result
    
    assert result["model_type"] == "RandomForest"
    assert result["sample_size"] == len(X)
    assert result["metrics"]["metric_name"] == "R²"
    assert "metric_value" in result["metrics"]
    assert result["metrics"]["cv_folds"] == 3


def test_train_random_forest_saves_files(sample_data, temp_output_dir):
    """Test that train_random_forest saves model and result files."""
    X, y = sample_data
    
    model, result = train_random_forest(
        X=X,
        y=y,
        cv=3,
        output_dir=temp_output_dir
    )
    
    # Check files exist
    model_path = os.path.join(temp_output_dir, "random_forest_model.joblib")
    result_path = os.path.join(temp_output_dir, "random_forest_result.json")
    
    assert os.path.exists(model_path)
    assert os.path.exists(result_path)
    
    # Verify result content can be loaded
    with open(result_path, 'r') as f:
        loaded_result = json.load(f)
    
    assert loaded_result["model_type"] == "RandomForest"
    assert "metrics" in loaded_result


def test_train_random_forest_metric_value_reasonable(sample_data, temp_output_dir):
    """Test that the trained model achieves a reasonable R² score."""
    X, y = sample_data
    
    model, result = train_random_forest(
        X=X,
        y=y,
        cv=3,
        output_dir=temp_output_dir
    )
    
    # R² should be between -1 and 1, and for this synthetic data should be > 0
    r2 = result["metrics"]["metric_value"]
    assert -1 <= r2 <= 1
    assert r2 > 0.1  # Should be able to explain some variance


def test_train_random_forest_with_population_mode(sample_data, temp_output_dir):
    """Test training in population mode (Pearson correlation)."""
    X, y = sample_data
    
    model, result = train_random_forest(
        X=X,
        y=y,
        cv=3,
        mode="population",
        output_dir=temp_output_dir
    )
    
    assert result["metrics"]["metric_name"] == "Pearson_r"
    assert "metric_value" in result["metrics"]
    # Correlation should be between -1 and 1
    assert -1 <= result["metrics"]["metric_value"] <= 1


def test_get_top_features(sample_data, temp_output_dir):
    """Test feature importance extraction."""
    X, y = sample_data
    
    model, _ = train_random_forest(
        X=X,
        y=y,
        cv=3,
        n_estimators=10,
        output_dir=temp_output_dir
    )
    
    top_features = get_top_features(model, X.columns.tolist(), n=5)
    
    assert isinstance(top_features, list)
    assert len(top_features) == 5
    
    for feature, importance in top_features:
        assert isinstance(feature, str)
        assert isinstance(importance, float)
        assert importance >= 0
    
    # Features should be sorted by importance descending
    importances = [imp for _, imp in top_features]
    assert importances == sorted(importances, reverse=True)


def test_calculate_metric_individual_mode():
    """Test R² calculation in individual mode."""
    y_true = np.array([1, 2, 3, 4, 5])
    y_pred = np.array([1.1, 2.2, 2.8, 4.1, 4.9])
    
    metric = calculate_metric(y_true, y_pred, mode="individual")
    
    assert isinstance(metric, float)
    assert metric > 0.9  # Very high correlation


def test_calculate_metric_population_mode():
    """Test Pearson correlation calculation in population mode."""
    y_true = np.array([1, 2, 3, 4, 5])
    y_pred = np.array([1.1, 2.2, 2.8, 4.1, 4.9])
    
    metric = calculate_metric(y_true, y_pred, mode="population")
    
    assert isinstance(metric, float)
    assert 0.9 <= metric <= 1.0


def test_calculate_metric_invalid_mode():
    """Test that invalid mode raises ValueError."""
    y_true = np.array([1, 2, 3])
    y_pred = np.array([1, 2, 3])
    
    with pytest.raises(ValueError, match="Unknown mode"):
        calculate_metric(y_true, y_pred, mode="invalid_mode")


def test_train_random_forest_small_dataset(sample_data, temp_output_dir, caplog):
    """Test training on a small dataset (< 50 samples) logs a warning."""
    X, y = sample_data
    X_small = X.iloc[:30]
    y_small = y[:30]
    
    model, result = train_random_forest(
        X=X_small,
        y=y_small,
        cv=3,
        output_dir=temp_output_dir
    )
    
    # Check that a warning was logged
    assert any("50" in str(record.message) and "unreliable" in str(record.message) 
               for record in caplog.records if record.levelname == "WARNING")
