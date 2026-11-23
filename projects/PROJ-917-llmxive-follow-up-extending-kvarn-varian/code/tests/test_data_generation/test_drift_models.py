"""
Specific tests for drift model implementations.
"""
import pytest
import numpy as np
from data_generation.utils import linear_drift, exponential_drift, sinusoidal_drift

def test_linear_drift_monotonicity():
    """Linear drift should be monotonic for positive slope."""
    steps = np.linspace(0, 10, 100)
    drift = linear_drift(steps, 0.5)
    assert np.all(np.diff(drift) > 0)

def test_exponential_drift_growth():
    """Exponential drift should grow faster than linear."""
    steps = np.linspace(0, 5, 100)
    linear = linear_drift(steps, 1.0)
    exp = exponential_drift(steps, 1.0)
    # At end, exp should be larger
    assert exp[-1] > linear[-1]
