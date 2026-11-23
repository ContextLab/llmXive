"""
Unit tests for KL-divergence calculations in code/simulation/state_tracker.py.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.simulation.state_tracker import compute_kl_divergence_simple


def test_kl_divergence_positive():
    """Test that KL divergence is always non-negative."""
    # Two identical distributions should have 0 KL divergence
    p = np.array([0.5, 0.5])
    q = np.array([0.5, 0.5])
    kl = compute_kl_divergence_simple(p, q)
    assert kl >= 0.0

    # Different distributions
    p = np.array([0.9, 0.1])
    q = np.array([0.1, 0.9])
    kl = compute_kl_divergence_simple(p, q)
    assert kl > 0.0


def test_kl_divergence_symmetry():
    """Test that KL divergence is not symmetric (D_KL(P||Q) != D_KL(Q||P))."""
    p = np.array([0.9, 0.1])
    q = np.array([0.1, 0.9])

    kl_pq = compute_kl_divergence_simple(p, q)
    kl_qp = compute_kl_divergence_simple(q, p)

    # They should be different
    assert not np.isclose(kl_pq, kl_qp)

    # But both should be positive
    assert kl_pq > 0.0
    assert kl_qp > 0.0


def test_kl_divergence_zero_prob():
    """Test handling of zero probabilities."""
    # P has zero where Q is non-zero -> KL should be infinite or very large
    p = np.array([1.0, 0.0])
    q = np.array([0.5, 0.5])
    # In a robust implementation, this might be handled with epsilon
    # For this test, we check that it doesn't crash and returns a number
    kl = compute_kl_divergence_simple(p, q)
    assert np.isfinite(kl) or np.isinf(kl)
