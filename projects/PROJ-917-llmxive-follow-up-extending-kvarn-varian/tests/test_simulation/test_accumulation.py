"""
Unit tests for error accumulation in simulation.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.simulation.state_tracker import StateTracker, compute_kl_divergence_simple


def test_cumulative_error_accumulation():
    """Test that errors accumulate correctly over multiple steps."""
    tracker = StateTracker()
    
    # Simulate 5 steps with constant KL divergence
    kl_step = 0.1
    steps = 5
    
    for _ in range(steps):
        p = np.array([0.6, 0.4])
        q = np.array([0.4, 0.6])
        kl = compute_kl_divergence_simple(p, q)
        tracker.update(kl)
    
    # Total accumulated KL should be approximately steps * kl_step
    expected_total = steps * kl_step
    assert np.isclose(tracker.state.accumulated_kl, expected_total, rtol=0.1)
    assert tracker.state.step_index == steps
