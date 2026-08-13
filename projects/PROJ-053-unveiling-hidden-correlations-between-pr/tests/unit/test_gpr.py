import pytest
import numpy as np
import pandas as pd
import tempfile
import os
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
from sklearn.model_selection import cross_val_score, KFold

# Import from the project's models module
from models.gpr_trainer import optimize_hyperparameters, train_gpr_model

def test_optimize_hyperparameters():
    """Test GPR hyperparameter optimization - T021."""
    # Create synthetic data with known non-linear relationship
    np.random.seed(42)
    n_samples = 50
    X = np.random.uniform(0, 1, (n_samples, 2))
    y = np.sin(X[:, 0] * 10) + np.cos(X[:, 1] * 10) + np.random.normal(0, 0.1, n_samples)
    
    # Optimize hyperparameters
    best_kernel, best_params = optimize_hyperparameters(X, y, n_iterations=5)
    
    # Verify results
    assert best_kernel is not None
    assert best_params is not None
    assert isinstance(best_kernel, (C * RBF))
    
    # Verify parameters are reasonable
    assert 'constant_value' in best_params
    assert 'length_scale' in best_params

def test_train_gpr_model():
    """Test GPR model training and prediction."""
    # Create synthetic data
    np.random.seed(42)
    n_samples = 50
    X = np.random.uniform(0, 1, (n_samples, 2))
    y = np.sin(X[:, 0] * 10) + np.cos(X[:, 1] * 10) + np.random.normal(0, 0.1, n_samples)
    
    # Split into train and test
    split_idx = int(0.8 * n_samples)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # Train GPR model
    model, metrics = train_gpr_model(X_train, y_train, X_test, y_test)
    
    # Verify model is trained
    assert model is not None
    assert isinstance(model, GaussianProcessRegressor)
    
    # Verify metrics are computed
    assert 'r2' in metrics
    assert 'rmse' in metrics
    assert 'mae' in metrics
    
    # Verify predictions are reasonable
    assert metrics['r2'] > -1.0  # R2 can be negative but should be > -1 for reasonable model
    assert metrics['rmse'] >= 0
    assert metrics['mae'] >= 0

def test_gpr_uncertainty_quantification():
    """Test that GPR provides uncertainty estimates."""
    np.random.seed(42)
    n_samples = 50
    X = np.random.uniform(0, 1, (n_samples, 2))
    y = np.sin(X[:, 0] * 10) + np.random.normal(0, 0.1, n_samples)
    
    split_idx = int(0.8 * n_samples)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    model, _ = train_gpr_model(X_train, y_train, X_test, y_test)
    
    # Predict with uncertainty
    y_pred, y_std = model.predict(X_test, return_std=True)
    
    # Verify uncertainty estimates
    assert y_pred.shape == y_test.shape
    assert y_std.shape == y_test.shape
    assert all(y_std >= 0)  # Standard deviation should be non-negative

def test_gpr_cross_validation():
    """Test that GPR uses cross-validation for hyperparameter tuning."""
    np.random.seed(42)
    n_samples = 60
    X = np.random.uniform(0, 1, (n_samples, 2))
    y = np.sin(X[:, 0] * 10) + np.cos(X[:, 1] * 10) + np.random.normal(0, 0.1, n_samples)
    
    # Optimize with cross-validation
    best_kernel, best_params = optimize_hyperparameters(X, y, n_iterations=10)
    
    # Verify the kernel has been optimized
    assert best_kernel is not None
    assert best_params is not None
    
    # The optimized kernel should have different parameters than default
    default_kernel = C(1.0, (1e-3, 1e3)) * RBF(1.0, (1e-2, 1e2))
    assert best_kernel != default_kernel or best_params != {'constant_value': 1.0, 'length_scale': 1.0}

def test_gpr_with_small_dataset():
    """Test GPR performance on small dataset (N=50) - T026 validation."""
    np.random.seed(42)
    n_samples = 50
    X = np.random.uniform(0, 1, (n_samples, 2))
    y = np.sin(X[:, 0] * 10) + np.cos(X[:, 1] * 10) + np.random.normal(0, 0.1, n_samples)
    
    split_idx = int(0.8 * n_samples)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    model, metrics = train_gpr_model(X_train, y_train, X_test, y_test)
    
    # Verify the model can achieve reasonable performance on small data
    # This is the success metric from T026: R² > 0.5
    assert metrics['r2'] > 0.5, f"GPR failed to recover signal on synthetic data (R²={metrics['r2']})"

def test_gpr_kernel_structure():
    """Test that the GPR kernel has the correct structure."""
    np.random.seed(42)
    n_samples = 50
    X = np.random.uniform(0, 1, (n_samples, 2))
    y = np.random.normal(0, 1, n_samples)
    
    best_kernel, _ = optimize_hyperparameters(X, y, n_iterations=5)
    
    # Verify kernel structure
    assert hasattr(best_kernel, 'k1')  # C * RBF structure
    assert hasattr(best_kernel, 'k2')
    
    # Verify it's a product of ConstantKernel and RBF
    from sklearn.gaussian_process.kernels import ConstantKernel as C, RBF
    assert isinstance(best_kernel, C * RBF)
