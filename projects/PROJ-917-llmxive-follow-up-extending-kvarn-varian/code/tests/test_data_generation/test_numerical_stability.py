"""
Unit tests for numerical stability utilities in data_generation.
Tests epsilon handling, drift models, and safe math operations.
"""
import pytest
import numpy as np
from data_generation.utils import (
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
    """Test that values below epsilon are replaced."""
    eps = 1e-8
    arr = np.array([0.0, 1e-9, 1e-7, -1e-9, -1e-7])
    result = apply_epsilon_floor(arr, eps)
    assert result[0] == eps
    assert result[1] == eps
    assert result[2] == 1e-7
    assert result[3] == eps
    assert result[4] == -1e-7  # Negative values not floored if logic is abs-based, or handled separately

def test_safe_log():
    """Test log handling for non-positive values."""
    arr = np.array([1.0, 0.0, -1.0, 1e-10])
    result = safe_log(arr)
    assert result[0] == 0.0
    assert result[1] == 0.0  # Or -inf depending on impl, but safe_log usually clamps
    assert result[2] == 0.0
    assert np.isfinite(result[3])

def test_safe_divide():
    """Test division by zero handling."""
    numer = np.array([1.0, 2.0, 0.0])
    denom = np.array([1.0, 0.0, 0.0])
    result = safe_divide(numer, denom)
    assert result[0] == 1.0
    assert np.isnan(result[1]) or result[1] == 0.0
    assert result[2] == 0.0

def test_check_numerical_stability():
    """Test detection of NaN and Inf."""
    arr_good = np.array([1.0, 2.0, 3.0])
    arr_bad = np.array([1.0, np.nan, 3.0])
    assert check_numerical_stability(arr_good) is True
    assert check_numerical_stability(arr_bad) is False

def test_drift_models():
    """Test that drift models return valid arrays."""
    steps = np.array([0.0, 1.0, 2.0, 3.0])
    assert linear_drift(steps, 0.1).shape == steps.shape
    assert exponential_drift(steps, 0.1).shape == steps.shape
    assert sinusoidal_drift(steps, 0.1, 0.1).shape == steps.shape

def test_get_drift_model():
    """Test factory function for drift models."""
    func = get_drift_model("linear")
    assert callable(func)
    with pytest.raises(ValueError):
        get_drift_model("invalid_model")
