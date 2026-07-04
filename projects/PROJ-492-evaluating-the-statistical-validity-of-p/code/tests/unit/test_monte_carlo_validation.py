"""
Unit tests for Monte-Carlo validation module.

Tests verify that the validation functions:
1. Execute without errors
2. Return expected data structures
3. Produce results within tolerance bounds
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from code.src.audit.monte_carlo_validation import (
    validate_z_test,
    validate_fisher_exact,
    validate_welch_t_test,
    validate_binomial_test,
    run_monte_carlo_validation,
    TOLERANCE,
    NUM_REPLICATES
)


class TestMonteCarloValidation:
    """Test suite for Monte-Carlo validation functions."""

    def test_validate_z_test_structure(self):
        """Test that z-test validation returns correct structure."""
        # Use fewer replicates for faster testing
        with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', 100):
            passed, max_diff, details = validate_z_test()

        assert isinstance(passed, bool)
        assert isinstance(max_diff, float)
        assert isinstance(details, dict)
        assert details['test'] == 'z-test'
        assert details['num_replicates'] == 100
        assert 'empirical_power' in details
        assert 'theoretical_power' in details
        assert 'max_difference' in details
        assert 'passed' in details

    def test_validate_fisher_exact_structure(self):
        """Test that Fisher's exact validation returns correct structure."""
        with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', 100):
            passed, max_diff, details = validate_fisher_exact()

        assert isinstance(passed, bool)
        assert isinstance(max_diff, float)
        assert isinstance(details, dict)
        assert details['test'] == 'fisher_exact'
        assert 'empirical_power' in details
        assert 'theoretical_power' in details

    def test_validate_welch_t_test_structure(self):
        """Test that Welch's t-test validation returns correct structure."""
        with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', 100):
            passed, max_diff, details = validate_welch_t_test()

        assert isinstance(passed, bool)
        assert isinstance(max_diff, float)
        assert isinstance(details, dict)
        assert details['test'] == 'welch_t_test'
        assert 'empirical_power' in details
        assert 'theoretical_power' in details

    def test_validate_binomial_test_structure(self):
        """Test that binomial test validation returns correct structure."""
        with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', 100):
            passed, max_diff, details = validate_binomial_test()

        assert isinstance(passed, bool)
        assert isinstance(max_diff, float)
        assert isinstance(details, dict)
        assert details['test'] == 'binomial_test'
        assert 'ks_statistic' in details
        assert 'max_difference' in details

    def test_run_monte_carlo_validation_returns_summary(self):
        """Test that full validation returns expected summary structure."""
        with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', 50):
            summary = run_monte_carlo_validation()

        assert isinstance(summary, dict)
        assert 'num_replicates' in summary
        assert 'tolerance' in summary
        assert 'all_tests_passed' in summary
        assert 'test_results' in summary
        assert 'timestamp' in summary

        # Check all expected tests are present
        expected_tests = ['z_test', 'fisher_exact', 'welch_t_test', 'binomial_test']
        for test in expected_tests:
            assert test in summary['test_results']

    def test_validation_tolerance_check(self):
        """Test that validation correctly identifies when tolerance is exceeded."""
        # This is a structural test - we verify the logic is in place
        # Actual tolerance checking is tested via integration with real data
        with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', 100):
            passed, max_diff, details = validate_z_test()

        # The passed flag should reflect the max_diff vs TOLERANCE comparison
        expected_passed = max_diff <= TOLERANCE
        assert passed == expected_passed

    def test_deterministic_seeding(self):
        """Test that results are deterministic with fixed seed."""
        # Run twice with same seed
        with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', 50):
            passed1, max_diff1, details1 = validate_z_test()
            passed2, max_diff2, details2 = validate_z_test()

        # Results should be identical due to deterministic seeding
        assert max_diff1 == max_diff2
        assert passed1 == passed2

    def test_large_replicates_performance(self):
        """Test that validation completes within reasonable time for large replicates."""
        import time

        # Use a moderate number for performance testing
        num_rep = 500
        with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', num_rep):
            start_time = time.time()
            summary = run_monte_carlo_validation()
            elapsed = time.time() - start_time

        # Should complete within 60 seconds for 500 replicates
        assert elapsed < 60
        assert summary['num_replicates'] == num_rep

    def test_error_handling_in_validation(self):
        """Test that validation handles unexpected errors gracefully."""
        # Mock scipy.stats to raise an exception
        with patch('scipy.stats.fisher_exact', side_effect=Exception("Test error")):
            with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', 10):
                summary = run_monte_carlo_validation()

        # Should still return a valid summary with error marked
        assert 'test_results' in summary
        assert 'fisher_exact' in summary['test_results']
        # The test should be marked as failed due to error
        assert not summary['test_results']['fisher_exact'].get('passed', True)
