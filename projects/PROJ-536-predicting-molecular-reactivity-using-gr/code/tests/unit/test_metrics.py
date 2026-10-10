"""Unit tests for src.utils.metrics."""
import pytest
import numpy as np

from src.utils.metrics import (
    calculate_mae,
    calculate_rmse,
    calculate_r2,
    calculate_all_metrics,
)


def test_mae_perfect_prediction():
    y = [1.0, 2.0, 3.0]
    assert calculate_mae(y, y) == 0.0


def test_mae_known_value():
    assert calculate_mae([1.0, 2.0, 3.0], [2.0, 2.0, 5.0]) == pytest.approx(1.0)


def test_rmse_known_value():
    # errors: 1, 0, 2 -> sqrt((1+0+4)/3)
    assert calculate_rmse([1.0, 2.0, 3.0], [2.0, 2.0, 5.0]) == pytest.approx(
        np.sqrt(5.0 / 3.0)
    )


def test_r2_perfect():
    y = [1.0, 2.0, 3.0]
    assert calculate_r2(y, y) == pytest.approx(1.0)


def test_r2_mean_prediction_is_zero():
    y = [1.0, 2.0, 3.0]
    assert calculate_r2(y, [2.0, 2.0, 2.0]) == pytest.approx(0.0)


def test_r2_zero_variance_true():
    with pytest.raises(ValueError):
        calculate_r2([5.0, 5.0], [1.0, 2.0])


def test_r2_zero_variance_perfect():
    assert calculate_r2([5.0, 5.0], [5.0, 5.0]) == 1.0


def test_length_mismatch_raises():
    with pytest.raises(ValueError):
        calculate_mae([1.0, 2.0], [1.0])


def test_empty_inputs_raise():
    with pytest.raises(ValueError):
        calculate_rmse([], [])


def test_nan_input_raises():
    with pytest.raises(ValueError):
        calculate_mae([1.0, float("nan")], [1.0, 2.0])


def test_all_metrics_keys_and_values():
    y_true = np.array([10.0, 20.0, 30.0, 40.0])
    y_pred = y_true + 1.0
    result = calculate_all_metrics(y_true, y_pred)
    assert set(result.keys()) == {"mae", "rmse", "r2"}
    assert result["mae"] == pytest.approx(1.0)
    assert result["rmse"] == pytest.approx(1.0)
    assert result["r2"] == pytest.approx(
        1.0 - (4.0 / np.sum((y_true - y_true.mean()) ** 2))
    )
    assert all(np.isfinite(v) for v in result.values())