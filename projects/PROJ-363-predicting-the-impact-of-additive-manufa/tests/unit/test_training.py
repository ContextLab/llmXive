import pytest
import os
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.dummy import DummyRegressor
from sklearn.metrics import r2_score
from train_models import (
    train_gradient_boosting,
    train_mlp,
    train_dummy_baseline,
    run_manual_cv,
    compute_metrics
)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n_samples = 100
    X = pd.DataFrame({
        'feature1': np.random.rand(n_samples),
        'feature2': np.random.rand(n_samples),
        'feature3': np.random.rand(n_samples)
    })
    y = pd.Series(np.random.rand(n_samples))
    return X, y

def test_reproducible_cv_splits(sample_data):
    """Test that 5-fold CV splits are reproducible with fixed seed."""
    X, y = sample_data
    
    # Run CV twice with same seed
    metrics1 = run_manual_cv(GradientBoostingRegressor(random_state=42), X, y, n_splits=5, random_state=42)
    metrics2 = run_manual_cv(GradientBoostingRegressor(random_state=42), X, y, n_splits=5, random_state=42)
    
    # Metrics should be identical
    assert np.allclose(metrics1['r2_scores'], metrics2['r2_scores'])
    assert np.allclose(metrics1['rmse_scores'], metrics2['rmse_scores'])
    assert np.allclose(metrics1['r2_mean'], metrics2['r2_mean'])

def test_cpu_only_execution(sample_data):
    """Test that training does not assign CUDA devices (CPU-only constraint)."""
    X, y = sample_data
    
    # Train models
    gb_model = train_gradient_boosting(X, y)
    mlp_model = train_mlp(X, y)
    
    # Check that models don't have CUDA device assignments
    # For sklearn models, this means no torch/cuda usage
    assert not hasattr(gb_model, 'device') or gb_model.device != 'cuda'
    assert not hasattr(mlp_model, 'device') or mlp_model.device != 'cuda'
    
    # Verify models can make predictions
    predictions = gb_model.predict(X.head())
    assert len(predictions) == len(X.head())
    
    predictions = mlp_model.predict(X.head())
    assert len(predictions) == len(X.head())

def test_gradient_boosting_training(sample_data):
    """Test that Gradient Boosting model trains successfully."""
    X, y = sample_data
    model = train_gradient_boosting(X, y)
    
    # Verify model is fitted
    assert hasattr(model, 'estimators_')
    assert len(model.estimators_) == 100  # n_estimators=100

def test_mlp_training(sample_data):
    """Test that MLP model trains successfully."""
    X, y = sample_data
    model = train_mlp(X, y)
    
    # Verify model is fitted
    assert hasattr(model, 'coefs_')
    assert len(model.coefs_) > 0

def test_dummy_baseline_training(sample_data):
    """Test that Dummy baseline model trains successfully."""
    X, y = sample_data
    model = train_dummy_baseline(X, y)
    
    # Verify model is fitted
    assert hasattr(model, 'constant_')

def test_compute_metrics(sample_data):
    """Test metric computation."""
    X, y = sample_data
    y_pred = y + np.random.normal(0, 0.1, len(y))
    
    rmse, r2 = compute_metrics(y, y_pred)
    
    assert rmse > 0
    assert r2 <= 1.0
    assert r2 >= -1.0  # R² can be negative

def test_cv_fold_count(sample_data):
    """Test that CV uses correct number of folds."""
    X, y = sample_data
    model = GradientBoostingRegressor(random_state=42)
    
    metrics = run_manual_cv(model, X, y, n_splits=5, random_state=42)
    
    assert len(metrics['r2_scores']) == 5
    assert len(metrics['rmse_scores']) == 5