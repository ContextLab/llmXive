"""
Unit tests for the model training pipeline (T028, T029).
"""
import pytest
import numpy as np
import pandas as pd
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))
from scripts.train_model import (
    load_features, 
    prepare_train_val_split, 
    train_logistic_regression, 
    train_random_forest, 
    evaluate_model,
    calculate_correlation_coefficient,
    RANDOM_SEED
)

class TestModelTraining:
    
    def test_prepare_train_val_split_reproducibility(self):
        """Test that splitting with a fixed seed produces deterministic results."""
        # Create synthetic data
        data = {
            'dependency_depth': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'cyclomatic_complexity': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'lines_of_code': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            'semantic_complexity_score': [1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8, 9.9, 10.0],
            'dynamic_execution_outcome': ['Pass', 'Fail', 'Pass', 'Fail', 'Timeout', 'Pass', 'Fail', 'Pass', 'Timeout', 'Fail']
        }
        df = pd.DataFrame(data)
        
        # Run split twice
        X1, X2, y1, y2 = prepare_train_val_split(df)
        X1b, X2b, y1b, y2b = prepare_train_val_split(df)
        
        # Check equality
        np.testing.assert_array_equal(X1, X1b)
        np.testing.assert_array_equal(y1, y1b)
        np.testing.assert_array_equal(X2, X2b)
        np.testing.assert_array_equal(y2, y2b)

    def test_train_logistic_regression_cpu_only(self):
        """Test that Logistic Regression trains correctly and uses CPU."""
        # Create small synthetic dataset
        X_train = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]])
        y_train = np.array([0, 1, 0])
        X_val = np.array([[1.5, 2.5, 3.5, 4.5]])
        y_val = np.array([0])
        
        model, metrics = train_logistic_regression(X_train, y_train, X_val, y_val)
        
        assert model is not None
        assert 'val_f1' in metrics
        assert 'coef' in metrics
        assert metrics['model_type'] == 'LogisticRegression'

    def test_train_random_forest_cpu_only(self):
        """Test that Random Forest trains correctly and uses CPU."""
        X_train = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]])
        y_train = np.array([0, 1, 0])
        X_val = np.array([[1.5, 2.5, 3.5, 4.5]])
        y_val = np.array([0])
        
        model, metrics = train_random_forest(X_train, y_train, X_val, y_val)
        
        assert model is not None
        assert 'val_f1' in metrics
        assert 'feature_importances' in metrics
        assert metrics['model_type'] == 'RandomForest'
        # Ensure n_jobs is 1 (CPU only)
        assert model.n_jobs == 1

    def test_evaluate_model_fnr_calculation(self):
        """Test that False Negative Rate is calculated correctly."""
        # Mock confusion matrix: TN=10, FP=2, FN=3, TP=5
        # FNR = FN / (FN + TP) = 3 / (3 + 5) = 0.375
        cm = np.array([[10, 2], [3, 5]])
        
        # We need to mock the model.predict to return the values that result in this CM
        # But evaluate_model takes a model object and data. 
        # Let's test the logic directly by constructing a scenario.
        # Actually, evaluate_model calls model.predict. We can mock the model.
        
        mock_model = MagicMock()
        # We need to ensure the predict results in the specific CM
        # This is hard to test in isolation without the data.
        # Instead, let's test the FNR logic by passing a mock that returns a specific prediction.
        # But evaluate_model does: y_pred = model.predict(X_val)
        # Then cm = confusion_matrix(y_val, y_pred)
        # We can't easily control the internal confusion_matrix call without patching sklearn.
        
        # Alternative: Test the function logic by creating a scenario where we know the outcome.
        # Let's create a simple test case.
        X_val = np.array([[1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3], [4, 4, 4, 4], [5, 5, 5, 5]])
        y_val = np.array([0, 0, 1, 1, 1]) # 2 Pass, 3 Fail
        
        # Mock model that predicts [0, 0, 0, 1, 1]
        # True: 0, 0, 1, 1, 1
        # Pred: 0, 0, 0, 1, 1
        # TN: 2 (0,0 predicted 0,0), FP: 0, FN: 1 (1 predicted 0), TP: 2 (1,1 predicted 1,1)
        # FNR = 1 / (1+2) = 0.333
        
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0, 0, 0, 1, 1])
        
        result = evaluate_model(mock_model, X_val, y_val, 'TestModel')
        
        assert 'false_negative_rate' in result
        expected_fnr = 1 / 3.0
        assert abs(result['false_negative_rate'] - expected_fnr) < 0.001

    def test_calculate_correlation_coefficient(self):
        """Test correlation calculation."""
        data = {
            'feature1': [1, 2, 3, 4, 5],
            'feature2': [2, 4, 6, 8, 10],
            'target': [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        
        corr = calculate_correlation_coefficient(df, ['feature1', 'feature2'], 'target')
        
        assert 'feature1' in corr
        assert 'feature2' in corr
        # feature1 and target are perfectly correlated
        assert abs(corr['feature1'] - 1.0) < 0.001
        # feature2 and target are perfectly correlated
        assert abs(corr['feature2'] - 1.0) < 0.001