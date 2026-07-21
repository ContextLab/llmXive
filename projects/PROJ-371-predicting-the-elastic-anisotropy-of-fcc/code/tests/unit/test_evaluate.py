"""
Unit tests for the evaluation module.

This module contains tests to verify that R², MAE, and RMSE calculations
match scikit-learn standards.
"""

import pytest
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error, root_mean_squared_error
from pathlib import Path
import sys

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.evaluate import calculate_metrics


class TestMetricsCalculationMatchesScikitLearn:
    """Test that our metric calculations match scikit-learn exactly."""

    def test_r2_matches_scikit_learn(self):
        """Verify R² calculation matches sklearn.metrics.r2_score."""
        y_true = np.array([3.0, -0.5, 2.0, 7.0])
        y_pred = np.array([2.5, 0.0, 2.0, 8.0])

        # Calculate using our function
        our_r2 = calculate_metrics(y_true, y_pred, r2=True, mae=False, rmse=False)["r2"]

        # Calculate using sklearn
        sklearn_r2 = r2_score(y_true, y_pred)

        assert np.isclose(our_r2, sklearn_r2, rtol=1e-10), \
            f"R² mismatch: ours={our_r2}, sklearn={sklearn_r2}"

    def test_mae_matches_scikit_learn(self):
        """Verify MAE calculation matches sklearn.metrics.mean_absolute_error."""
        y_true = np.array([3.0, -0.5, 2.0, 7.0, 1.0])
        y_pred = np.array([2.5, 0.0, 2.0, 8.0, 1.5])

        # Calculate using our function
        our_mae = calculate_metrics(y_true, y_pred, r2=False, mae=True, rmse=False)["mae"]

        # Calculate using sklearn
        sklearn_mae = mean_absolute_error(y_true, y_pred)

        assert np.isclose(our_mae, sklearn_mae, rtol=1e-10), \
            f"MAE mismatch: ours={our_mae}, sklearn={sklearn_mae}"

    def test_rmse_matches_scikit_learn(self):
        """Verify RMSE calculation matches sklearn.metrics.root_mean_squared_error."""
        y_true = np.array([3.0, -0.5, 2.0, 7.0, 1.0])
        y_pred = np.array([2.5, 0.0, 2.0, 8.0, 1.5])

        # Calculate using our function
        our_rmse = calculate_metrics(y_true, y_pred, r2=False, mae=False, rmse=True)["rmse"]

        # Calculate using sklearn
        sklearn_rmse = root_mean_squared_error(y_true, y_pred)

        assert np.isclose(our_rmse, sklearn_rmse, rtol=1e-10), \
            f"RMSE mismatch: ours={our_rmse}, sklearn={sklearn_rmse}"

    def test_all_metrics_together(self):
        """Verify all metrics calculated together match individual sklearn calls."""
        y_true = np.array([3.0, -0.5, 2.0, 7.0, 1.0, -2.0])
        y_pred = np.array([2.5, 0.0, 2.0, 8.0, 1.5, -1.5])

        # Calculate using our function (all metrics)
        our_metrics = calculate_metrics(y_true, y_pred, r2=True, mae=True, rmse=True)

        # Calculate using sklearn
        sklearn_r2 = r2_score(y_true, y_pred)
        sklearn_mae = mean_absolute_error(y_true, y_pred)
        sklearn_rmse = root_mean_squared_error(y_true, y_pred)

        assert np.isclose(our_metrics["r2"], sklearn_r2, rtol=1e-10), \
            f"R² mismatch in combined: ours={our_metrics['r2']}, sklearn={sklearn_r2}"
        assert np.isclose(our_metrics["mae"], sklearn_mae, rtol=1e-10), \
            f"MAE mismatch in combined: ours={our_metrics['mae']}, sklearn={sklearn_mae}"
        assert np.isclose(our_metrics["rmse"], sklearn_rmse, rtol=1e-10), \
            f"RMSE mismatch in combined: ours={our_metrics['rmse']}, sklearn={sklearn_rmse}"

    def test_perfect_prediction(self):
        """Test metrics when predictions are perfect."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0])

        metrics = calculate_metrics(y_true, y_pred, r2=True, mae=True, rmse=True)

        assert np.isclose(metrics["r2"], 1.0, rtol=1e-10), "Perfect prediction should have R² = 1.0"
        assert np.isclose(metrics["mae"], 0.0, rtol=1e-10), "Perfect prediction should have MAE = 0.0"
        assert np.isclose(metrics["rmse"], 0.0, rtol=1e-10), "Perfect prediction should have RMSE = 0.0"

    def test_constant_prediction(self):
        """Test metrics when predictions are constant (worst case for R²)."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0])
        y_pred = np.array([2.5, 2.5, 2.5, 2.5])  # Mean of y_true

        metrics = calculate_metrics(y_true, y_pred, r2=True, mae=True, rmse=True)

        # R² should be 0.0 for constant prediction equal to mean
        assert np.isclose(metrics["r2"], 0.0, rtol=1e-10), \
            f"Constant prediction (mean) should have R² = 0.0, got {metrics['r2']}"

    def test_negative_r2(self):
        """Test that R² can be negative for very poor predictions."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0])
        y_pred = np.array([4.0, 3.0, 2.0, 1.0])  # Inverted

        metrics = calculate_metrics(y_true, y_pred, r2=True, mae=True, rmse=True)

        # R² should be negative
        assert metrics["r2"] < 0.0, \
            f"Very poor prediction should have negative R², got {metrics['r2']}"

    def test_single_element(self):
        """Test with single element arrays."""
        y_true = np.array([5.0])
        y_pred = np.array([5.0])

        metrics = calculate_metrics(y_true, y_pred, r2=True, mae=True, rmse=True)

        # Single element: R² is undefined (returns NaN in sklearn), MAE and RMSE should be 0
        assert np.isnan(metrics["r2"]), "Single element should result in NaN R²"
        assert np.isclose(metrics["mae"], 0.0, rtol=1e-10), "Single element identical should have MAE = 0.0"
        assert np.isclose(metrics["rmse"], 0.0, rtol=1e-10), "Single element identical should have RMSE = 0.0"

    def test_large_scale_values(self):
        """Test with large scale values to ensure numerical stability."""
        y_true = np.array([1e6, 2e6, 3e6, 4e6])
        y_pred = np.array([1.1e6, 1.9e6, 3.1e6, 3.9e6])

        our_metrics = calculate_metrics(y_true, y_pred, r2=True, mae=True, rmse=True)
        sklearn_r2 = r2_score(y_true, y_pred)
        sklearn_mae = mean_absolute_error(y_true, y_pred)
        sklearn_rmse = root_mean_squared_error(y_true, y_pred)

        assert np.isclose(our_metrics["r2"], sklearn_r2, rtol=1e-6), \
            f"Large scale R² mismatch: ours={our_metrics['r2']}, sklearn={sklearn_r2}"
        assert np.isclose(our_metrics["mae"], sklearn_mae, rtol=1e-6), \
            f"Large scale MAE mismatch: ours={our_metrics['mae']}, sklearn={sklearn_mae}"
        assert np.isclose(our_metrics["rmse"], sklearn_rmse, rtol=1e-6), \
            f"Large scale RMSE mismatch: ours={our_metrics['rmse']}, sklearn={sklearn_rmse}"