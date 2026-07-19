"""
Unit tests for model_training.py
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import os
import tempfile

from model_training import (
    prepare_features_targets,
    train_gpr,
    train_rf,
    evaluate_model,
    perform_lmm_analysis
)

@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe with features and target."""
    data = {
        'material_id': ['m1', 'm2', 'm3', 'm4', 'm5'],
        'formation_energy': [-1.0, -2.0, -3.0, -4.0, -5.0],
        'feature1': [1.0, 2.0, 3.0, 4.0, 5.0],
        'feature2': [2.0, 3.0, 4.0, 5.0, 6.0],
        'feature3': [3.0, 4.0, 5.0, 6.0, 7.0],
        'dft_computed': [True, True, True, True, True]
    }
    return pd.DataFrame(data)

def test_prepare_features_targets(sample_dataframe):
    """Test feature and target extraction."""
    X, y = prepare_features_targets(sample_dataframe)
    
    assert X.shape == (5, 3), f"Expected (5, 3), got {X.shape}"
    assert y.shape == (5,), f"Expected (5,), got {y.shape}"
    assert np.array_equal(y, np.array([-1.0, -2.0, -3.0, -4.0, -5.0]))

def test_train_gpr():
    """Test GPR training."""
    X = np.random.rand(10, 5)
    y = np.random.rand(10)
    
    model = train_gpr(X, y)
    assert model is not None
    assert hasattr(model, 'kernel_')

def test_train_rf():
    """Test Random Forest training."""
    X = np.random.rand(10, 5)
    y = np.random.rand(10)
    
    model = train_rf(X, y)
    assert model is not None
    assert model.n_estimators == 100

def test_evaluate_model_gpr():
    """Test GPR evaluation including variance and calibration."""
    X_train = np.random.rand(20, 5)
    y_train = np.random.rand(20)
    X_test = np.random.rand(5, 5)
    y_test = np.random.rand(5)
    
    model = train_gpr(X_train, y_train)
    metrics = evaluate_model(model, X_test, y_test, 'GPR')
    
    assert 'rmse' in metrics
    assert 'mae' in metrics
    assert 'variance' in metrics
    assert 'calibration_slope' in metrics
    assert metrics['variance'] >= 0

def test_evaluate_model_rf():
    """Test RF evaluation."""
    X_train = np.random.rand(20, 5)
    y_train = np.random.rand(20)
    X_test = np.random.rand(5, 5)
    y_test = np.random.rand(5)
    
    model = train_rf(X_train, y_train)
    metrics = evaluate_model(model, X_test, y_test, 'RF')
    
    assert 'rmse' in metrics
    assert 'mae' in metrics
    # RF variance is set to 0.0 in this implementation
    assert metrics['variance'] == 0.0
    assert metrics['calibration_slope'] == 0.0

def test_perform_lmm_analysis():
    """Test LMM analysis."""
    # Create dummy metrics dataframe
    data = {
        'sparsity_level': ['low', 'low', 'medium', 'medium', 'high', 'high'],
        'model': ['GPR', 'GPR', 'GPR', 'GPR', 'GPR', 'GPR'],
        'seed': [1, 2, 1, 2, 1, 2],
        'rmse': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
        'mae': [0.05, 0.1, 0.15, 0.2, 0.25, 0.3]
    }
    df = pd.DataFrame(data)
    
    result = perform_lmm_analysis(df)
    assert result is not None
    assert hasattr(result, 'fe_params')
    assert hasattr(result, 'cov_re')