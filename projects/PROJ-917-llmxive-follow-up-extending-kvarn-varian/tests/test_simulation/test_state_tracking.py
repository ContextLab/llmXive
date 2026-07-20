"""
Unit tests for SimulationState and StateTracker in code/simulation/state_tracker.py.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.simulation.state_tracker import (
    SimulationState,
    StateTracker,
    compute_kl_divergence_simple
)


def test_simulation_state_initialization():
    """Test that SimulationState initializes with correct defaults."""
    state = SimulationState()
    assert state.accumulated_kl == 0.0
    assert state.step_index == 0
    assert state.current_error_state is not None


def test_state_tracker_update():
    """Test that StateTracker correctly updates accumulated KL."""
    tracker = StateTracker()
    
    # Simulate a step with a known KL divergence
    p = np.array([0.8, 0.2])
    q = np.array([0.2, 0.8])
    kl = compute_kl_divergence_simple(p, q)
    
    tracker.update(kl)
    
    assert tracker.state.step_index == 1
    assert np.isclose(tracker.state.accumulated_kl, kl)


def test_compute_kl_divergence_simple():
    """Test the underlying KL divergence function."""
    p = np.array([0.5, 0.5])
    q = np.array([0.5, 0.5])
    assert np.isclose(compute_kl_divergence_simple(p, q), 0.0)
    
    p = np.array([1.0, 0.0])
    q = np.array([0.5, 0.5])
    # Should be finite due to epsilon handling in implementation
    result = compute_kl_divergence_simple(p, q)
    assert np.isfinite(result)
