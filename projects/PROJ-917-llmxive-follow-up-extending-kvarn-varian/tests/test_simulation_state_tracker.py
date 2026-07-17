"""
Tests for the Simulation State Tracking Framework (T006).

These tests verify:
1. Cumulative error accumulation
2. KL-divergence calculation and accumulation
3. Numerical stability (handling near-zero probabilities)
4. Snapshotting and history tracking
5. JSON serialization/deserialization
"""

import pytest
import numpy as np
import json
import tempfile
from pathlib import Path

# Import the module under test
from simulation.state_tracker import StateTracker, SimulationState, compute_kl_divergence_simple


def create_mock_logits(size=10):
    """Helper to create valid logit arrays."""
    return np.random.randn(size).astype(np.float64)


def create_mock_probs(size=10):
    """Helper to create valid probability arrays."""
    logits = np.random.randn(size)
    logits -= np.max(logits)
    probs = np.exp(logits)
    return probs / np.sum(probs)


class TestStateTrackerInitialization:
    def test_initial_state(self):
        tracker = StateTracker(epsilon=1e-8)
        assert tracker.step == 0
        assert tracker.cumulative_error == 0.0
        assert tracker.accumulated_kl_divergence == 0.0
        assert tracker.current_kl_divergence == 0.0

    def test_custom_initial_error(self):
        tracker = StateTracker(init_cumulative_error=5.0)
        assert tracker.cumulative_error == 5.0


class TestUpdateLogic:
    def test_update_increments_step(self):
        tracker = StateTracker()
        q_logits = create_mock_logits()
        fp_logits = create_mock_logits()

        tracker.update(q_logits, fp_logits, current_var=1.0, current_kurt=3.0)
        assert tracker.step == 1

        tracker.update(q_logits, fp_logits, current_var=1.0, current_kurt=3.0)
        assert tracker.step == 2

    def test_accumulates_kl_divergence(self):
        tracker = StateTracker()
        q_logits = create_mock_logits()
        fp_logits = create_mock_logits()

        # First update
        tracker.update(q_logits, fp_logits, current_var=1.0, current_kurt=3.0)
        kl_1 = tracker.current_kl_divergence
        acc_1 = tracker.accumulated_kl_divergence

        assert np.isclose(acc_1, kl_1)

        # Second update
        tracker.update(q_logits, fp_logits, current_var=1.0, current_kurt=3.0)
        kl_2 = tracker.current_kl_divergence
        acc_2 = tracker.accumulated_kl_divergence

        assert np.isclose(acc_2, acc_1 + kl_2)

    def test_accumulates_custom_error_metric(self):
        tracker = StateTracker()
        q_logits = create_mock_logits()
        fp_logits = create_mock_logits()

        tracker.update(q_logits, fp_logits, current_var=1.0, current_kurt=3.0, error_metric=0.5)
        assert np.isclose(tracker.cumulative_error, 0.5)

        tracker.update(q_logits, fp_logits, current_var=1.0, current_kurt=3.0, error_metric=0.3)
        assert np.isclose(tracker.cumulative_error, 0.8)

    def test_default_error_metric_is_mse(self):
        tracker = StateTracker()
        q_logits = create_mock_logits()
        fp_logits = create_mock_logits()

        # Manually compute expected MSE
        p_logits = fp_logits - np.max(fp_logits)
        q_logits_stable = q_logits - np.max(q_logits)
        p_probs = np.exp(p_logits) / (np.sum(np.exp(p_logits)) + 1e-8)
        q_probs = np.exp(q_logits_stable) / (np.sum(np.exp(q_logits_stable)) + 1e-8)

        expected_mse = np.mean((p_probs - q_probs) ** 2)

        tracker.update(q_logits, fp_logits, current_var=1.0, current_kurt=3.0)

        assert np.isclose(tracker.cumulative_error, expected_mse)


