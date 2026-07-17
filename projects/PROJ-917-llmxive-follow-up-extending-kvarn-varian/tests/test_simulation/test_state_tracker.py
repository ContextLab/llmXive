"""
Unit tests for the simulation state tracking framework.
"""
import pytest
import numpy as np
import json
import tempfile
from pathlib import Path

from simulation.state_tracker import (
    SimulationState,
    StateTracker,
    compute_kl_divergence_simple,
    compute_kl_divergence_batch,
    reset_tracker,
    load_state_tracker_from_file,
    save_state_tracker_to_file,
    compute_cumulative_kl_trace,
    compute_cumulative_error_trace,
    compute_average_kl_per_step,
    compute_average_error_per_step,
    validate_state_consistency
)


class TestSimulationState:
    """Tests for SimulationState dataclass."""

    def test_initialization(self):
        """Test default and custom initialization."""
        state = SimulationState(step=0)
        assert state.step == 0
        assert state.current_kl_divergence == 0.0
        assert state.cumulative_kl_divergence == 0.0
        assert state.current_error_magnitude == 0.0
        assert state.cumulative_error_magnitude == 0.0
        assert state.latency_ms == 0.0
        assert state.metadata == {}

        state_custom = SimulationState(
            step=5,
            current_kl_divergence=0.1,
            cumulative_kl_divergence=0.5,
            current_error_magnitude=0.05,
            cumulative_error_magnitude=0.25,
            latency_ms=2.5,
            metadata={"key": 1.0}
        )
        assert state_custom.step == 5
        assert state_custom.current_kl_divergence == 0.1
        assert state_custom.metadata["key"] == 1.0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        state = SimulationState(
            step=3,
            current_kl_divergence=0.1,
            cumulative_kl_divergence=0.5,
            current_error_magnitude=0.05,
            cumulative_error_magnitude=0.25,
            latency_ms=2.5,
            metadata={"metric": 1.0}
        )
        
        d = state.to_dict()
        assert d["step"] == 3
        assert d["current_kl_divergence"] == 0.1
        assert d["cumulative_kl_divergence"] == 0.5
        assert d["current_error_magnitude"] == 0.05
        assert d["cumulative_error_magnitude"] == 0.25
        assert d["latency_ms"] == 2.5
        assert d["metadata"]["metric"] == 1.0

    def test_from_dict(self):
        """Test reconstruction from dictionary."""
        data = {
            "step": 10,
            "current_kl_divergence": 0.2,
            "cumulative_kl_divergence": 1.0,
            "current_error_magnitude": 0.1,
            "cumulative_error_magnitude": 0.5,
            "latency_ms": 3.0,
            "metadata": {"test": 2.0}
        }
        
        state = SimulationState.from_dict(data)
        assert state.step == 10
        assert state.current_kl_divergence == 0.2
        assert state.cumulative_kl_divergence == 1.0
        assert state.metadata["test"] == 2.0

    def test_round_trip(self):
        """Test serialization round-trip."""
        state = SimulationState(
            step=7,
            current_kl_divergence=0.15,
            cumulative_kl_divergence=0.75,
            current_error_magnitude=0.08,
            cumulative_error_magnitude=0.40,
            latency_ms=2.0,
            metadata={"a": 1.0, "b": 2.0}
        )
        
        d = state.to_dict()
        restored = SimulationState.from_dict(d)
        
        assert restored.step == state.step
        assert restored.current_kl_divergence == state.current_kl_divergence
        assert restored.cumulative_kl_divergence == state.cumulative_kl_divergence
        assert restored.current_error_magnitude == state.current_error_magnitude
        assert restored.cumulative_error_magnitude == state.cumulative_error_magnitude
        assert restored.latency_ms == state.latency_ms
        assert restored.metadata == state.metadata


