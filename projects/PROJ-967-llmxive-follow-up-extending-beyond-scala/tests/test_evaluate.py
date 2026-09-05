"""
Unit tests for evaluation functions in evaluate.py
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import tempfile
import pickle

# Ensure we can import from code/
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.evaluate import calculate_metrics, calculate_baseline_mae, calculate_permutation_pvalue
from sklearn.linear_model import Ridge
from sklearn.dummy import DummyRegressor

def test_calculate_metrics():
    """Test metrics calculation."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.1, 2.2, 2.8, 4.1, 4.9])
    
    r2, mae = calculate_metrics(y_true, y_pred)
    
    # Check that metrics are calculated
    assert isinstance(r2, float)
    assert isinstance(mae, float)
    assert r2 <= 1.0
    assert mae >= 0.0

def test_calculate_baseline_mae():
    """Test baseline MAE calculation."""
    y_train = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_test = np.array([1.5, 2.5, 3.5, 4.5, 5.5])
    
    # Test with mean strategy
    baseline_mae = calculate_baseline_mae(y_train, y_test, strategy='mean')
    
    # Check that baseline MAE is calculated
    assert isinstance(baseline_mae, float)
    assert baseline_mae >= 0.0

def test_calculate_permutation_pvalue():
    """Test permutation p-value calculation."""
    # Create mock model and data
    X = np.random.rand(50, 5)
    y = np.random.rand(50)
    
    model = Ridge(alpha=1.0)
    model.fit(X, y)
    
    # Calculate permutation p-value
    p_value = calculate_permutation_pvalue(model, X, y, n_permutations=10, random_state=42)
    
    # Check that p-value is calculated
    assert isinstance(p_value, float)
    assert 0.0 <= p_value <= 1.0
