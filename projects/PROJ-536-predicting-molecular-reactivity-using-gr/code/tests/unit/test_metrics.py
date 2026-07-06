"""
Unit tests for metric calculators in src/utils/metrics.py.
"""

import pytest
import numpy as np

from src.utils.metrics import calculate_mae, calculate_rmse, calculate_r2, calculate_all_metrics


def test_calculate_mae_basic():
    """Test MAE calculation with simple known values."""
    y_true = [3.0, -0.5, 2.0, 7.0]
    y_pred = [2.5, 0.0, 2.0, 8.0]
    # Errors: 0.5, 0.5, 0.0, 1.0 -> Mean: 2.0 / 4 = 0.5
    expected = 0.5
    assert calculate_mae(y_true, y_pred) == pytest.approx(expected)


def test_calculate_mae_numpy():
    """Test MAE calculation with numpy arrays."""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.0, 2.0, 3.0])
    assert calculate_mae(y_true, y_pred) == pytest.approx(0.0)


def test_calculate_rmse_basic():
    """Test RMSE calculation with simple known values."""
    y_true = [3.0, -0.5, 2.0, 7.0]
    y_pred = [2.5, 0.0, 2.0, 8.0]
    # Squared errors: 0.25, 0.25, 0.0, 1.0 -> Mean: 1.5 / 4 = 0.375
    # RMSE: sqrt(0.375)
    expected = np.sqrt(0.375)
    assert calculate_rmse(y_true, y_pred) == pytest.approx(expected)


def test_calculate_r2_perfect():
    """Test R² for perfect predictions."""
    y_true = [1.0, 2.0, 3.0, 4.0]
    y_pred = [1.0, 2.0, 3.0, 4.0]
    assert calculate_r2(y_true, y_pred) == pytest.approx(1.0)


def test_calculate_r2_worse_than_mean():
    """Test R² for predictions worse than the mean."""
    # Mean of y_true is 2.0.
    # Predictions are far off: [10, 10, 10, 10]
    y_true = [1.0, 2.0, 3.0, 4.0]
    y_pred = [10.0, 10.0, 10.0, 10.0]
    # ss_res = 9 + 64 + 49 + 36 = 158
    # ss_tot = 1 + 0 + 1 + 4 = 6
    # R2 = 1 - (158/6) = 1 - 26.33 = -25.33
    result = calculate_r2(y_true, y_pred)
    assert result < 0.0


def test_calculate_all_metrics():
    """Test the aggregate metrics function."""
    y_true = [3.0, -0.5, 2.0, 7.0]
    y_pred = [2.5, 0.0, 2.0, 8.0]

    metrics = calculate_all_metrics(y_true, y_pred)

    assert "mae" in metrics
    assert "rmse" in metrics
    assert "r2" in metrics
    assert metrics["mae"] == pytest.approx(0.5)
    assert metrics["rmse"] == pytest.approx(np.sqrt(0.375))


def test_mae_empty_input():
    """Test that empty input raises ValueError."""
    with pytest.raises(ValueError):
        calculate_mae([], [])


def test_mae_mismatched_lengths():
    """Test that mismatched lengths raise ValueError."""
    with pytest.raises(ValueError):
        calculate_mae([1.0, 2.0], [1.0])


def test_r2_zero_variance():
    """Test that zero variance in y_true raises ValueError."""
    y_true = [2.0, 2.0, 2.0]
    y_pred = [1.0, 2.0, 3.0]
    with pytest.raises(ValueError):
        calculate_r2(y_true, y_pred)