class TestStateTracker:
    """Tests for StateTracker class."""

    def test_initialization(self):
        """Test tracker initialization."""
        tracker = StateTracker()
        assert tracker.total_steps == 0
        assert len(tracker.states) == 0
        assert tracker.current_state.step == 0

    def test_update_basic(self):
        """Test basic state update."""
        tracker = StateTracker()
        state = tracker.update(
            step=0,
            current_kl=0.1,
            current_error=0.05,
            latency_ms=1.5,
            metadata={"test": 1.0}
        )
        
        assert len(tracker.states) == 1
        assert tracker.total_steps == 1
        assert state.step == 0
        assert state.current_kl_divergence == 0.1
        assert state.cumulative_kl_divergence == 0.1
        assert state.current_error_magnitude == 0.05
        assert state.cumulative_error_magnitude == 0.05
        assert state.latency_ms == 1.5
        assert state.metadata["test"] == 1.0

    def test_update_accumulation(self):
        """Test cumulative metric accumulation."""
        tracker = StateTracker()
        
        tracker.update(step=0, current_kl=0.1, current_error=0.05)
        tracker.update(step=1, current_kl=0.2, current_error=0.1)
        tracker.update(step=2, current_kl=0.15, current_error=0.08)
        
        assert tracker.total_steps == 3
        assert len(tracker.states) == 3
        
        final_state = tracker.get_final_state()
        assert final_state.cumulative_kl_divergence == 0.45  # 0.1 + 0.2 + 0.15
        assert final_state.cumulative_error_magnitude == 0.23  # 0.05 + 0.1 + 0.08

    def test_update_invalid_kl(self):
        """Test update with invalid KL value raises error."""
        tracker = StateTracker()
        
        with pytest.raises(ValueError):
            tracker.update(step=0, current_kl=float('nan'), current_error=0.05)

    def test_update_invalid_error(self):
        """Test update with invalid error value raises error."""
        tracker = StateTracker()
        
        with pytest.raises(ValueError):
            tracker.update(step=0, current_kl=0.1, current_error=float('inf'))

    def test_get_accumulated_metrics(self):
        """Test accumulated metrics calculation."""
        tracker = StateTracker()
        
        tracker.update(step=0, current_kl=0.1, current_error=0.05, latency_ms=1.0)
        tracker.update(step=1, current_kl=0.2, current_error=0.1, latency_ms=2.0)
        tracker.update(step=2, current_kl=0.15, current_error=0.08, latency_ms=3.0)
        
        metrics = tracker.get_accumulated_metrics()
        
        assert metrics["total_steps"] == 3
        assert metrics["cumulative_kl_divergence"] == 0.45
        assert metrics["cumulative_error_magnitude"] == 0.23
        assert metrics["average_latency_ms"] == pytest.approx(2.0)
        assert metrics["final_current_kl"] == 0.15
        assert metrics["final_current_error"] == 0.08

    def test_empty_tracker_metrics(self):
        """Test metrics for empty tracker."""
        tracker = StateTracker()
        metrics = tracker.get_accumulated_metrics()
        
        assert metrics["total_steps"] == 0
        assert metrics["cumulative_kl_divergence"] == 0.0
        assert metrics["average_latency_ms"] == 0.0

    def test_to_json_string(self):
        """Test JSON serialization to string."""
        tracker = StateTracker()
        tracker.update(step=0, current_kl=0.1, current_error=0.05)
        tracker.update(step=1, current_kl=0.2, current_error=0.1)
        
        json_str = tracker.to_json()
        data = json.loads(json_str)
        
        assert data["total_steps"] == 2
        assert len(data["states"]) == 2
        assert "summary" in data

    def test_to_json_file(self):
        """Test JSON serialization to file."""
        tracker = StateTracker()
        tracker.update(step=0, current_kl=0.1, current_error=0.05)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_state.json"
            json_str = tracker.to_json(path)
            
            assert path.exists()
            with open(path, 'r') as f:
                file_content = f.read()
            assert json_str == file_content

    def test_from_json(self):
        """Test reconstruction from JSON."""
        tracker = StateTracker()
        tracker.update(step=0, current_kl=0.1, current_error=0.05, metadata={"a": 1.0})
        tracker.update(step=1, current_kl=0.2, current_error=0.1, metadata={"b": 2.0})
        
        json_str = tracker.to_json()
        restored = StateTracker.from_json(json_str)
        
        assert restored.total_steps == 2
        assert len(restored.states) == 2
        assert restored.states[0].metadata["a"] == 1.0
        assert restored.states[1].metadata["b"] == 2.0

    def test_from_json_file(self):
        """Test reconstruction from JSON file."""
        tracker = StateTracker()
        tracker.update(step=0, current_kl=0.1, current_error=0.05)
        tracker.update(step=1, current_kl=0.2, current_error=0.1)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_state.json"
            tracker.to_json(path)
            
            restored = load_state_tracker_from_file(path)
            assert restored.total_steps == 2
            assert len(restored.states) == 2

    def test_save_load_file(self):
        """Test save and load cycle."""
        tracker = StateTracker()
        tracker.update(step=0, current_kl=0.1, current_error=0.05)
        tracker.update(step=1, current_kl=0.2, current_error=0.1)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_state.json"
            save_state_tracker_to_file(tracker, path)
            loaded = load_state_tracker_from_file(path)
            
            assert loaded.total_steps == tracker.total_steps
            assert len(loaded.states) == len(tracker.states)
            assert loaded.states[-1].cumulative_kl_divergence == tracker.states[-1].cumulative_kl_divergence


