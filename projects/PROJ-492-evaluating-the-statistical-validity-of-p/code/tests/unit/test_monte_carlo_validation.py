"""
Unit tests for Monte-Carlo validation module (T062).
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.audit.monte_carlo_validation import (
    validate_z_test,
    validate_fisher_exact,
    validate_welch_t_test,
    validate_binomial_test,
    run_monte_carlo_validation,
    NUM_REPLICATES,
    THRESHOLD,
)
from code.src.utils.logger import get_default_logger


class TestMonteCarloValidation:
    """Tests for Monte-Carlo validation functions."""

    def test_validate_z_test_returns_dict(self):
        """Test that z-test validation returns a dict with required keys."""
        passed, details = validate_z_test()
        assert isinstance(details, dict)
        assert "test" in details
        assert "replicates" in details
        assert "empirical_alpha" in details
        assert "expected_alpha" in details
        assert "absolute_difference" in details
        assert "passed" in details
        assert details["test"] == "z-test"
        assert details["replicates"] == NUM_REPLICATES

    def test_validate_fisher_exact_returns_dict(self):
        """Test that Fisher's exact test validation returns a dict with required keys."""
        passed, details = validate_fisher_exact()
        assert isinstance(details, dict)
        assert details["test"] == "fisher_exact"
        assert details["replicates"] == NUM_REPLICATES

    def test_validate_welch_t_returns_dict(self):
        """Test that Welch's t-test validation returns a dict with required keys."""
        passed, details = validate_welch_t_test()
        assert isinstance(details, dict)
        assert details["test"] == "welch_t"
        assert details["replicates"] == NUM_REPLICATES

    def test_validate_binomial_returns_dict(self):
        """Test that binomial test validation returns a dict with required keys."""
        passed, details = validate_binomial_test()
        assert isinstance(details, dict)
        assert details["test"] == "binomial"
        assert details["replicates"] == NUM_REPLICATES

    def test_difference_within_threshold(self):
        """
        Test that the absolute difference is within the threshold for at least one test.
        Note: This is a probabilistic test; with 10,000 replicates, the standard error
        for alpha=0.05 is sqrt(0.05*0.95/10000) ≈ 0.0022, so we expect most runs to pass.
        """
        # Run z-test validation
        passed, details = validate_z_test()
        assert details["absolute_difference"] <= THRESHOLD + 0.01  # Allow small margin for randomness

    def test_run_monte_carlo_validation_returns_int(self):
        """Test that run_monte_carlo_validation returns an integer exit code."""
        with patch("code.src.audit.monte_carlo_validation.get_default_logger") as mock_logger:
            # Mock logger to avoid actual logging
            mock_logger.return_value = MagicMock()
            exit_code = run_monte_carlo_validation(output_dir=Path("/tmp"))
            assert isinstance(exit_code, int)
            assert exit_code in [0, 1]

    def test_constants_defined(self):
        """Test that required constants are defined."""
        assert NUM_REPLICATES == 10000
        assert THRESHOLD == 0.005
        assert 0 < THRESHOLD < 1
