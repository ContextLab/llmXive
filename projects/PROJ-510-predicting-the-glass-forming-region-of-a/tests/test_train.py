"""
Unit tests for model training functions in code/train.py.
"""
import pytest
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from train import load_data, train_model, run_cross_validation, evaluate_on_test

def test_train_model_basic():
    """Test basic model training."""
    X = pd.DataFrame(np.random.rand(100, 5))
    y = pd.Series(np.random.rand(100))
    model = train_model(X, y, random_state=42)
    assert isinstance(model, RandomForestRegressor)
    assert model.random_state == 42

def test_run_cross_validation_basic():
    """Test cross-validation scoring."""
    X = pd.DataFrame(np.random.rand(100, 5))
    y = pd.Series(np.random.rand(100))
    model = RandomForestRegressor(random_state=42)
    scores = run_cross_validation(model, X, y, n_splits=3)
    assert len(scores) == 3
    assert all(isinstance(s, float) for s in scores)

def test_evaluate_on_test_basic():
    """Test evaluation on test set."""
    X = pd.DataFrame(np.random.rand(100, 5))
    y = pd.Series(np.random.rand(100))
    model = RandomForestRegressor(random_state=42)
    model.fit(X, y)
    rmse = evaluate_on_test(model, X, y)
    assert isinstance(rmse, float)
    assert rmse >= 0.0
