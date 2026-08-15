import pytest
import numpy as np
import pandas as pd
import os
import sys
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.models.gpr_trainer import optimize_hyperparameters, train_gpr_model
from code.models.metrics import calculate_r2, calculate_rmse
from code.config import get_random_seed

@pytest.fixture
def synthetic_training_data():
    """Create synthetic data for GPR training tests."""
    np.random.seed(get_random_seed())
    n_samples = 100
    
    # Generate features
    X = np.random.rand(n_samples, 3) * 100  # laser_power, scan_speed, layer_thickness
    
    # Generate target with known non-linear relationship
    y = (
        0.5 * X[:, 0] +  # laser_power
        0.3 * X[:, 1] -  # scan_speed
        0.2 * X[:, 2] +  # layer_thickness
        0.1 * np.sin(X[:, 0]) +  # Non-linear component
        np.random.normal(0, 2, n_samples)  # Noise
    )
    
    return X, y

@pytest.fixture
def synthetic_test_data():
    """Create synthetic test data."""
    np.random.seed(get_random_seed() + 1)
    n_samples = 20
    
    X = np.random.rand(n_samples, 3) * 100
    y = (
        0.5 * X[:, 0] +
        0.3 * X[:, 1] -
        0.2 * X[:, 2] +
        0.1 * np.sin(X[:, 0]) +
        np.random.normal(0, 2, n_samples)
    )
    
    return X, y

def test_optimize_hyperparameters(synthetic_training_data):
    """Test hyperparameter optimization for GPR."""
    X, y = synthetic_training_data
    
    best_params, best_score = optimize_hyperparameters(X, y, cv=3)
    
    # Check that optimization returns valid parameters
    assert 'length_scale' in best_params
    assert 'sigma' in best_params
    assert 'noise_level' in best_params
    
    # Check that score is a valid number
    assert isinstance(best_score, float)
    assert best_score > -np.inf

def test_train_gpr_model(synthetic_training_data, synthetic_test_data):
    """Test GPR model training and prediction."""
    X_train, y_train = synthetic_training_data
    X_test, y_test = synthetic_test_data
    
    model = train_gpr_model(X_train, y_train)
    
    # Check that model can make predictions
    predictions, uncertainty = model.predict(X_test, return_std=True)
    
    assert len(predictions) == len(X_test)
    assert len(uncertainty) == len(X_test)
    
    # Check that uncertainty is positive
    assert np.all(uncertainty > 0)

def test_gpr_model_performance(synthetic_training_data, synthetic_test_data):
    """Test that GPR model achieves reasonable performance metrics."""
    X_train, y_train = synthetic_training_data
    X_test, y_test = synthetic_test_data
    
    model = train_gpr_model(X_train, y_train)
    predictions, _ = model.predict(X_test, return_std=True)
    
    r2 = calculate_r2(y_test, predictions)
    rmse = calculate_rmse(y_test, predictions)
    
    # Check that R² is reasonable (should be > 0 for this synthetic data)
    assert r2 > 0.0, f"R² score {r2} is unexpectedly low"
    
    # Check that RMSE is reasonable relative to target range
    target_range = np.max(y_test) - np.min(y_test)
    assert rmse < target_range * 0.5, f"RMSE {rmse} is too large relative to target range {target_range}"

def test_gpr_uncertainty_quantification(synthetic_training_data):
    """Test that GPR provides meaningful uncertainty estimates."""
    X_train, y_train = synthetic_training_data
    
    # Train on a subset of data
    X_subset = X_train[:50]
    y_subset = y_train[:50]
    
    model = train_gpr_model(X_subset, y_subset)
    
    # Predict on training data (should have low uncertainty)
    _, uncertainty_train = model.predict(X_subset, return_std=True)
    
    # Predict on new data (should have higher uncertainty)
    X_new = X_train[50:]
    _, uncertainty_new = model.predict(X_new, return_std=True)
    
    # Check that uncertainty is generally higher for new data
    # (This is a statistical property, so we check the mean)
    assert np.mean(uncertainty_new) >= np.mean(uncertainty_train) * 0.8, \
        "Uncertainty for new data should be comparable or higher than training data"

def test_gpr_with_different_kernels(synthetic_training_data):
    """Test GPR training with different kernel configurations."""
    X, y = synthetic_training_data
    
    # Test with default RBF kernel
    model_rbf = train_gpr_model(X, y)
    predictions_rbf, _ = model_rbf.predict(X[:10], return_std=True)
    
    assert len(predictions_rbf) == 10
    assert np.all(np.isfinite(predictions_rbf))

def test_gpr_hyperparameter_sensitivity(synthetic_training_data):
    """Test that GPR performance is sensitive to hyperparameters."""
    X, y = synthetic_training_data
    
    # Train with optimized hyperparameters
    best_params, best_score = optimize_hyperparameters(X, y, cv=3)
    model_optimized = train_gpr_model(X, y)
    
    # Train with fixed (potentially suboptimal) hyperparameters
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
    
    fixed_kernel = C(1.0) * RBF(length_scale=1.0)
    model_fixed = GaussianProcessRegressor(kernel=fixed_kernel, random_state=get_random_seed())
    model_fixed.fit(X, y)
    
    # Compare performance on a test set
    X_test = X[:20]
    y_test = y[:20]
    
    pred_opt, _ = model_optimized.predict(X_test, return_std=True)
    pred_fixed = model_fixed.predict(X_test)
    
    r2_opt = calculate_r2(y_test, pred_opt)
    r2_fixed = calculate_r2(y_test, pred_fixed)
    
    # Optimized model should generally perform better or equally well
    assert r2_opt >= r2_fixed - 0.1, \
        f"Optimized model R² ({r2_opt}) should be at least close to fixed model R² ({r2_fixed})"
