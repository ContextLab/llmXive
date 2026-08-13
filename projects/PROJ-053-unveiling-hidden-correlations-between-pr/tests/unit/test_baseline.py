import pytest
import numpy as np
import pandas as pd
import tempfile
import os

# Import from the project's models module
from models.baseline_trainer import train_linear_baseline

def test_train_linear_baseline():
    """Test linear regression baseline training."""
    # Create synthetic data
    np.random.seed(42)
    n_samples = 100
    X = np.random.uniform(0, 1, (n_samples, 3))
    y = 2 * X[:, 0] + 3 * X[:, 1] - 1 * X[:, 2] + np.random.normal(0, 0.1, n_samples)
    
    # Split into train and test
    split_idx = int(0.8 * n_samples)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # Train baseline
    model, metrics = train_linear_baseline(X_train, y_train, X_test, y_test)
    
    # Verify model is trained
    assert model is not None
    
    # Verify metrics are computed
    assert 'r2' in metrics
    assert 'rmse' in metrics
    assert 'mae' in metrics
    
    # Verify metrics are reasonable
    assert metrics['r2'] >= -1.0  # R2 can be negative
    assert metrics['rmse'] >= 0
    assert metrics['mae'] >= 0

def test_train_linear_baseline_multiple_targets():
    """Test linear regression with multiple target variables."""
    np.random.seed(42)
    n_samples = 100
    X = np.random.uniform(0, 1, (n_samples, 3))
    y = np.column_stack([
        2 * X[:, 0] + 3 * X[:, 1] + np.random.normal(0, 0.1, n_samples),
        1 * X[:, 0] - 2 * X[:, 1] + 4 * X[:, 2] + np.random.normal(0, 0.1, n_samples)
    ])
    
    split_idx = int(0.8 * n_samples)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    model, metrics = train_linear_baseline(X_train, y_train, X_test, y_test)
    
    assert model is not None
    assert 'r2' in metrics
    assert 'rmse' in metrics
    assert 'mae' in metrics

def test_train_linear_baseline_small_dataset():
    """Test linear baseline on small dataset (N=50)."""
    np.random.seed(42)
    n_samples = 50
    X = np.random.uniform(0, 1, (n_samples, 2))
    y = X[:, 0] + X[:, 1] + np.random.normal(0, 0.1, n_samples)
    
    split_idx = int(0.8 * n_samples)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    model, metrics = train_linear_baseline(X_train, y_train, X_test, y_test)
    
    assert model is not None
    assert metrics['r2'] >= -1.0
    assert metrics['rmse'] >= 0

def test_train_linear_baseline_perfect_fit():
    """Test linear baseline with perfect linear relationship."""
    np.random.seed(42)
    n_samples = 100
    X = np.random.uniform(0, 1, (n_samples, 2))
    y = 2 * X[:, 0] + 3 * X[:, 1]  # Perfect linear relationship
    
    split_idx = int(0.8 * n_samples)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    model, metrics = train_linear_baseline(X_train, y_train, X_test, y_test)
    
    # Should achieve near-perfect R²
    assert metrics['r2'] > 0.99
    assert metrics['rmse'] < 0.01
    assert metrics['mae'] < 0.01
