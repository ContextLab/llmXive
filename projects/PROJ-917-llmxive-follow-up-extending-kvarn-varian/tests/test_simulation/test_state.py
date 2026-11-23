import pytest
import sys
from pathlib import Path

# Add code to path for imports if running from tests directory
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from simulation.state import SimulationState

class TestSimulationState:
    """
    Unit tests for the SimulationState dataclass.
    """

    def test_initial_state_defaults(self):
        """Test that a new SimulationState initializes with correct defaults."""
        state = SimulationState()
        assert state.accumulated_kl == 0.0
        assert state.step_index == 0
        assert state.full_trajectory == []
        assert isinstance(state.current_error_state, dict)
        assert len(state.current_error_state) == 0

    def test_update_accumulates_kl(self):
        """Test that update correctly accumulates KL-divergence."""
        initial_state = SimulationState(accumulated_kl=10.0, step_index=5)
        new_state = initial_state.update(step_kl=2.5)
        
        assert new_state.accumulated_kl == 12.5
        assert new_state.step_index == 6
        assert new_state.full_trajectory == [2.5]

    def test_update_extends_trajectory(self):
        """Test that update appends to the full_trajectory list."""
        initial_trajectory = [1.0, 2.0, 3.0]
        initial_state = SimulationState(
            accumulated_kl=6.0,
            step_index=3,
            full_trajectory=initial_trajectory
        )
        
        new_state = initial_state.update(step_kl=4.0)
        
        assert len(new_state.full_trajectory) == 4
        assert new_state.full_trajectory == [1.0, 2.0, 3.0, 4.0]
        assert new_state.accumulated_kl == 10.0

    def test_update_includes_error_details(self):
        """Test that update correctly stores error details."""
        state = SimulationState()
        error_data = {"loss": 0.05, "converged": True}
        new_state = state.update(step_kl=0.0, error_details=error_data)
        
        assert new_state.current_error_state == error_data
        assert new_state.step_index == 1

    def test_update_without_error_details(self):
        """Test that update works when error_details is None."""
        state = SimulationState()
        new_state = state.update(step_kl=0.0, error_details=None)
        
        assert new_state.current_error_state == {}
        assert new_state.step_index == 1

    def test_state_immutability(self):
        """Test that update returns a new state without modifying the original."""
        original = SimulationState(accumulated_kl=10.0, step_index=5)
        original_trajectory_ref = original.full_trajectory
        
        _ = original.update(step_kl=1.0)
        
        assert original.accumulated_kl == 10.0
        assert original.step_index == 5
        assert original.full_trajectory == []
        assert original.full_trajectory is original_trajectory_ref