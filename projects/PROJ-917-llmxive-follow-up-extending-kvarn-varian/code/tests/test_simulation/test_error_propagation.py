"""
Tests for error propagation in simulation.
"""
import pytest
import numpy as np
from simulation.state_tracker import StateTracker

def test_error_accumulates():
    """Test that errors accumulate over steps."""
    tracker = StateTracker()
    errors = [0.1, 0.2, 0.3, 0.4]
    for i, err in enumerate(errors):
        tracker.update(step=i+1, error=err, kl_div=0.0)
    assert tracker.state.cumulative_error == sum(errors)
