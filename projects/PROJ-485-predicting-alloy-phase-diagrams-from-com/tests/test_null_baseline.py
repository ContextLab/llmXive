"""
Tests for null baseline model implementation.

These tests verify the global mean baseline model and comparison logic
as required by FR-009.
"""
import os
import sys
import json
import tempfile
import shutil
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.null_baseline import (
    compute_global_mean,
    predict_null_model,
    evaluate_model,
    compare_models,
    run_null_baseline_analysis
)


class TestComputeGlobalMean:
    """Tests for compute_global_mean function."""

    def test_compute_mean_basic(self):
        """Test basic mean calculation."""
        y = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        expected_mean = 30.0
        result = compute_global_mean(y)
        assert result == expected_mean

    def test_compute_mean_negative(self):
        """Test mean calculation with negative values."""
        y = np.array([-10.0, -20.0, -30.0])
        expected_mean = -20.0
        result = compute_global_mean(y)
        assert result == expected_mean

    def test_compute_mean_single_value(self):
        """Test mean calculation with single value."""
        y = np.array([42.0])
        expected_mean = 42.0
        result = compute_global_mean(y)
        assert result == expected_mean

    def test_compute_mean_floats(self):
        """Test mean calculation with floating point values."""
        y = np.array([1.5, 2.5, 3.5, 4.5])
        expected_mean = 3.0
        result = compute_global_mean(y)
        assert result == expected_mean


class TestPredictNullModel:
    """Tests for predict_null_model function."""

    def test_predict_all_same(self):
        """Test that all predictions are equal to global mean."""
        X = np.array([[1, 2], [3, 4], [5, 6]])
        global_mean = 25.0
        predictions = predict_null_model(X, global_mean)

        assert len(predictions) == 3
        assert np.all(predictions == global_mean)

    def test_predict_shape(self):
        """Test that predictions have correct shape."""
        X = np.random.rand(100, 10)
        global_mean = 15.0
        predictions = predict_null_model(X, global_mean)

        assert predictions.shape == (100,)

    def test_predict_ignores_features(self):
        """Test that feature values don't affect predictions."""
        X1 = np.array([[1, 1], [2, 2]])
        X2 = np.array([[100, 200], [300, 400]])
        global_mean = 50.0

        pred1 = predict_null_model(X1, global_mean)
        pred2 = predict_null_model(X2, global_mean)

        assert np.array_equal(pred1, pred2)


class TestEvaluateModel:
    """Tests for evaluate_model function."""

    def test_perfect_prediction(self):
        """Test evaluation with perfect predictions."""
        y_true = np.array([10.0, 20.0, 30.0])
        y_pred = np.array([10.0, 20.0, 30.0])

        metrics = evaluate_model(y_true, y_pred)

        assert metrics['mae'] == 0.0
        assert metrics['r2'] == 1.0

    def test_constant_prediction(self):
        """Test evaluation with constant predictions (null model scenario)."""
        y_true = np.array([10.0, 20.0, 30.0])
        y_pred = np.array([20.0, 20.0, 20.0])  # Global mean

        metrics = evaluate_model(y_true, y_pred)

        # MAE should be positive
        assert metrics['mae'] > 0
        # R² should be 0 for constant prediction equal to mean
        assert abs(metrics['r2']) < 1e-6

    def test_worse_than_mean(self):
        """Test evaluation when predictions are worse than mean."""
        y_true = np.array([10.0, 20.0, 30.0])
        y_pred = np.array([50.0, 50.0, 50.0])  # Far from mean

        metrics = evaluate_model(y_true, y_pred)

        assert metrics['mae'] > 0
        # R² should be negative (worse than horizontal line)
        assert metrics['r2'] < 0


