"""
Unit tests for error metric calculation (MAE, RMSE, MSE) in code/utils.py.

Tests the calculate_metrics function which computes Mean Absolute Error,
Root Mean Squared Error, and Mean Squared Error.
"""
import pytest
import numpy as np
from code.utils import calculate_metrics


class TestCalculateMetrics:
    """Tests for the calculate_metrics function."""

    def test_basic_metrics(self):
        """Test basic MAE, RMSE, and MSE calculation with known values."""
        # Predictions: [1, 2, 3], Actual: [1, 2, 3] -> perfect match
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])

        mae, rmse, mse = calculate_metrics(y_true, y_pred)

        assert mae == pytest.approx(0.0, rel=1e-9)
        assert rmse == pytest.approx(0.0, rel=1e-9)
        assert mse == pytest.approx(0.0, rel=1e-9)

    def test_non_zero_metrics(self):
        """Test metrics with non-zero errors."""
        # Predictions: [1, 2, 3], Actual: [2, 3, 4] -> errors: [-1, -1, -1]
        y_true = np.array([2.0, 3.0, 4.0])
        y_pred = np.array([1.0, 2.0, 3.0])

        # Errors: [-1, -1, -1]
        # MAE = mean(|-1|, |-1|, |-1|) = 1.0
        # MSE = mean((-1)^2, (-1)^2, (-1)^2) = 1.0
        # RMSE = sqrt(1.0) = 1.0
        mae, rmse, mse = calculate_metrics(y_true, y_pred)

        assert mae == pytest.approx(1.0, rel=1e-9)
        assert rmse == pytest.approx(1.0, rel=1e-9)
        assert mse == pytest.approx(1.0, rel=1e-9)

    def test_mixed_errors(self):
        """Test metrics with mixed positive and negative errors."""
        # Predictions: [1, 2, 3], Actual: [1, 4, 2] -> errors: [0, -2, 1]
        y_true = np.array([1.0, 4.0, 2.0])
        y_pred = np.array([1.0, 2.0, 3.0])

        # Absolute errors: [0, 2, 1] -> MAE = 3/3 = 1.0
        # Squared errors: [0, 4, 1] -> MSE = 5/3 ≈ 1.6667
        # RMSE = sqrt(5/3) ≈ 1.2910
        mae, rmse, mse = calculate_metrics(y_true, y_pred)

        assert mae == pytest.approx(1.0, rel=1e-9)
        assert mse == pytest.approx(5.0/3.0, rel=1e-9)
        assert rmse == pytest.approx(np.sqrt(5.0/3.0), rel=1e-9)

    def test_single_element(self):
        """Test metrics with a single data point."""
        y_true = np.array([5.0])
        y_pred = np.array([3.0])

        # Error: 2.0
        # MAE = 2.0, MSE = 4.0, RMSE = 2.0
        mae, rmse, mse = calculate_metrics(y_true, y_pred)

        assert mae == pytest.approx(2.0, rel=1e-9)
        assert mse == pytest.approx(4.0, rel=1e-9)
        assert rmse == pytest.approx(2.0, rel=1e-9)

    def test_large_values(self):
        """Test metrics with large magnitude values."""
        y_true = np.array([1000.0, 2000.0, 3000.0])
        y_pred = np.array([1001.0, 1999.0, 3002.0])

        # Errors: [-1, 1, -2]
        # Absolute: [1, 1, 2] -> MAE = 4/3 ≈ 1.3333
        # Squared: [1, 1, 4] -> MSE = 6/3 = 2.0
        # RMSE = sqrt(2.0) ≈ 1.4142
        mae, rmse, mse = calculate_metrics(y_true, y_pred)

        assert mae == pytest.approx(4.0/3.0, rel=1e-9)
        assert mse == pytest.approx(2.0, rel=1e-9)
        assert rmse == pytest.approx(np.sqrt(2.0), rel=1e-9)

    def test_negative_values(self):
        """Test metrics with negative energy values."""
        # Typical DFT energies are negative
        y_true = np.array([-100.0, -200.0, -300.0])
        y_pred = np.array([-101.0, -199.0, -302.0])

        # Errors: [1, -1, 2]
        # Absolute: [1, 1, 2] -> MAE = 4/3 ≈ 1.3333
        # Squared: [1, 1, 4] -> MSE = 6/3 = 2.0
        # RMSE = sqrt(2.0) ≈ 1.4142
        mae, rmse, mse = calculate_metrics(y_true, y_pred)

        assert mae == pytest.approx(4.0/3.0, rel=1e-9)
        assert mse == pytest.approx(2.0, rel=1e-9)
        assert rmse == pytest.approx(np.sqrt(2.0), rel=1e-9)

    def test_zero_error(self):
        """Test that zero error is correctly identified."""
        y_true = np.array([0.0, 0.0, 0.0])
        y_pred = np.array([0.0, 0.0, 0.0])

        mae, rmse, mse = calculate_metrics(y_true, y_pred)

        assert mae == pytest.approx(0.0, rel=1e-9)
        assert rmse == pytest.approx(0.0, rel=1e-9)
        assert mse == pytest.approx(0.0, rel=1e-9)

    def test_float_precision(self):
        """Test that metrics handle floating point precision correctly."""
        y_true = np.array([0.1 + 0.2, 0.3, 0.6])
        y_pred = np.array([0.3, 0.3, 0.6])

        # First element: 0.1 + 0.2 ≈ 0.30000000000000004
        # Error ≈ 0.00000000000000004
        # All errors are essentially zero
        mae, rmse, mse = calculate_metrics(y_true, y_pred)

        # Should be very close to zero
        assert mae < 1e-15
        assert rmse < 1e-15
        assert mse < 1e-15