"""
Tests for saving/loading simulation state.
"""
import pytest
import json
from simulation.state_tracker import SimulationState, StateTracker
from pathlib import Path
import tempfile

def test_state_serialization():
    """Test that state can be serialized to JSON."""
    tracker = StateTracker()
    tracker.update(step=1, error=0.1, kl_div=0.05)
    state = tracker.state
    # Convert to dict for JSON serialization
    state_dict = {
        "step": state.step,
        "cumulative_error": state.cumulative_error,
        "total_kl_divergence": state.total_kl_divergence
    }
    json_str = json.dumps(state_dict)
    assert json_str is not None
