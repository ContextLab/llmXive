"""
Unit tests for Monte-Carlo validation module.

These tests verify that the Monte-Carlo validation functions
execute correctly and return expected data structures.
"""

import pytest
import numpy as np
from pathlib import Path
import json
import tempfile

from code.src.audit.monte_carlo_validation import (
    validate_z_test,
    validate_fisher_exact,
    validate_welch_t_test,
    validate_binomial_test,
    run_monte_carlo_validation,
    NUM_REPLICATES,
    TOLERANCE,
)
from code.src.config import SEED


class TestMonteCarloValidation:
    """Tests for Monte-Carlo validation functions."""

    def test_validate_z_test_returns_correct_structure(self):
        """Verify z-test validation returns expected tuple structure."""
        passed, emp_p, theo_p, details = validate_z_test(n_replicates=100, seed=SEED)

        assert isinstance(passed, bool)
        assert isinstance(emp_p, float)
        assert isinstance(theo_p, float)
        assert isinstance(details, dict)

        # Check required keys in details
        required_keys = [
            "test_type", "n_replicates", "sample_sizes",
            "true_proportions", "alpha", "empirical_error_rate",
            "theoretical_error_rate", "absolute_difference", "passed"
        ]
        for key in required_keys:
            assert key in details

        assert details["test_type"] == "z_test"
        assert details["n_replicates"] == 100
        assert abs(details["theoretical_error_rate"] - 0.05) < 0.001

    def test_validate_fisher_exact_returns_correct_structure(self):
        """Verify Fisher's exact test validation returns expected tuple structure."""
        passed, emp_p, theo_p, details = validate_fisher_exact(n_replicates=100, seed=SEED)

        assert isinstance(passed, bool)
        assert isinstance(emp_p, float)
        assert isinstance(theo_p, float)
        assert isinstance(details, dict)

        assert details["test_type"] == "fisher_exact"
        assert details["n_replicates"] == 100

    def test_validate_welch_t_test_returns_correct_structure(self):
        """Verify Welch's t-test validation returns expected tuple structure."""
        passed, emp_p, theo_p, details = validate_welch_t_test(n_replicates=100, seed=SEED)

        assert isinstance(passed, bool)
        assert isinstance(emp_p, float)
        assert isinstance(theo_p, float)
        assert isinstance(details, dict)

        assert details["test_type"] == "welch_t_test"
        assert details["n_replicates"] == 100

    def test_validate_binomial_test_returns_correct_structure(self):
        """Verify binomial test validation returns expected tuple structure."""
        passed, emp_p, theo_p, details = validate_binomial_test(n_replicates=100, seed=SEED)

        assert isinstance(passed, bool)
        assert isinstance(emp_p, float)
        assert isinstance(theo_p, float)
        assert isinstance(details, dict)

        assert details["test_type"] == "binomial_test"
        assert details["n_replicates"] == 100

    def test_run_monte_carlo_validation_returns_bool(self):
        """Verify run_monte_carlo_validation returns a boolean."""
        result = run_monte_carlo_validation(n_replicates=50, seed=SEED)
        assert isinstance(result, bool)

    def test_run_monte_carlo_validation_writes_output(self):
        """Verify run_monte_carlo_validation writes output file when path provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_results.json"
            run_monte_carlo_validation(n_replicates=50, seed=SEED, output_path=output_path)

            assert output_path.exists()

            with open(output_path, 'r') as f:
                data = json.load(f)

            assert "all_passed" in data
            assert "test_results" in data
            assert len(data["test_results"]) == 4  # 4 test types

    def test_tolerance_constant_is_correct(self):
        """Verify TOLERANCE constant is set to 0.005."""
        assert TOLERANCE == 0.005

    def test_num_replicates_constant_is_correct(self):
        """Verify NUM_REPLICATES constant is set to 10000."""
        assert NUM_REPLICATES == 10000

    def test_deterministic_with_seed(self):
        """Verify results are deterministic when using the same seed."""
        # Run twice with same seed
        result1 = validate_z_test(n_replicates=50, seed=42)
        result2 = validate_z_test(n_replicates=50, seed=42)

        # Empirical error rates should be identical
        assert result1[1] == result2[1]
        assert result1[3]["empirical_error_rate"] == result2[3]["empirical_error_rate"]
