"""
Unit tests for Monte-Carlo validation module.
"""

import pytest
import sys
from pathlib import Path
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.audit.monte_carlo_validation import (
    validate_z_test,
    validate_fisher_exact,
    validate_welch_t_test,
    validate_binomial_test,
    run_monte_carlo_validation
)


class TestMonteCarloValidation:
    """Test suite for Monte-Carlo validation functions."""

    def test_validate_z_test_returns_tuple(self):
        """Test that z-test validation returns a tuple of (bool, dict)."""
        passed, details = validate_z_test(seed=42)
        assert isinstance(passed, bool)
        assert isinstance(details, dict)
        assert "test" in details
        assert details["test"] == "z_test"
        assert "passed" in details
        assert "difference" in details
        assert "threshold" in details

    def test_validate_z_test_structure(self):
        """Test that z-test validation result has expected structure."""
        passed, details = validate_z_test(seed=42)
        required_keys = ["test", "replicates", "empirical_alpha", "theoretical_alpha",
                       "difference", "threshold", "passed", "seed"]
        for key in required_keys:
            assert key in details, f"Missing key: {key}"

    def test_validate_fisher_exact_returns_tuple(self):
        """Test that Fisher's exact validation returns a tuple of (bool, dict)."""
        passed, details = validate_fisher_exact(seed=42)
        assert isinstance(passed, bool)
        assert isinstance(details, dict)
        assert details["test"] == "fisher_exact"

    def test_validate_welch_t_test_returns_tuple(self):
        """Test that Welch's t-test validation returns a tuple of (bool, dict)."""
        passed, details = validate_welch_t_test(seed=42)
        assert isinstance(passed, bool)
        assert isinstance(details, dict)
        assert details["test"] == "welch_t"

    def test_validate_binomial_test_returns_tuple(self):
        """Test that binomial test validation returns a tuple of (bool, dict)."""
        passed, details = validate_binomial_test(seed=42)
        assert isinstance(passed, bool)
        assert isinstance(details, dict)
        assert details["test"] == "binomial"

    def test_run_monte_carlo_validation_all_tests(self):
        """Test that running full validation suite returns results for all tests."""
        passed, results = run_monte_carlo_validation(seed=42)
        assert isinstance(passed, bool)
        assert isinstance(results, dict)
        assert "tests" in results
        assert "z_test" in results["tests"]
        assert "fisher_exact" in results["tests"]
        assert "welch_t" in results["tests"]
        assert "binomial" in results["tests"]
        assert "all_passed" in results

    def test_tolerance_threshold_applied(self):
        """Test that the tolerance threshold is correctly applied."""
        _, details = validate_z_test(seed=42)
        assert details["threshold"] == 0.005
        # Difference should be a float
        assert isinstance(details["difference"], float)

    def test_replicates_count(self):
        """Test that the correct number of replicates is used."""
        _, details = validate_z_test(seed=42)
        assert details["replicates"] == 100000

    def test_seed_reproducibility(self):
        """Test that using the same seed produces consistent results."""
        _, details1 = validate_z_test(seed=123)
        _, details2 = validate_z_test(seed=123)
        # The difference values should be identical (or very close due to float precision)
        assert abs(details1["difference"] - details2["difference"]) < 1e-10

    def test_empirical_alpha_reasonable_range(self):
        """Test that empirical alpha is within a reasonable range."""
        _, details = validate_z_test(seed=42)
        # Under null, empirical alpha should be close to 0.05
        # Allow some variance due to Monte-Carlo simulation
        assert 0.0 < details["empirical_alpha"] < 0.15, \
            f"empirical_alpha {details['empirical_alpha']} out of expected range"

    def test_difference_is_absolute(self):
        """Test that difference is always non-negative (absolute difference)."""
        _, details = validate_z_test(seed=42)
        assert details["difference"] >= 0, "Difference should be absolute (non-negative)"