"""
Tests for KL-divergence accumulator.
"""
import pytest
from simulation.state_tracker import StateTracker

def test_kl_accumulation():
    """Test that KL divergence accumulates correctly."""
    tracker = StateTracker()
    kl_values = [0.1, 0.2, 0.3]
    for i, kl in enumerate(kl_values):
        tracker.update(step=i+1, error=0.0, kl_div=kl)
    assert tracker.state.total_kl_divergence == sum(kl_values)
