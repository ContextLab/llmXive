"""
Unit tests for state space degradation logic in synthetic_mdp.py.

Verifies that when N > 50, the state space size |S| is reduced by a factor of 2
(halved) as per FR-016 and T034 requirements.
"""

import pytest
import sys
import os
import logging
from unittest.mock import patch
import io

# Add code directory to path if running standalone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.environment.synthetic_mdp import generate_mdp, SyntheticTabularMDP


class TestRunnerDegradation:
    """Test suite for state space reduction logic."""

    def test_n_le_50_no_reduction(self):
        """Test that N <= 50 does not trigger state space reduction."""
        mdp = generate_mdp(n_objectives=50, force_reduce_state_space=True)
        assert mdp.n_states == 100, f"Expected 100 states for N=50, got {mdp.n_states}"
        assert not mdp.state_space_reduced, "State space should not be reduced for N=50"

    def test_n_51_reduction_triggered(self):
        """Test that N > 50 triggers state space reduction."""
        mdp = generate_mdp(n_objectives=51, force_reduce_state_space=True)
        assert mdp.n_states == 50, f"Expected 50 states for N=51, got {mdp.n_states}"
        assert mdp.state_space_reduced, "State space should be reduced for N=51"

    def test_n_100_reduction_triggered(self):
        """Test that N=100 triggers state space reduction."""
        mdp = generate_mdp(n_objectives=100, force_reduce_state_space=True)
        assert mdp.n_states == 50, f"Expected 50 states for N=100, got {mdp.n_states}"
        assert mdp.state_space_reduced, "State space should be reduced for N=100"

    def test_force_reduce_false_no_reduction(self):
        """Test that force_reduce_state_space=False prevents reduction."""
        mdp = generate_mdp(n_objectives=100, force_reduce_state_space=False)
        assert mdp.n_states == 100, f"Expected 100 states when force_reduce=False, got {mdp.n_states}"
        assert not mdp.state_space_reduced, "State space should not be reduced when force_reduce=False"

    def test_explicit_n_states_ignores_reduction(self):
        """Test that explicitly provided n_states overrides default reduction logic."""
        mdp = generate_mdp(n_objectives=100, n_states=200, force_reduce_state_space=True)
        assert mdp.n_states == 200, f"Expected 200 states when explicitly set, got {mdp.n_states}"
        assert not mdp.state_space_reduced, "State space should not be marked reduced if explicitly set"

    def test_warning_logged_on_reduction(self):
        """Test that a warning is logged when state space is reduced."""
        # Capture log output
        with patch('logging.Logger.warning') as mock_warn:
            mdp = generate_mdp(n_objectives=100, force_reduce_state_space=True)
            
            # Verify warning was called
            assert mock_warn.called, "Logger.warning should be called when state space is reduced"
            
            # Verify warning message contains expected text
            warning_msg = mock_warn.call_args[0][0]
            assert "State space reduced" in warning_msg, f"Warning message unexpected: {warning_msg}"
            assert "N=100" in warning_msg, f"Warning message should contain N=100: {warning_msg}"

    def test_metadata_reflects_reduction(self):
        """Test that metadata dictionary correctly reflects state space reduction."""
        mdp = generate_mdp(n_objectives=100, force_reduce_state_space=True)
        assert mdp.metadata["state_space_reduced"] is True
        assert mdp.metadata["original_n_states"] == 100

        mdp_no_reduce = generate_mdp(n_objectives=50, force_reduce_state_space=True)
        assert mdp_no_reduce.metadata["state_space_reduced"] is False
        assert mdp_no_reduce.metadata.get("original_n_states") is None
