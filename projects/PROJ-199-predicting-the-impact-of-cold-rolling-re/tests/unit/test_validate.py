"""
Unit tests for the model validation module (T027).
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json
import os

# Mock the training functions to avoid dependency on real data/models for unit tests
# We test the validation logic (CV loop, metrics calculation) with synthetic inputs
from unittest.mock import patch, MagicMock

from models.validate import (
    calculate_rmse,
    calculate_r2,
    run_cross_validation,
    validate_models
)

class TestMetrics:
    def test_calculate_rmse(self):
        y_true = np.array([3.0, -0.5, 2.0, 7.0])
        y_pred = np.array([2.5, 0.0, 2.0, 8.0])
        # RMSE = sqrt( (0.25 + 0.25 + 0 + 1) / 4 ) = sqrt(0.375)
        expected = np.sqrt(0.375)
        assert np.isclose(calculate_rmse(y_true, y_pred), expected)

    def test_calculate_r2_perfect(self):
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1, 2, 3, 4, 5])
        assert calculate_r2(y_true, y_pred) == 1.0

    def test_calculate_r2_worse_than_mean(self):
        y_true = np.array([1, 2, 3])
        y_pred = np.array([3, 2, 1]) # Poor prediction
        # R2 should be negative if worse than horizontal line
        r2 = calculate_r2(y_true, y_pred)
        assert r2 < 1.0

class TestCrossValidationLogic:
    @patch('models.validate.train_polynomial_model')
    @patch('models.validate.train_gaussian_process_model')
    def test_run_cv_polynomial(self, mock_gp_train, mock_poly_train):
        # Setup mock models
        mock_poly_model = MagicMock()
        mock_poly_model.predict.return_value = np.array([1.0, 2.0, 3.0])
        mock_poly_train.return_value = mock_poly_model

        X = np.array([[1], [2], [3], [4], [5], [6]])
        y = np.array([1, 2, 3, 4, 5, 6])

        # Run with 2 folds to keep it fast
        results = run_cross_validation(X, y, model_type='polynomial', n_splits=2)

        assert results['model_type'] == 'polynomial'
        assert len(results['fold_metrics']) == 2
        assert 'aggregated' in results
        assert 'rmse_mean' in results['aggregated']
        assert 'r2_mean' in results['aggregated']

    @patch('models.validate.train_polynomial_model')
    @patch('models.validate.train_gaussian_process_model')
    def test_run_cv_gp(self, mock_gp_train, mock_poly_train):
        # Setup mock models
        mock_gp_model = MagicMock()
        mock_gp_model.predict.return_value = np.array([1.0, 2.0, 3.0])
        mock_gp_train.return_value = mock_gp_model

        X = np.array([[1], [2], [3], [4], [5], [6]])
        y = np.array([1, 2, 3, 4, 5, 6])

        results = run_cross_validation(X, y, model_type='gaussian_process', n_splits=2)

        assert results['model_type'] == 'gaussian_process'
        assert len(results['fold_metrics']) == 2

class TestValidateModels:
    @patch('models.validate.load_training_data')
    @patch('models.validate.prepare_features')
    @patch('models.validate.run_cross_validation')
    def test_validate_models_integration(self, mock_cv, mock_prepare, mock_load):
        # Mock data loading
        mock_df = pd.DataFrame({
            'reduction': [10, 20, 30],
            'material': [0, 1, 0],
            'brass_frac': [0.1, 0.2, 0.3],
            'copper_frac': [0.1, 0.1, 0.1]
        })
        mock_load.return_value = mock_df

        # Mock feature preparation
        X = np.array([[10, 0], [20, 1], [30, 0]])
        y = np.array([0.1, 0.2, 0.3])
        mock_prepare.return_value = (X, y, ['reduction', 'material'], ['brass_frac'])

        # Mock CV results
        mock_cv.return_value = {
            'model_type': 'polynomial',
            'n_splits': 5,
            'fold_metrics': [],
            'aggregated': {'rmse_mean': 0.05, 'r2_mean': 0.95}
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_metrics.json"
            # Override default path in function call
            report = validate_models(output_path=output_path)

            assert report is not None
            assert 'models' in report
            assert os.path.exists(output_path)

            # Verify JSON is valid
            with open(output_path) as f:
                loaded = json.load(f)
                assert 'validation_date' in loaded
                assert 'aggregated' in loaded['models']['polynomial_regression']