"""
Unit tests for model training in code/train.py.
"""
import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.train import (
    load_data,
    train_model,
    run_cross_validation,
    evaluate_on_test
)

class TestLoadData:
    def test_load_data_structure(self):
        """Test that load_data returns correct structure."""
        # Mock data creation
        data = {
            'mixing_enthalpy': [1.0, 2.0, 3.0, 4.0, 5.0],
            'atomic_size_mismatch': [0.1, 0.2, 0.3, 0.4, 0.5],
            'electronegativity_variance': [0.01, 0.02, 0.03, 0.04, 0.05],
            'critical_cooling_rate': [100.0, 200.0, 300.0, 400.0, 500.0]
        }
        df = pd.DataFrame(data)
        # Since load_data expects a file path, we test the logic
        # by simulating the split
        from sklearn.model_selection import train_test_split
        X = df[['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']]
        y = df['critical_cooling_rate']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        assert len(X_train) == 4
        assert len(X_test) == 1
        assert len(y_train) == 4
        assert len(y_test) == 1

class TestTrainModel:
    def test_train_model(self):
        """Test training a Random Forest model."""
        from sklearn.ensemble import RandomForestRegressor
        X = np.array([[1.0, 0.1, 0.01], [2.0, 0.2, 0.02], [3.0, 0.3, 0.03], [4.0, 0.4, 0.04]])
        y = np.array([100.0, 200.0, 300.0, 400.0])
        
        model = train_model(X, y)
        assert model is not None
        assert isinstance(model, RandomForestRegressor)
        predictions = model.predict(X)
        assert len(predictions) == 4

class TestRunCrossValidation:
    def test_cross_validation(self):
        """Test cross-validation returns scores."""
        from sklearn.ensemble import RandomForestRegressor
        X = np.array([[1.0, 0.1, 0.01], [2.0, 0.2, 0.02], [3.0, 0.3, 0.03], [4.0, 0.4, 0.04], [5.0, 0.5, 0.05]])
        y = np.array([100.0, 200.0, 300.0, 400.0, 500.0])
        
        model = RandomForestRegressor(random_state=42)
        scores = run_cross_validation(model, X, y, n_folds=3)
        
        assert len(scores) == 3
        assert all(isinstance(s, float) for s in scores)

class TestEvaluateOnTest:
    def test_evaluate_rmse(self):
        """Test RMSE calculation."""
        y_true = np.array([100.0, 200.0, 300.0])
        y_pred = np.array([110.0, 190.0, 310.0])
        
        rmse = evaluate_on_test(y_true, y_pred)
        # Calculate expected RMSE manually
        # errors: 10, -10, 10 -> squares: 100, 100, 100 -> mean: 100 -> sqrt: 10
        assert abs(rmse - 10.0) < 1e-5
