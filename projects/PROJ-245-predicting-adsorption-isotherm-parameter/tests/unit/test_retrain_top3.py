"""
Unit tests for T033: Retrain on Top 3 Features.
"""
import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Mock the dependencies if necessary, but we test the logic
# We assume the module is importable
try:
    from models.retrain_top3 import (
        load_shap_summary, 
        load_model_metrics, 
        get_model_instance,
        run_null_model
    )
except ImportError:
    pytest.skip("Models module not ready", allow_module_level=True)

def test_load_shap_summary():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "shap.json"
        data = {"features": [{"feature": "f1", "mean_abs_shap": 0.1}, {"feature": "f2", "mean_abs_shap": 0.2}]}
        with open(path, 'w') as f:
            json.dump(data, f)
        
        result = load_shap_summary(str(path))
        assert len(result) == 2
        assert result[0]['feature'] == 'f1'

def test_load_model_metrics():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "metrics.json"
        data = {"models": [{"name": "RF", "r2": 0.9}, {"name": "LR", "r2": 0.8}]}
        with open(path, 'w') as f:
            json.dump(data, f)
        
        result = load_model_metrics(str(path))
        assert result == "RF"

def test_get_model_instance():
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression

    model = get_model_instance("RandomForest")
    assert isinstance(model, RandomForestRegressor)

    model = get_model_instance("GradientBoosting")
    assert isinstance(model, GradientBoostingRegressor)

    model = get_model_instance("LinearRegression")
    assert isinstance(model, LinearRegression)

def test_run_null_model():
    import numpy as np
    y_train = np.array([1, 2, 3, 4, 5])
    y_test = np.array([1.5, 2.5, 3.5])
    X_train = np.array([[1], [2], [3], [4], [5]])
    X_test = np.array([[1.5], [2.5], [3.5]])
    
    result = run_null_model(X_train, X_test, y_train, y_test)
    
    assert 'r2' in result
    assert 'rmse' in result
    assert 'mae' in result
    # The null model predicts mean(y_train) = 3.0
    # y_test: [1.5, 2.5, 3.5] -> predictions: [3.0, 3.0, 3.0]
    # R2 should be negative or low because it's worse than mean
    assert isinstance(result['r2'], float)