class TestCompareModels:
    """Tests for compare_models function."""

    def test_rf_better(self):
        """Test comparison when RF model is better."""
        null_metrics = {'mae': 10.0, 'r2': 0.0}
        rf_metrics = {'mae': 5.0, 'r2': 0.5}

        comparison = compare_models(null_metrics, rf_metrics)

        assert comparison['mae_improvement_percent'] == 50.0
        assert comparison['r2_improvement'] == 0.5
        assert comparison['rf_better'] is True

    def test_rf_worse(self):
        """Test comparison when RF model is worse."""
        null_metrics = {'mae': 5.0, 'r2': 0.5}
        rf_metrics = {'mae': 10.0, 'r2': 0.0}

        comparison = compare_models(null_metrics, rf_metrics)

        assert comparison['mae_improvement_percent'] == -100.0
        assert comparison['r2_improvement'] == -0.5
        assert comparison['rf_better'] is False

    def test_equal_performance(self):
        """Test comparison when models perform equally."""
        null_metrics = {'mae': 10.0, 'r2': 0.0}
        rf_metrics = {'mae': 10.0, 'r2': 0.0}

        comparison = compare_models(null_metrics, rf_metrics)

        assert comparison['mae_improvement_percent'] == 0.0
        assert comparison['r2_improvement'] == 0.0
        assert comparison['rf_better'] is False

    def test_zero_null_mae(self):
        """Test comparison when null model MAE is zero."""
        null_metrics = {'mae': 0.0, 'r2': 1.0}
        rf_metrics = {'mae': 0.0, 'r2': 1.0}

        comparison = compare_models(null_metrics, rf_metrics)

        # Should handle division by zero gracefully
        assert comparison['mae_improvement_percent'] == 0.0


class TestRunNullBaselineAnalysis:
    """Tests for run_null_baseline_analysis function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.data_path = os.path.join(self.test_dir, 'test_data.csv')
        self.model_path = os.path.join(self.test_dir, 'test_model.pkl')
        self.output_path = os.path.join(self.test_dir, 'results.json')

        # Create test data
        with open(self.data_path, 'w') as f:
            f.write('feature1,feature2,target\n')
            f.write('1.0,2.0,10.0\n')
            f.write('2.0,3.0,20.0\n')
            f.write('3.0,4.0,30.0\n')
            f.write('4.0,5.0,40.0\n')
            f.write('5.0,6.0,50.0\n')

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_basic_analysis(self):
        """Test basic null baseline analysis without RF model."""
        results = run_null_baseline_analysis(
            data_path=self.data_path,
            rf_model_path=None,
            output_path=self.output_path
        )

        assert 'global_mean' in results
        assert 'null_model_metrics' in results
        assert 'sample_count' in results
        assert results['sample_count'] == 5
        assert abs(results['global_mean'] - 30.0) < 1e-6

        # Verify output file was created
        assert os.path.exists(self.output_path)
        with open(self.output_path, 'r') as f:
            saved_results = json.load(f)
        assert saved_results == results

    def test_analysis_with_mock_rf_model(self):
        """Test analysis with a mock RF model."""
        # Create a mock RF model that returns perfect predictions
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([10.0, 20.0, 30.0, 40.0, 50.0])

        # Save mock model
        import pickle
        with open(self.model_path, 'wb') as f:
            pickle.dump(mock_model, f)

        results = run_null_baseline_analysis(
            data_path=self.data_path,
            rf_model_path=self.model_path,
            output_path=self.output_path
        )

        assert 'rf_model_metrics' in results
        assert 'comparison' in results
        assert results['comparison']['rf_better'] is True

    def test_nonexistent_data_file(self):
        """Test analysis with non-existent data file."""
        with pytest.raises(FileNotFoundError):
            run_null_baseline_analysis(
                data_path='nonexistent.csv',
                rf_model_path=None,
                output_path=self.output_path
            )

    def test_output_directory_creation(self):
        """Test that output directory is created if it doesn't exist."""
        nested_output_path = os.path.join(self.test_dir, 'nested', 'dir', 'results.json')
        results = run_null_baseline_analysis(
            data_path=self.data_path,
            rf_model_path=None,
            output_path=nested_output_path
        )

        assert os.path.exists(nested_output_path)

    def test_null_model_mae_is_positive(self):
        """Test that null model MAE is positive for non-constant target."""
        # Create data with varying targets
        with open(self.data_path, 'w') as f:
            f.write('f1,f2,target\n')
            f.write('1,1,10\n')
            f.write('2,2,20\n')
            f.write('3,3,30\n')

        results = run_null_baseline_analysis(
            data_path=self.data_path,
            rf_model_path=None,
            output_path=self.output_path
        )

        assert results['null_model_metrics']['mae'] > 0

    def test_r2_for_null_model_is_zero_or_negative(self):
        """Test that R² for null model (global mean) is <= 0 for varying targets."""
        results = run_null_baseline_analysis(
            data_path=self.data_path,
            rf_model_path=None,
            output_path=self.output_path
        )

        # For a dataset with varying targets, the global mean predictor
        # should have R² ≈ 0 (or slightly negative due to numerical precision)
        assert results['null_model_metrics']['r2'] <= 1e-6