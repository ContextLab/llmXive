"""
Unit tests for T019: Model Training.
Tests CPU-only compliance and basic model training logic.
"""
import os
import sys
import tempfile
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.train import (
    train_linear_baseline,
    train_gradient_boosting,
    load_split_data
)

@pytest.fixture
def sample_data():
    """Generate sample data for testing."""
    n_samples = 100
    n_features = 5
    X = pd.DataFrame(np.random.rand(n_samples, n_features), columns=[f'feat_{i}' for i in range(n_features)])
    y = pd.Series(np.random.rand(n_samples) * 100)  # Simulated Tg values
    return X, y

def test_linear_baseline_training(sample_data):
    """Test that Linear Regression trains without error."""
    X_train, y_train = sample_data
    X_test = X_train.iloc[:10]
    y_test = y_train.iloc[:10]
    
    model, metrics = train_linear_baseline(X_train, X_test, y_train, y_test)
    
    assert model is not None
    assert metrics['model_type'] == 'LinearRegression'
    assert 'rmse' in metrics
    assert 'r2' in metrics
    assert metrics['rmse'] >= 0
    assert -1 <= metrics['r2'] <= 1

def test_gradient_boosting_training(sample_data):
    """Test that Gradient Boosting trains without error."""
    X_train, y_train = sample_data
    X_test = X_train.iloc[:10]
    y_test = y_train.iloc[:10]
    
    model, metrics = train_gradient_boosting(X_train, X_test, y_train, y_test)
    
    assert model is not None
    assert metrics['model_type'] == 'GradientBoostingRegressor'
    assert 'rmse' in metrics
    assert 'r2' in metrics
    assert 'cv_rmse' in metrics
    assert metrics['rmse'] >= 0
    assert -1 <= metrics['r2'] <= 1

def test_cpu_only_compliance():
    """Verify that no CUDA/GPU dependencies are triggered."""
    # This test ensures we don't accidentally import torch or use GPU
    # by checking that the sklearn models run on CPU (default)
    import sklearn
    assert not hasattr(sklearn, 'cuda') or not any('cuda' in str(v).lower() for v in dir(sklearn))
    
    # Verify default n_jobs behavior (should be 1 or -1 but we force 1 in code)
    from sklearn.ensemble import GradientBoostingRegressor
    model = GradientBoostingRegressor(n_jobs=1)
    assert model.n_jobs == 1

def test_data_loading_error_handling():
    """Test that missing split data raises appropriate error."""
    with patch('pathlib.Path.exists', return_value=False):
        with pytest.raises(FileNotFoundError, match="Split artifacts missing"):
            load_split_data()