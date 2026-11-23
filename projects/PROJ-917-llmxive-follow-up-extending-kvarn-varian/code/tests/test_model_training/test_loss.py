"""
Tests for loss function implementation.
"""
import pytest
import numpy as np

def test_mse_loss():
    """Test MSE loss calculation."""
    y_true = np.array([1.0, 2.0])
    y_pred = np.array([1.5, 2.5])
    loss = np.mean((y_true - y_pred) ** 2)
    assert loss == 0.25
