"""
Unit tests for numerical stability utilities in code/data_generation/utils.py.
"""
import pytest
import numpy as np
from code.data_generation.utils import (
    apply_epsilon_floor,
    safe_log,
    safe_divide,
    check_numerical_stability,
    linear_drift,
    exponential_drift,
    sinusoidal_drift,
    get_drift_model
)


def test_apply_epsilon_floor():
    """Test that values below epsilon are floored to epsilon."""
    epsilon = 1e-6
    assert apply_epsilon_floor(0.0, epsilon) == epsilon
    assert apply_epsilon_floor(1e-9, epsilon) == epsilon
    assert apply_epsilon_floor(1e-5, epsilon) == 1e-5
    assert apply_epsilon_floor(-1.0, epsilon) == epsilon


def test_safe_log():
    """Test safe log handling for near-zero and negative values."""
    epsilon = 1e-6
    # Positive value
    assert np.isclose(safe_log(1.0, epsilon), 0.0)
    # Near zero should be floored
    result = safe_log(1e-9, epsilon)
    assert result == safe_log(epsilon, epsilon)
    # Negative should be floored to epsilon before log
    result = safe_log(-1.0, epsilon)
    assert result == safe_log(epsilon, epsilon)


def test_safe_divide():
    """Test safe division handling for near-zero denominators."""
    epsilon = 1e-6
    assert np.isclose(safe_divide(1.0, 0.0, epsilon), 1.0 / epsilon)
    assert np.isclose(safe_divide(1.0, 1e-9, epsilon), 1.0 / epsilon)
    assert np.isclose(safe_divide(1.0, 2.0, epsilon), 0.5)


def test_check_numerical_stability():
    """Test detection of NaN and Inf values."""
    assert check_numerical_stability(1.0) is True
    assert check_numerical_stability(np.nan) is False
    assert check_numerical_stability(np.inf) is False
    assert check_numerical_stability(-np.inf) is False


def test_drift_models():
    """Test that drift models return expected shapes and types."""
    steps = 10
    # Linear drift
    result = linear_drift(steps, start=0.0, slope=0.1)
    assert len(result) == steps
    assert result[0] == 0.0
    assert result[9] == 0.9

    # Exponential drift
    result = exponential_drift(steps, start=1.0, rate=0.1)
    assert len(result) == steps
    assert result[0] == 1.0

    # Sinusoidal drift
    result = sinusoidal_drift(steps, amplitude=1.0, frequency=0.1, phase=0.0)
    assert len(result) == steps


def test_get_drift_model():
    """Test factory function for drift models."""
    model = get_drift_model("linear")
    assert callable(model)
    model = get_drift_model("exponential")
    assert callable(model)
    model = get_drift_model("sinusoidal")
    assert callable(model)
    with pytest.raises(ValueError):
        get_drift_model("invalid_model")