class TestNumericalStability:
    def test_handles_near_zero_probabilities(self):
        tracker = StateTracker(epsilon=1e-8)
        # Create logits that result in very small probabilities
        q_logits = np.array([-100.0, -100.0, -100.0])
        fp_logits = np.array([-100.0, -100.0, -100.0])

        # Should not raise an exception
        state = tracker.update(q_logits, fp_logits, current_var=1e-10, current_kurt=3.0)
        assert state.step == 1
        assert np.isfinite(state.accumulated_kl_divergence)

    def test_handles_identical_distributions(self):
        tracker = StateTracker()
        logits = create_mock_logits()

        # Same distribution for both
        state = tracker.update(logits, logits, current_var=1.0, current_kurt=3.0)

        # KL divergence should be ~0 for identical distributions
        assert state.current_kl_divergence < 1e-6


class TestSnapshotting:
    def test_snapshot_capture(self):
        tracker = StateTracker()
        q_logits = create_mock_logits()
        fp_logits = create_mock_logits()

        state = tracker.update(q_logits, fp_logits, current_var=1.0, current_kurt=3.0)

        assert isinstance(state, SimulationState)
        assert state.step == 1
        assert state.cumulative_error > 0
        assert state.accumulated_kl_divergence > 0

    def test_history_accumulation(self):
        tracker = StateTracker()
        q_logits = create_mock_logits()
        fp_logits = create_mock_logits()

        for _ in range(5):
            tracker.update(q_logits, fp_logits, current_var=1.0, current_kurt=3.0)

        history = tracker.get_history()
        assert len(history) == 5
        assert history[-1].step == 5


class TestReset:
    def test_reset_clears_state(self):
        tracker = StateTracker()
        q_logits = create_mock_logits()
        fp_logits = create_mock_logits()

        tracker.update(q_logits, fp_logits, current_var=1.0, current_kurt=3.0)
        tracker.update(q_logits, fp_logits, current_var=1.0, current_kurt=3.0)

        tracker.reset()

        assert tracker.step == 0
        assert tracker.cumulative_error == 0.0
        assert tracker.accumulated_kl_divergence == 0.0
        assert len(tracker.get_history()) == 0


class TestSummary:
    def test_summary_dict(self):
        tracker = StateTracker()
        q_logits = create_mock_logits()
        fp_logits = create_mock_logits()

        tracker.update(q_logits, fp_logits, current_var=1.0, current_kurt=3.0, error_metric=0.1)
        tracker.update(q_logits, fp_logits, current_var=1.0, current_kurt=3.0, error_metric=0.2)

        summary = tracker.to_summary_dict()

        assert summary["total_steps"] == 2
        assert np.isclose(summary["final_cumulative_error"], 0.3)
        assert "final_accumulated_kl" in summary
        assert "avg_kl_per_step" in summary

    def test_summary_empty_run(self):
        tracker = StateTracker()
        summary = tracker.to_summary_dict()
        assert summary["total_steps"] == 0
        assert summary["final_cumulative_error"] == 0.0


class TestSerialization:
    def test_save_and_load_history(self):
        tracker = StateTracker()
        q_logits = create_mock_logits()
        fp_logits = create_mock_logits()

        for _ in range(3):
            tracker.update(q_logits, fp_logits, current_var=1.0, current_kurt=3.0)

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            tracker.save_history(temp_path)
            assert Path(temp_path).exists()

            # Load into a new tracker
            new_tracker = StateTracker()
            new_tracker.load_history(temp_path)

            assert new_tracker.step == 3
            assert len(new_tracker.get_history()) == 3
            assert np.isclose(
                new_tracker.accumulated_kl_divergence,
                tracker.accumulated_kl_divergence
            )
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_load_nonexistent_file(self):
        tracker = StateTracker()
        with pytest.raises(FileNotFoundError):
            tracker.load_history("nonexistent_path.json")


class TestKLComputationUtility:
    def test_kl_divergence_computation(self):
        p = np.array([0.8, 0.1, 0.1])
        q = np.array([0.7, 0.2, 0.1])

        kl = compute_kl_divergence_simple(p, q)
        # Manual check: sum(p * log(p/q))
        expected = np.sum(p * np.log(p / q))

        assert np.isclose(kl, expected)

    def test_kl_identical(self):
        p = np.array([0.5, 0.5])
        q = np.array([0.5, 0.5])
        kl = compute_kl_divergence_simple(p, q)
        assert kl < 1e-8