class TestKLCompute:
    """Tests for KL-divergence computation functions."""

    def test_kl_divergence_identical(self):
        """Test KL-divergence of identical distributions is ~0."""
        p = np.array([0.2, 0.3, 0.5])
        q = np.array([0.2, 0.3, 0.5])
        
        kl = compute_kl_divergence_simple(p, q)
        assert kl == pytest.approx(0.0, abs=1e-6)

    def test_kl_divergence_different(self):
        """Test KL-divergence of different distributions is positive."""
        p = np.array([0.5, 0.3, 0.2])
        q = np.array([0.2, 0.3, 0.5])
        
        kl = compute_kl_divergence_simple(p, q)
        assert kl > 0

    def test_kl_divergence_zero_handling(self):
        """Test KL-divergence handles zeros with epsilon floor."""
        p = np.array([0.5, 0.5, 0.0])
        q = np.array([0.3, 0.3, 0.4])
        
        kl = compute_kl_divergence_simple(p, q)
        # Should not be inf due to epsilon floor
        assert not np.isinf(kl)
        assert kl > 0

    def test_kl_divergence_invalid(self):
        """Test KL-divergence returns inf for invalid inputs."""
        p = np.array([float('nan'), 0.5, 0.5])
        q = np.array([0.3, 0.3, 0.4])
        
        kl = compute_kl_divergence_simple(p, q)
        assert np.isinf(kl)

    def test_kl_divergence_batch(self):
        """Test batch KL-divergence computation."""
        p_batch = np.array([
            [0.5, 0.3, 0.2],
            [0.3, 0.4, 0.3],
            [0.8, 0.1, 0.1]
        ])
        q_batch = np.array([
            [0.2, 0.3, 0.5],
            [0.3, 0.4, 0.3],
            [0.1, 0.8, 0.1]
        ])
        
        kl_divs = compute_kl_divergence_batch(p_batch, q_batch)
        
        assert kl_divs.shape == (3,)
        # Second pair is identical, so KL should be ~0
        assert kl_divs[1] == pytest.approx(0.0, abs=1e-6)
        # Others should be positive
        assert kl_divs[0] > 0
        assert kl_divs[2] > 0

    def test_kl_divergence_batch_shape_mismatch(self):
        """Test batch KL-divergence raises on shape mismatch."""
        p_batch = np.array([[0.5, 0.3, 0.2]])
        q_batch = np.array([[0.2, 0.3], [0.3, 0.4]])
        
        with pytest.raises(ValueError):
            compute_kl_divergence_batch(p_batch, q_batch)


