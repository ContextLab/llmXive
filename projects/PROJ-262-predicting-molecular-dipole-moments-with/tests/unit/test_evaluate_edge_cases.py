"""
Unit tests for edge cases in the training evaluation utilities.

These tests verify that the core metric functions handle simple,
well‑behaved inputs correctly and return expected zero error values.
They also ensure that the ``evaluate`` helper returns a dictionary with
the required keys.
"""

import numpy as np
import pytest

# Import the public functions as defined in the project API surface
from training.evaluate import mae, rmse, evaluate


def test_mae_zero_error():
    """MAE should be zero when predictions exactly match true values."""
    y_true = np.array([0.0, 1.5, -2.3, 4.0])
    y_pred = np.array([0.0, 1.5, -2.3, 4.0])
    assert mae(y_true, y_pred) == 0.0


def test_rmse_zero_error():
    """RMSE should be zero when predictions exactly match true values."""
    y_true = np.array([0.0, 1.5, -2.3, 4.0])
    y_pred = np.array([0.0, 1.5, -2.3, 4.0])
    assert rmse(y_true, y_pred) == 0.0


def test_evaluate_returns_correct_keys_and_zero_error():
    """``evaluate`` should return a dict containing MAE and RMSE keys with zero values."""
    y_true = np.array([1.2, -0.7, 3.3])
    y_pred = np.array([1.2, -0.7, 3.3])
    metrics = evaluate(y_true, y_pred)

    # The function should return a dictionary
    assert isinstance(metrics, dict), "evaluate must return a dict"

    # Required metric keys must be present
    expected_keys = {"mae", "rmse"}
    assert expected_keys.issubset(metrics.keys()), f"Missing keys: {expected_keys - metrics.keys()}"

    # With perfect predictions both metrics should be exactly zero
    assert metrics["mae"] == 0.0
    assert metrics["rmse"] == 0.0


def test_mae_with_numpy_float_inputs():
    """MAE should correctly handle scalar numpy float inputs."""
    y_true = np.array([5.0])
    y_pred = np.array([5.0])
    assert mae(y_true, y_pred) == 0.0


def test_rmse_with_numpy_float_inputs():
    """RMSE should correctly handle scalar numpy float inputs."""
    y_true = np.array([5.0])
    y_pred = np.array([5.0])
    assert rmse(y_true, y_pred) == 0.0


# Additional sanity check: ensure that passing mismatched array lengths raises an error.
def test_mae_mismatched_lengths_raises():
    """MAE should raise a ValueError when input arrays have different lengths."""
    y_true = np.array([1.0, 2.0])
    y_pred = np.array([1.0])
    with pytest.raises(ValueError):
        mae(y_true, y_pred)


def test_rmse_mismatched_lengths_raises():
    """RMSE should raise a ValueError when input arrays have different lengths."""
    y_true = np.array([1.0, 2.0])
    y_pred = np.array([1.0])
    with pytest.raises(ValueError):
        rmse(y_true, y_pred)