"""
Tests for edge cases in simulation.
"""
import pytest
import numpy as np
from simulation.state_tracker import compute_kl_divergence_simple

def test_identical_distributions():
    """KL divergence should be 0 for identical distributions."""
    p = np.array([0.2, 0.3, 0.5])
    q = np.array([0.2, 0.3, 0.5])
    kl = compute_kl_divergence_simple(p, q)
    assert kl == 0.0
