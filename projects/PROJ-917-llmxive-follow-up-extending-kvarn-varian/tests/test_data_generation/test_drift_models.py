"""
Unit tests for drift model functions in code/data_generation/utils.py.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data_generation.utils import (
    linear_drift,
    exponential_drift,
    sinusoidal_drift
)


def test_linear_drift_monotonicity():
    """Test that linear drift is monotonic for positive slope."""
    steps = 20
    result = linear_drift(steps, start=0.0, slope=0.1)
    for i in range(1, len(result)):
        assert result[i] >= result[i-1], "Linear drift with positive slope should be non-decreasing"


def test_exponential_drift_growth():
    """Test that exponential drift grows over time."""
    steps = 20
    result = exponential_drift(steps, start=1.0, rate=0.1)
    for i in range(1, len(result)):
        assert result[i] > result[i-1], "Exponential drift should be strictly increasing"


def test_sinusoidal_drift_bounds():
    """Test that sinusoidal drift stays within expected bounds."""
    steps = 100
    amplitude = 1.0
    result = sinusoidal_drift(steps, amplitude=amplitude, frequency=0.1, phase=0.0)
    assert all(-amplitude <= x <= amplitude for x in result)
