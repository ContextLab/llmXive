"""
Unit tests for Monte-Carlo validation module.

These tests verify that the Monte-Carlo validation functions
execute correctly and return expected data structures.
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
    main,
    TOLERANCE,
    ALPHA,
)
from code.src.config import SEED


class TestMonteCarloValidation:
    """Tests for Monte-Carlo validation functions."""

    def test_validate_z_test_returns_correct_structure(self):
        """Test that z-test validation returns correct tuple structure."""
        # Use a small number of replicates for speed in unit tests
        passed, empirical, theoretical = validate_z_test(num_replicates=100)

        assert isinstance(passed, bool), "passed should be a boolean"
        assert isinstance(empirical, float), "empirical should be a float"
        assert isinstance(theoretical, float), "theoretical should be a float"
        assert theoretical == ALPHA, "theoretical should equal ALPHA constant"
        assert 0 <= empirical <= 1, "empirical should be between 0 and 1"

    def test_validate_fisher_exact_returns_correct_structure(self):
        """Test that Fisher's exact validation returns correct tuple structure."""
        passed, empirical, theoretical = validate_fisher_exact(num_replicates=100)

        assert isinstance(passed, bool), "passed should be a boolean"
        assert isinstance(empirical, float), "empirical should be a float"
        assert isinstance(theoretical, float), "theoretical should be a float"
        assert theoretical == ALPHA, "theoretical should equal ALPHA constant"

    def test_validate_welch_t_test_returns_correct_structure(self):
        """Test that Welch's t-test validation returns correct tuple structure."""
        passed, empirical, theoretical = validate_welch_t_test(num_replicates=100)

        assert isinstance(passed, bool), "passed should be a boolean"
        assert isinstance(empirical, float), "empirical should be a float"
        assert isinstance(theoretical, float), "theoretical should be a float"
        assert theoretical == ALPHA, "theoretical should equal ALPHA constant"

    def test_validate_binomial_test_returns_correct_structure(self):
        """Test that binomial test validation returns correct tuple structure."""
        passed, empirical, theoretical = validate_binomial_test(num_replicates=100)

        assert isinstance(passed, bool), "passed should be a boolean"
        assert isinstance(empirical, float), "empirical should be a float"
        assert isinstance(theoretical, float), "theoretical should be a float"
        assert theoretical == ALPHA, "theoretical should equal ALPHA constant"

    def test_run_monte_carlo_validation_returns_dict(self):
        """Test that full validation returns a dictionary with expected keys."""
        with patch('code.src.audit.monte_carlo_validation.validate_z_test') as mock_z, \
             patch('code.src.audit.monte_carlo_validation.validate_fisher_exact') as mock_fisher, \
             patch('code.src.audit.monte_carlo_validation.validate_welch_t_test') as mock_welch, \
             patch('code.src.audit.monte_carlo_validation.validate_binomial_test') as mock_binomial:

            # Mock return values
            mock_z.return_value = (True, 0.048, 0.05)
            mock_fisher.return_value = (True, 0.051, 0.05)
            mock_welch.return_value = (True, 0.049, 0.05)
            mock_binomial.return_value = (True, 0.050, 0.05)

            results = run_monte_carlo_validation()

            assert isinstance(results, dict), "Results should be a dictionary"
            assert 'z_test' in results, "Results should contain 'z_test'"
            assert 'fisher_exact' in results, "Results should contain 'fisher_exact'"
            assert 'welch_t_test' in results, "Results should contain 'welch_t_test'"
            assert 'binomial_test' in results, "Results should contain 'binomial_test'"
            assert 'all_passed' in results, "Results should contain 'all_passed'"
            assert results['all_passed'] is True, "all_passed should be True when all tests pass"

    def test_run_monte_carlo_validation_detects_failure(self):
        """Test that full validation detects when a test fails."""
        with patch('code.src.audit.monte_carlo_validation.validate_z_test') as mock_z, \
             patch('code.src.audit.monte_carlo_validation.validate_fisher_exact') as mock_fisher, \
             patch('code.src.audit.monte_carlo_validation.validate_welch_t_test') as mock_welch, \
             patch('code.src.audit.monte_carlo_validation.validate_binomial_test') as mock_binomial:

            # Mock return values with one failure
            mock_z.return_value = (False, 0.08, 0.05)  # Failed (difference > TOLERANCE)
            mock_fisher.return_value = (True, 0.051, 0.05)
            mock_welch.return_value = (True, 0.049, 0.05)
            mock_binomial.return_value = (True, 0.050, 0.05)

            results = run_monte_carlo_validation()

            assert results['all_passed'] is False, "all_passed should be False when a test fails"

    def test_tolerance_check(self):
        """Test that tolerance is correctly applied in validation logic."""
        # This test verifies that the tolerance constant is reasonable
        assert TOLERANCE > 0, "Tolerance should be positive"
        assert TOLERANCE <= 0.1, "Tolerance should be reasonable (<= 0.1)"
        assert TOLERANCE == 0.005, "Tolerance should be 0.005 as per FR-026"

    def test_alpha_constant(self):
        """Test that ALPHA constant is set correctly."""
        assert ALPHA == 0.05, "ALPHA should be 0.05"

    @pytest.mark.slow
    def test_full_validation_with_real_replicates(self):
        """
        Test full validation with actual replicates (slow).

        This test is marked as slow and should be run separately
        during integration testing.
        """
        results = run_monte_carlo_validation()

        # Verify structure
        assert 'all_passed' in results
        assert isinstance(results['all_passed'], bool)

        # Each test should have passed, empirical_alpha, and theoretical_alpha
        for test_name in ['z_test', 'fisher_exact', 'welch_t_test', 'binomial_test']:
            assert test_name in results
            assert 'passed' in results[test_name]
            assert 'empirical_alpha' in results[test_name]
            assert 'theoretical_alpha' in results[test_name]

class TestMainFunction:
    """Tests for the main() entry point."""

    def test_main_returns_zero_on_success(self):
        """Test that main() returns 0 when all validations pass."""
        with patch('code.src.audit.monte_carlo_validation.run_monte_carlo_validation') as mock_run:
            mock_run.return_value = {'all_passed': True}

            result = main()
            assert result == 0, "main() should return 0 on success"

    def test_main_returns_nonzero_on_failure(self):
        """Test that main() returns non-zero when validation fails."""
        with patch('code.src.audit.monte_carlo_validation.run_monte_carlo_validation') as mock_run:
            mock_run.return_value = {'all_passed': False}

            result = main()
            assert result == 1, "main() should return 1 on failure"

    def test_main_handles_exceptions(self):
        """Test that main() returns 2 on exception."""
        with patch('code.src.audit.monte_carlo_validation.run_monte_carlo_validation') as mock_run:
            mock_run.side_effect = Exception("Test error")

            result = main()
            assert result == 2, "main() should return 2 on exception"
