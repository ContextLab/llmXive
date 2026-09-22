"""
Tests for train.py
"""

import pytest
import os
import json
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.dummy import DummyRegressor

# Mock data for testing
def create_mock_data(n_rows=100):
    """Create a mock dataframe for testing."""
    np.random.seed(42)
    data = {
        'mixing_enthalpy': np.random.randn(n_rows),
        'atomic_size_mismatch': np.random.rand(n_rows),
        'electronegativity_variance': np.random.rand(n_rows),
        'critical_cooling_rate': np.random.rand(n_rows) * 1000,
        'source_label': 'test',
        'composition': 'Cu40Zr40Ti20'
    }
    return pd.DataFrame(data)

def test_train_model():
    """Test model training function."""
    from train import train_model
    df = create_mock_data()
    X = df[['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']]
    y = df['critical_cooling_rate']
    
    model = train_model(X, y)
    assert isinstance(model, RandomForestRegressor)
    assert model.n_estimators == 100
    assert model.random_state == 42

def test_run_cross_validation():
    """Test cross-validation function."""
    from train import run_cross_validation
    df = create_mock_data()
    X = df[['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']]
    y = df['critical_cooling_rate']
    
    scores, indices = run_cross_validation(RandomForestRegressor(n_estimators=10, random_state=42), X, y)
    
    assert len(scores) == 5
    assert all(isinstance(s, float) for s in scores)
    assert len(indices) == 5
    for train_idx, test_idx in indices:
        assert len(train_idx) == 80
        assert len(test_idx) == 20

def test_statistical_test_logic():
    """Test the logic of statistical comparison."""
    # Mock CV scores
    model_scores = [10.0, 11.0, 10.5, 11.5, 10.8]
    null_scores = [20.0, 21.0, 20.5, 21.5, 20.8]
    
    from scipy.stats import ttest_rel
    t_stat, p_value = ttest_rel(model_scores, null_scores)
    
    # With such distinct means, p-value should be very small
    assert p_value < 0.05