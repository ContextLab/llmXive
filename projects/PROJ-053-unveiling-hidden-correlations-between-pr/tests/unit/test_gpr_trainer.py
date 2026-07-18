import pytest
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.model_selection import KFold

from models.gpr_trainer import optimize_hyperparameters, train_gpr_model

@pytest.fixture
def sample_data():
    np.random.seed(42)
    X = np.random.rand(100, 3)
    y = np.sin(X[:, 0]).ravel() + np.random.normal(0, 0.1, 100)
    return X, y

def test_optimize_hyperparameters_structure(sample_data):
    X, y = sample_data
    best_params, mean_lml = optimize_hyperparameters(X, y, n_splits=3)
    
    assert isinstance(best_params, dict)
    assert "kernel" in best_params
    assert "log_marginal_likelihood" in best_params
    assert "optimal_length_scales" in best_params
    assert "optimal_noise_level" in best_params
    
    assert isinstance(mean_lml, float)
    assert not np.isnan(mean_lml)

def test_train_gpr_model_returns_metrics(sample_data):
    X, y = sample_data
    X_train, X_test = X[:80], X[80:]
    y_train, y_test = y[:80], y[80:]
    
    result = train_gpr_model(X_train, y_train, X_test, y_test, target_col="test_target")
    
    assert "model" in result
    assert "scaler" in result
    assert "metrics" in result
    
    metrics = result["metrics"]
    assert "r2_score" in metrics
    assert "rmse" in metrics
    assert "mae" in metrics
    assert "final_log_marginal_likelihood" in metrics
    
    assert metrics["r2_score"] <= 1.0
    assert metrics["rmse"] >= 0
    assert metrics["mae"] >= 0

def test_gpr_model_predicts_uncertainty(sample_data):
    X, y = sample_data
    X_train, X_test = X[:80], X[80:]
    y_train, y_test = y[:80], y[80:]
    
    result = train_gpr_model(X_train, y_train, X_test, y_test, target_col="test_target")
    model = result["model"]
    scaler = result["scaler"]
    
    X_test_scaled = scaler.transform(X_test)
    y_pred, y_std = model.predict(X_test_scaled, return_std=True)
    
    assert len(y_pred) == len(X_test)
    assert len(y_std) == len(X_test)
    assert np.all(y_std >= 0)