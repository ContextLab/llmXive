"""
Unit tests for code/simulate_agent.py
Verifies sigmoid function, heuristic solver, evidence visibility, and simulation logic.
"""
import pytest
import math
import sys
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.simulate_agent import sigmoid, heuristic_solver_success, check_evidence_visibility


class TestSigmoid:
    """Tests for the sigmoid function used in heuristic solver."""

    def test_zero_input(self):
        """Sigmoid(0) should be 0.5."""
        assert sigmoid(0, alpha=1.0, threshold=0.0) == 0.5

    def test_large_positive(self):
        """Sigmoid(large positive) should approach 1."""
        assert sigmoid(10, alpha=1.0, threshold=0.0) > 0.99

    def test_large_negative(self):
        """Sigmoid(large negative) should approach 0."""
        assert sigmoid(-10, alpha=1.0, threshold=0.0) < 0.01

    def test_threshold_shift(self):
        """Verify threshold parameter shifts the curve."""
        # With threshold=0.5, sigmoid(0.5) should be 0.5
        assert sigmoid(0.5, alpha=1.0, threshold=0.5) == 0.5

    def test_alpha_scaling(self):
        """Verify alpha parameter scales the slope."""
        # Higher alpha should make the transition sharper
        s1 = sigmoid(0.6, alpha=1.0, threshold=0.5)
        s2 = sigmoid(0.6, alpha=10.0, threshold=0.5)
        # s2 should be closer to 1 than s1
        assert s2 > s1


class TestHeuristicSolverSuccess:
    """Tests for the heuristic solver success logic."""

    def test_probabilistic_outcome(self):
        """Verify that the function returns 0 or 1 based on probability."""
        # Run multiple times to ensure it can return both 0 and 1
        # With a density that gives ~50% probability
        results = [heuristic_solver_success(density=0.5, alpha=10.0, threshold=0.5) for _ in range(100)]
        assert 0 in results
        assert 1 in results

    def test_high_density_success(self):
        """High density should result in high success probability."""
        # With very high alpha, density >> threshold should be almost always 1
        results = [heuristic_solver_success(density=0.9, alpha=100.0, threshold=0.5) for _ in range(100)]
        # Should be all 1s or mostly 1s
        assert sum(results) > 95

    def test_low_density_failure(self):
        """Low density should result in low success probability."""
        results = [heuristic_solver_success(density=0.1, alpha=100.0, threshold=0.5) for _ in range(100)]
        assert sum(results) < 5


class TestCheckEvidenceVisibility:
    """Tests for evidence visibility logic based on retention horizon."""

    def test_evidence_within_horizon(self):
        """Evidence should be visible if within the retention horizon."""
        # Current turn = 10, Horizon = 5, Evidence turn = 7
        # Window: [10-5+1, 10] = [6, 10]. Evidence at 7 is visible.
        assert check_evidence_visibility(current_turn=10, retention_horizon=5, evidence_turn=7) is True

    def test_evidence_outside_horizon(self):
        """Evidence should be invisible if outside the retention horizon."""
        # Current turn = 10, Horizon = 3, Evidence turn = 5
        # Window: [10-3+1, 10] = [8, 10]. Evidence at 5 is invisible.
        assert check_evidence_visibility(current_turn=10, retention_horizon=3, evidence_turn=5) is False

    def test_evidence_at_boundary(self):
        """Evidence at the exact boundary should be visible."""
        # Current turn = 10, Horizon = 5, Evidence turn = 6
        # Window: [6, 10]. Evidence at 6 is visible.
        assert check_evidence_visibility(current_turn=10, retention_horizon=5, evidence_turn=6) is True

    def test_last_turn_edge_case(self):
        """Verify edge case where evidence is at the very last turn (T)."""
        # Current turn = T, Horizon = 1, Evidence turn = T
        # Window: [T, T]. Evidence at T is visible.
        assert check_evidence_visibility(current_turn=10, retention_horizon=1, evidence_turn=10) is True

    def test_zero_horizon(self):
        """Zero horizon should make everything invisible."""
        assert check_evidence_visibility(current_turn=10, retention_horizon=0, evidence_turn=5) is False
