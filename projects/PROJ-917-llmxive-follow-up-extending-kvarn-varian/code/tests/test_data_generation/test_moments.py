"""
Tests for moment extraction logic.
"""
import pytest
import numpy as np

def test_moment_calculation():
    """Test basic moment calculation."""
    data = np.array([1, 2, 3, 4, 5])
    mean = np.mean(data)
    var = np.var(data)
    assert mean == 3.0
    assert var == 2.0
