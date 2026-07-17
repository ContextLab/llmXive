"""
Tests for KL-divergence calculation logic.
"""
import pytest
import numpy as np
from simulation.state_tracker import compute_kl_divergence_simple

def test_kl_divergence_symmetry():
    """KL divergence is not symmetric, but we test valid inputs."""
    p = np.array([0.5, 0.5])
    q = np.array([0.5, 0.5])
    kl = compute_kl_divergence_simple(p, q)
    assert kl == 0.0

def test_kl_divergence_positive():
    """KL divergence should be non-negative."""
    p = np.array([0.9, 0.1])
    q = np.array([0.1, 0.9])
    kl = compute_kl_divergence_simple(p, q)
    assert kl >= 0
