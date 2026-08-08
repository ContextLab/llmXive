"""
Unit tests for the MAE and RMSE metric implementations.

The tests verify correctness on simple, deterministic inputs and edge cases
including empty inputs and NaN values.
"""

import numpy as np
import pytest

# Import the metric functions from the project package.
from code.training.evaluate import mae, rmse


@pytest.mark.parametrize(
    "y_true, y_pred, expected_mae, expected_rmse",
    [
        # Perfect prediction → both errors are zero.
        (np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0, 3.0]), 0.0, 0.0),
        # Simple offset errors.
        (
            np.array([1.0, 2.0, 3.0]),
            np.array([2.0, 2.0, 4.0]),
            (1.0 + 0.0 + 1.0) / 3.0,  # MAE = 2/3
            np.sqrt((1.0 ** 2 + 0.0 ** 2 + 1.0 ** 2) / 3.0),  # RMSE = sqrt(2/3)
        ),
        # Mixed positive and negative errors.
        (
            np.array([-1.0, 0.0, 1.0]),
            np.array([0.0, -1.0, 2.0]),
            (1.0 + 1.0 + 1.0) / 3.0,  # MAE = 1.0
            np.sqrt((1.0 ** 2 + 1.0 ** 2 + 1.0 ** 2) / 3.0),  # RMSE = sqrt(1)
        ),
    ],
)
def test_mae_rmse(y_true, y_pred, expected_mae, expected_rmse):
    """Validate that mae and rmse return the expected numerical results."""
    computed_mae = mae(y_true, y_pred)
    computed_rmse = rmse(y_true, y_pred)

    # Use a tolerant comparison for floating‑point results.
    np.testing.assert_allclose(computed_mae, expected_mae, rtol=1e-7, atol=1e-9)
    np.testing.assert_allclose(computed_rmse, expected_rmse, rtol=1e-7, atol=1e-9)


def test_metrics_handles_empty_input():
    """Assert that empty input raises a ValueError."""
    empty_true = np.array([])
    empty_pred = np.array([])

    with pytest.raises(ValueError, match="Input arrays cannot be empty"):
        mae(empty_true, empty_pred)

    with pytest.raises(ValueError, match="Input arrays cannot be empty"):
        rmse(empty_true, empty_pred)


def test_metrics_handles_nan_values():
    """Assert that inputs containing NaN raise a ValueError."""
    y_true_nan = np.array([1.0, np.nan, 3.0])
    y_pred_valid = np.array([1.0, 2.0, 3.0])

    y_true_valid = np.array([1.0, 2.0, 3.0])
    y_pred_nan = np.array([1.0, np.nan, 3.0])

    # Test NaN in true values
    with pytest.raises(ValueError, match="Input arrays contain NaN"):
        mae(y_true_nan, y_pred_valid)

    with pytest.raises(ValueError, match="Input arrays contain NaN"):
        rmse(y_true_nan, y_pred_valid)

    # Test NaN in predicted values
    with pytest.raises(ValueError, match="Input arrays contain NaN"):
        mae(y_true_valid, y_pred_nan)

    with pytest.raises(ValueError, match="Input arrays contain NaN"):
        rmse(y_true_valid, y_pred_nan)