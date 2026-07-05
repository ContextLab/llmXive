"""
Unit tests for Monte-Carlo Validation Module.
Verifies that the module functions are importable and run without error.
"""
import pytest
import sys
from unittest.mock import patch, MagicMock
import numpy as np

# Import the module
from code.src.audit.monte_carlo_validation import (
    validate_z_test,
    validate_fisher_exact,
    validate_welch_t_test,
    validate_binomial_test,
    run_monte_carlo_validation
)
from code.src.config import set_rng_seed

class TestMonteCarloValidation:
    
    def test_validate_z_test_import_and_structure(self):
        """Test that validate_z_test returns expected tuple structure."""
        # We don't run the full 100k reps here to save time in unit tests,
        # but we verify the function exists and returns the right type.
        # We will mock the heavy lifting or run a tiny subset if needed.
        # For this unit test, we assume the function signature is correct.
        # To be safe and fast, we just check importability and return type shape
        # by mocking the internal heavy calls if necessary, but since we need
        # to verify logic, we'll run a small subset if the function allows,
        # or just check the return type if we mock the simulation.
        
        # Actually, let's just ensure it doesn't crash with a small mock
        # But the function is self-contained. Let's run it with a mocked NUM_REPLICATES?
        # No, we can't easily mock global constants inside.
        # Instead, we verify the logic by checking the return type.
        # We will run the function but with a much smaller N for the test?
        # The function uses global NUM_REPLICATES.
        # We will patch the global constant.
        
        with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', 10):
            passed, s_p, e_p, result = validate_z_test()
            assert isinstance(passed, bool)
            assert isinstance(s_p, float)
            assert isinstance(e_p, float)
            assert isinstance(result, dict)
            assert "test" in result
            assert result["test"] == "z_test"

    def test_validate_fisher_exact_import_and_structure(self):
        with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', 10):
            passed, s_p, e_p, result = validate_fisher_exact()
            assert isinstance(passed, bool)
            assert isinstance(s_p, float)
            assert isinstance(e_p, float)
            assert isinstance(result, dict)
            assert result["test"] == "fisher_exact"

    def test_validate_welch_t_test_import_and_structure(self):
        with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', 10):
            passed, s_p, e_p, result = validate_welch_t_test()
            assert isinstance(passed, bool)
            assert isinstance(s_p, float)
            assert isinstance(e_p, float)
            assert isinstance(result, dict)
            assert result["test"] == "welch_t"

    def test_validate_binomial_test_import_and_structure(self):
        with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', 10):
            passed, s_p, e_p, result = validate_binomial_test()
            assert isinstance(passed, bool)
            assert isinstance(s_p, float)
            assert isinstance(e_p, float)
            assert isinstance(result, dict)
            assert result["test"] == "binomial"

    def test_run_monte_carlo_validation(self):
        """Test the main runner function."""
        # Patch replicates to be small for speed
        with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', 10):
            # Note: With only 10 replicates, the p-value estimation is noisy and might fail the tolerance check.
            # This test verifies the runner logic, not the statistical validity with 10 samples.
            # We expect it to run without crashing.
            try:
                result = run_monte_carlo_validation()
                # It returns a boolean. It might be False due to low N, but it should run.
                assert isinstance(result, bool)
            except Exception as e:
                pytest.fail(f"run_monte_carlo_validation raised an exception: {e}")

    def test_tolerance_constant_exists(self):
        from code.src.audit.monte_carlo_validation import TOLERANCE
        assert TOLERANCE == 0.005

    def test_replicates_constant_exists(self):
        from code.src.audit.monte_carlo_validation import NUM_REPLICATES
        assert NUM_REPLICATES == 100000
