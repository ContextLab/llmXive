import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
import pickle
import json

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.train import train_model, evaluate_model, inner_loop_cv_selection

@pytest.fixture
def sample_data():
    """Create a small synthetic dataset for testing the training functions."""
    np.random.seed(42)
    n_samples = 100
    X = pd.DataFrame({
        'tolerance_factor': np.random.uniform(0.8, 1.1, n_samples),
        'octahedral_factor': np.random.uniform(0.4, 0.9, n_samples),
        'ionic_radius_mismatch': np.random.uniform(0.0, 0.5, n_samples),
        'electronegativity_difference': np.random.uniform(0.0, 2.0, n_samples)
    })
    # Create a target that has some relationship to features
    y = (
        -0.5 * X['tolerance_factor'] +
        -0.3 * X['octahedral_factor'] +
        0.2 * X['ionic_radius_mismatch'] +
        0.1 * X['electronegativity_difference'] +
        np.random.normal(0, 0.05, n_samples)
    )
    return X, y

def test_inner_loop_cv_selection_returns_best_params(sample_data):
    """Test that inner loop CV returns a valid dict with best_params."""
    X, y = sample_data
    results = inner_loop_cv_selection(X, y)
    
    assert 'best_params' in results
    assert 'best_cv_mse' in results
    assert 'best_cv_rmse' in results
    
    params = results['best_params']
    assert 'max_depth' in params
    assert 'min_samples_leaf' in params
    assert params['max_depth'] in [10, 15, 20]
    assert params['min_samples_leaf'] in [1, 2, 4]

def test_train_model_returns_fitted_model(sample_data):
    """Test that train_model returns a fitted RandomForestRegressor."""
    from sklearn.ensemble import RandomForestRegressor
    X, y = sample_data
    best_params = {'max_depth': 10, 'min_samples_leaf': 1}
    
    model = train_model(X, y, best_params)
    
    assert isinstance(model, RandomForestRegressor)
    assert hasattr(model, 'estimators_')  # Check if fitted
    assert len(model.estimators_) > 0

def test_evaluate_model_returns_metrics_dict(sample_data):
    """Test that evaluate_model returns a dict with required keys."""
    from sklearn.ensemble import RandomForestRegressor
    X, y = sample_data
    
    # Train a dummy model first
    model = RandomForestRegressor(random_state=42, n_jobs=-1, max_depth=10)
    model.fit(X, y)
    
    metrics = evaluate_model(model, X, y)
    
    assert 'test_rmse' in metrics
    assert 'test_mae' in metrics
    assert 'test_r2' in metrics
    assert 'n_test_samples' in metrics
    
    assert isinstance(metrics['test_rmse'], float)
    assert metrics['test_rmse'] >= 0
    assert metrics['test_r2'] <= 1.0

def test_full_training_flow(sample_data, tmp_path):
    """Test a simplified full training flow: CV -> Train -> Evaluate."""
    X, y = sample_data
    
    # 1. CV
    cv_results = inner_loop_cv_selection(X, y)
    best_params = cv_results['best_params']
    
    # 2. Train
    model = train_model(X, y, best_params)
    
    # 3. Evaluate
    metrics = evaluate_model(model, X, y)
    
    # Verify consistency
    assert metrics['n_test_samples'] == len(y)
    assert metrics['test_rmse'] < 0.5  # Expect reasonable error on this synthetic data
