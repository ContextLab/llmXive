"""
Tests for cumulative error accumulation logic.
"""
import pytest
from simulation.state_tracker import StateTracker

def test_cumulative_error_accumulation():
    """Test that errors accumulate correctly."""
    tracker = StateTracker()
    tracker.update(step=1, error=0.1, kl_div=0.0)
    tracker.update(step=2, error=0.2, kl_div=0.0)
    tracker.update(step=3, error=0.3, kl_div=0.0)
    assert tracker.state.cumulative_error == 0.6
