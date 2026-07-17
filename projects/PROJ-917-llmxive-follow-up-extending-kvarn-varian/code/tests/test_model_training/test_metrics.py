"""
Tests for training metrics calculation.
"""
import pytest
import numpy as np

def test_mse_calculation():
    """Test Mean Squared Error calculation."""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.1, 2.1, 2.9])
    mse = np.mean((y_true - y_pred) ** 2)
    expected = np.mean([0.01, 0.01, 0.01])
    assert abs(mse - expected) < 1e-6
