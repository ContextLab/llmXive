"""
Unit tests for the SimulationState dataclass.
"""
import pytest
import numpy as np
from simulation.state import SimulationState


class TestSimulationState:
    """Tests for the SimulationState dataclass."""

    def test_initialization_defaults(self):
        """Test that default values are set correctly on initialization."""
        state = SimulationState()
        assert state.accumulated_kl == 0.0
        assert state.step_index == 0
        assert state.current_error_state == {}

    def test_initialization_custom(self):
        """Test initialization with custom values."""
        initial_kl = 1.5
        initial_index = 10
        initial_error = {"metric_a": 0.1, "metric_b": 0.2}

        state = SimulationState(
            accumulated_kl=initial_kl,
            current_error_state=initial_error,
            step_index=initial_index
        )

        assert state.accumulated_kl == initial_kl
        assert state.step_index == initial_index
        assert state.current_error_state == initial_error

    def test_update_accumulates_kl(self):
        """Test that update correctly accumulates KL divergence."""
        state = SimulationState(accumulated_kl=1.0, step_index=0)
        delta = 0.5
        new_state = state.update(step_delta_kl=delta)

        assert new_state.accumulated_kl == pytest.approx(1.5)
        assert new_state.step_index == 1

    def test_update_increments_step_index(self):
        """Test that update correctly increments the step index."""
        state = SimulationState(step_index=5)
        new_state = state.update(step_delta_kl=0.0)

        assert new_state.step_index == 6

    def test_update_merges_error_metrics(self):
        """Test that update merges new error metrics into the state."""
        state = SimulationState(
            current_error_state={"existing": 100}
        )
        new_metrics = {"new_metric": 200, "existing": 300}  # Overwrite existing
        new_state = state.update(step_delta_kl=0.0, new_error_metrics=new_metrics)

        assert new_state.current_error_state["existing"] == 300
        assert new_state.current_error_state["new_metric"] == 200

    def test_update_preserves_error_state_when_none(self):
        """Test that update preserves error state when new_metrics is None."""
        state = SimulationState(current_error_state={"keep": "value"})
        new_state = state.update(step_delta_kl=0.0, new_error_metrics=None)

        assert new_state.current_error_state == {"keep": "value"}

    def test_to_dict_serialization(self):
        """Test serialization to dictionary."""
        state = SimulationState(
            accumulated_kl=2.5,
            current_error_state={"key": "val"},
            step_index=5
        )
        data = state.to_dict()

        assert data["accumulated_kl"] == 2.5
        assert data["current_error_state"] == {"key": "val"}
        assert data["step_index"] == 5

    def test_from_dict_deserialization(self):
        """Test deserialization from dictionary."""
        data = {
            "accumulated_kl": 3.3,
            "current_error_state": {"foo": "bar"},
            "step_index": 12
        }
        state = SimulationState.from_dict(data)

        assert state.accumulated_kl == 3.3
        assert state.current_error_state == {"foo": "bar"}
        assert state.step_index == 12

    def test_round_trip_serialization(self):
        """Test that to_dict and from_dict are inverses."""
        original = SimulationState(
            accumulated_kl=1.23,
            current_error_state={"a": 1, "b": [1, 2, 3]},
            step_index=42
        )
        data = original.to_dict()
        restored = SimulationState.from_dict(data)

        assert restored.accumulated_kl == original.accumulated_kl
        assert restored.current_error_state == original.current_error_state
        assert restored.step_index == original.step_index

    def test_update_returns_new_instance(self):
        """Test that update does not modify the original state."""
        state = SimulationState(accumulated_kl=1.0, step_index=0)
        new_state = state.update(step_delta_kl=1.0)

        assert state.accumulated_kl == 1.0
        assert state.step_index == 0
        assert new_state.accumulated_kl == 2.0
        assert new_state.step_index == 1