class TestHelperFunctions:
    """Tests for helper utility functions."""

    def test_reset_tracker(self):
        """Test reset_tracker factory function."""
        tracker = reset_tracker()
        assert isinstance(tracker, StateTracker)
        assert tracker.total_steps == 0

    def test_compute_traces(self):
        """Test trace extraction functions."""
        tracker = StateTracker()
        tracker.update(step=0, current_kl=0.1, current_error=0.05)
        tracker.update(step=1, current_kl=0.2, current_error=0.1)
        tracker.update(step=2, current_kl=0.15, current_error=0.08)
        
        kl_trace = compute_cumulative_kl_trace(tracker)
        error_trace = compute_cumulative_error_trace(tracker)
        
        assert kl_trace == [0.1, 0.3, 0.45]
        assert error_trace == [0.05, 0.15, 0.23]

    def test_compute_averages(self):
        """Test average calculation functions."""
        tracker = StateTracker()
        tracker.update(step=0, current_kl=0.1, current_error=0.05)
        tracker.update(step=1, current_kl=0.2, current_error=0.1)
        tracker.update(step=2, current_kl=0.15, current_error=0.08)
        
        avg_kl = compute_average_kl_per_step(tracker)
        avg_error = compute_average_error_per_step(tracker)
        
        assert avg_kl == pytest.approx(0.45 / 3)
        assert avg_error == pytest.approx(0.23 / 3)

    def test_empty_tracker_averages(self):
        """Test average functions with empty tracker."""
        tracker = StateTracker()
        
        assert compute_average_kl_per_step(tracker) == 0.0
        assert compute_average_error_per_step(tracker) == 0.0

    def test_validate_state_consistency_pass(self):
        """Test consistency validation passes for valid data."""
        tracker = StateTracker()
        tracker.update(step=0, current_kl=0.1, current_error=0.05)
        tracker.update(step=1, current_kl=0.2, current_error=0.1)
        
        is_valid, errors = validate_state_consistency(tracker)
        assert is_valid
        assert len(errors) == 0

    def test_validate_state_consistency_empty(self):
        """Test consistency validation with empty tracker."""
        tracker = StateTracker()
        is_valid, errors = validate_state_consistency(tracker)
        assert is_valid
        assert len(errors) == 0

    def test_validate_state_consistency_decrease(self):
        """Test consistency validation catches decreases."""
        tracker = StateTracker()
        tracker.update(step=0, current_kl=0.1, current_error=0.05)
        # Manually create a state with decreased cumulative value
        from simulation.state_tracker import SimulationState
        bad_state = SimulationState(
            step=1,
            current_kl_divergence=0.05,
            cumulative_kl_divergence=0.05,  # Decreased from 0.1
            current_error_magnitude=0.1,
            cumulative_error_magnitude=0.15
        )
        tracker.states.append(bad_state)
        tracker.total_steps = 2
        
        is_valid, errors = validate_state_consistency(tracker)
        assert not is_valid
        assert len(errors) > 0
        assert any("decreased" in err for err in errors)

class TestStateTrackerIntegration:
    """Integration tests for StateTracker workflow."""

    def test_full_workflow(self):
        """Test complete workflow of tracking and saving/loading."""
        tracker = reset_tracker()
        
        # Simulate a run
        for i in range(5):
            tracker.update(
                step=i,
                current_kl=0.1 * (i + 1),
                current_error=0.05 * (i + 1),
                latency_ms=2.0 + i * 0.1,
                metadata={"iteration": i}
            )
        
        # Save
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "full_workflow.json"
            tracker.to_json(path)
            
            # Load
            loaded = load_state_tracker_from_file(path)
            
            # Verify
            assert loaded.total_steps == tracker.total_steps
            assert len(loaded.states) == len(tracker.states)
            
            for orig, load_state in zip(tracker.states, loaded.states):
                assert orig.step == load_state.step
                assert orig.cumulative_kl_divergence == load_state.cumulative_kl_divergence
                assert orig.cumulative_error_magnitude == load_state.cumulative_error_magnitude
                assert orig.metadata == load_state.metadata
            
            # Verify metrics match
            orig_metrics = tracker.get_accumulated_metrics()
            load_metrics = loaded.get_accumulated_metrics()
            
            assert orig_metrics["cumulative_kl_divergence"] == load_metrics["cumulative_kl_divergence"]
            assert orig_metrics["cumulative_error_magnitude"] == load_metrics["cumulative_error_magnitude"]
            assert orig_metrics["average_latency_ms"] == pytest.approx(load_metrics["average_latency_ms"])

    def test_long_run_tracking(self):
        """Test tracking over many steps."""
        tracker = StateTracker()
        n_steps = 1000
        
        for i in range(n_steps):
            tracker.update(
                step=i,
                current_kl=0.01,
                current_error=0.005,
                latency_ms=1.0
            )
        
        assert tracker.total_steps == n_steps
        assert len(tracker.states) == n_steps
        
        final = tracker.get_final_state()
        assert final.cumulative_kl_divergence == pytest.approx(0.01 * n_steps)
        assert final.cumulative_error_magnitude == pytest.approx(0.005 * n_steps)
        
        metrics = tracker.get_accumulated_metrics()
        assert metrics["average_latency_ms"] == pytest.approx(1.0)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])