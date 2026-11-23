"""
Unit tests for code/validate_convergence.py
"""
import pytest
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils import CONVERGENCE_THRESHOLD, MAX_EPOCHS
from validate_convergence import determine_convergence_status


class TestConvergenceLogic:
    def test_converged_first_epoch(self):
        """Test convergence at the very first step."""
        trajectory = [{"epoch": 1, "loss": 0.5, "accuracy": 0.95}]
        status, steps, acc = determine_convergence_status(trajectory)
        assert status == "converged"
        assert steps == 1
        assert acc == 0.95

    def test_converged_exact_threshold(self):
        """Test convergence when accuracy exactly equals threshold."""
        trajectory = [{"epoch": 1, "loss": 0.5, "accuracy": CONVERGENCE_THRESHOLD}]
        status, steps, acc = determine_convergence_status(trajectory)
        assert status == "converged"
        assert steps == 1

    def test_censored_below_threshold(self):
        """Test censoring when accuracy is just below threshold at max epochs."""
        trajectory = [
            {"epoch": i, "loss": 1.0, "accuracy": 0.89}
            for i in range(1, MAX_EPOCHS + 1)
        ]
        status, steps, acc = determine_convergence_status(trajectory)
        assert status == "censored"
        assert steps == MAX_EPOCHS
        assert acc == 0.89

    def test_converged_early_then_drops(self):
        """Test that once converged, we stop counting steps (early exit)."""
        trajectory = [
            {"epoch": 1, "loss": 0.5, "accuracy": 0.5},
            {"epoch": 2, "loss": 0.3, "accuracy": 0.95}, # Converges here
            {"epoch": 3, "loss": 0.1, "accuracy": 0.40}, # Drops later (shouldn't matter)
        ]
        status, steps, acc = determine_convergence_status(trajectory)
        assert status == "converged"
        assert steps == 2
        assert acc == 0.40 # Final accuracy is from the last epoch

    def test_censored_max_epoch_boundary(self):
        """Test edge case at MAX_EPOCHS with value just under threshold."""
        trajectory = [
            {"epoch": i, "loss": 1.0, "accuracy": 0.89999}
            for i in range(1, MAX_EPOCHS + 1)
        ]
        status, steps, acc = determine_convergence_status(trajectory)
        assert status == "censored"
        assert steps == MAX_EPOCHS

    def test_converged_at_max_epoch_boundary(self):
        """Test edge case at MAX_EPOCHS with value exactly at threshold."""
        trajectory = [
            {"epoch": i, "loss": 1.0, "accuracy": 0.80 + (i * 0.01)}
            for i in range(1, MAX_EPOCHS)
        ]
        # Force last epoch to be exactly threshold
        trajectory.append({"epoch": MAX_EPOCHS, "loss": 0.0, "accuracy": CONVERGENCE_THRESHOLD})
        
        status, steps, acc = determine_convergence_status(trajectory)
        assert status == "converged"
        assert steps == MAX_EPOCHS