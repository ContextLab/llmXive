import pytest
import numpy as np
from simulation.state import SimulationState

class TestSimulationState:
    """Tests for the SimulationState dataclass."""

    def test_initial_state(self):
        """Test that a new SimulationState initializes with correct defaults."""
        state = SimulationState()
        assert state.accumulated_kl == 0.0
        assert state.step_index == 0
        assert state.full_trajectory == []
        assert state.current_error_state == {}

    def test_update_state(self):
        """Test updating the state with a new step."""
        state = SimulationState()
        initial_kl = 0.5
        error_details = {"error_type": "quantization", "magnitude": 0.1}
        
        state.update(initial_kl, error_details)
        
        assert state.accumulated_kl == initial_kl
        assert state.step_index == 1
        assert len(state.full_trajectory) == 1
        assert state.full_trajectory[0] == initial_kl
        assert state.current_error_state == error_details

    def test_multiple_updates(self):
        """Test accumulating multiple steps."""
        state = SimulationState()
        steps = [0.1, 0.2, 0.3]
        
        for step_kl in steps:
            state.update(step_kl)
        
        expected_total = sum(steps)
        assert state.accumulated_kl == pytest.approx(expected_total)
        assert state.step_index == len(steps)
        assert state.full_trajectory == steps

    def test_to_dict_serialization(self):
        """Test converting state to dictionary."""
        state = SimulationState()
        state.update(0.5, {"metric": "test"})
        
        data = state.to_dict()
        
        assert isinstance(data, dict)
        assert data["accumulated_kl"] == 0.5
        assert data["step_index"] == 1
        assert data["full_trajectory"] == [0.5]
        assert data["current_error_state"] == {"metric": "test"}

    def test_from_dict_deserialization(self):
        """Test creating state from dictionary."""
        data = {
            "accumulated_kl": 1.5,
            "current_error_state": {"source": "reconstruction"},
            "step_index": 3,
            "full_trajectory": [0.5, 0.5, 0.5]
        }
        
        state = SimulationState.from_dict(data)
        
        assert state.accumulated_kl == 1.5
        assert state.step_index == 3
        assert state.full_trajectory == [0.5, 0.5, 0.5]
        assert state.current_error_state == {"source": "reconstruction"}

    def test_round_trip_serialization(self):
        """Test that to_dict and from_dict preserve state."""
        original = SimulationState()
        original.update(0.25, {"type": "round_trip"})
        original.update(0.25)
        
        data = original.to_dict()
        restored = SimulationState.from_dict(data)
        
        assert restored.accumulated_kl == original.accumulated_kl
        assert restored.step_index == original.step_index
        assert restored.full_trajectory == original.full_trajectory
        assert restored.current_error_state == original.current_error_state

    def test_reset_state(self):
        """Test resetting the state to initial values."""
        state = SimulationState()
        state.update(1.0, {"data": "temp"})
        state.update(1.0)
        
        state.reset()
        
        assert state.accumulated_kl == 0.0
        assert state.step_index == 0
        assert state.full_trajectory == []
        assert state.current_error_state == {}

    def test_update_without_error_details(self):
        """Test updating state without providing error details."""
        state = SimulationState()
        state.update(0.5)
        
        # current_error_state should remain empty or unchanged if not provided
        # (depending on implementation, but here we check it doesn't crash)
        assert state.step_index == 1
        assert state.accumulated_kl == 0.5