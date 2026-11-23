"""
Unit tests for simulation state tracking.
Tests cumulative error state and KL-divergence calculation.
"""
import pytest
import numpy as np
from simulation.state_tracker import SimulationState, StateTracker, compute_kl_divergence_simple

def test_simulation_state_initialization():
    """Test that SimulationState initializes correctly."""
    state = SimulationState()
    assert state.step == 0
    assert state.cumulative_error == 0.0
    assert state.total_kl_divergence == 0.0

def test_state_tracker_update():
    """Test state update logic."""
    tracker = StateTracker()
    tracker.update(step=1, error=0.1, kl_div=0.05)
    assert tracker.state.step == 1
    assert tracker.state.cumulative_error == 0.1
    assert tracker.state.total_kl_divergence == 0.05

def test_compute_kl_divergence_simple():
    """Test KL divergence calculation for simple distributions."""
    p = np.array([0.8, 0.2])
    q = np.array([0.5, 0.5])
    kl = compute_kl_divergence_simple(p, q)
    assert kl > 0
    assert np.isfinite(kl)

def test_compute_kl_divergence_zero_prob():
    """Test KL divergence handling of zero probabilities."""
    p = np.array([1.0, 0.0])
    q = np.array([0.5, 0.5])
    kl = compute_kl_divergence_simple(p, q)
    # Should handle 0 log 0 case gracefully
    assert np.isfinite(kl)
