"""
Unit tests for Monte-Carlo Validation Module (T062)
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
    TOLERANCE
)
from code.src.config import SEED

@pytest.fixture(autouse=True)
def set_seed():
    np.random.seed(SEED)
    yield

def test_validate_z_test_structure():
    """Test that z-test validation returns expected structure"""
    # Run with fewer replicates for speed in unit test
    # We can't easily change NUM_REPLICATES in the function, so we test the return structure
    # by mocking the heavy loop or just running a small subset if possible.
    # For now, we test that the function returns a tuple of (bool, float, float, dict)
    # We will patch the loop to run 0 times or 1 time to check structure?
    # No, let's just run it. It might take a few seconds.
    # To speed up, we can't easily change NUM_REPLICATES.
    # Let's assume the function is correct if it returns the right types.
    # We will run a small test by patching the loop range.
    
    with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', 10):
        with patch('code.src.audit.monte_carlo_validation.set_seeds'):
            passed, mean_sim, mean_lib, details = validate_z_test()
            assert isinstance(passed, bool)
            assert isinstance(mean_sim, float)
            assert isinstance(mean_lib, float)
            assert isinstance(details, dict)

def test_validate_fisher_exact_structure():
    """Test that Fisher's exact validation returns expected structure"""
    with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', 10):
        with patch('code.src.audit.monte_carlo_validation.set_seeds'):
            passed, mean_sim, mean_lib, details = validate_fisher_exact()
            assert isinstance(passed, bool)
            assert isinstance(mean_sim, float)
            assert isinstance(mean_lib, float)
            assert isinstance(details, dict)

def test_validate_welch_t_test_structure():
    """Test that Welch's t-test validation returns expected structure"""
    with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', 10):
        with patch('code.src.audit.monte_carlo_validation.set_seeds'):
            passed, mean_sim, mean_lib, details = validate_welch_t_test()
            assert isinstance(passed, bool)
            assert isinstance(mean_sim, float)
            assert isinstance(mean_lib, float)
            assert isinstance(details, dict)

def test_validate_binomial_test_structure():
    """Test that Binomial test validation returns expected structure"""
    with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', 10):
        with patch('code.src.audit.monte_carlo_validation.set_seeds'):
            passed, mean_sim, mean_lib, details = validate_binomial_test()
            assert isinstance(passed, bool)
            assert isinstance(mean_sim, float)
            assert isinstance(mean_lib, float)
            assert isinstance(details, dict)

def test_run_monte_carlo_validation():
    """Test the main runner function"""
    with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', 5):
        with patch('code.src.audit.monte_carlo_validation.set_seeds'):
            # Patch individual validators to return known values
            with patch('code.src.audit.monte_carlo_validation.validate_z_test') as mock_z:
                with patch('code.src.audit.monte_carlo_validation.validate_fisher_exact') as mock_f:
                    with patch('code.src.audit.monte_carlo_validation.validate_welch_t_test') as mock_w:
                        with patch('code.src.audit.monte_carlo_validation.validate_binomial_test') as mock_b:
                            
                            mock_z.return_value = (True, 0.5, 0.5, {})
                            mock_f.return_value = (True, 0.5, 0.5, {})
                            mock_w.return_value = (True, 0.5, 0.5, {})
                            mock_b.return_value = (True, 0.5, 0.5, {})
                            
                            results = run_monte_carlo_validation()
                            
                            assert results['all_passed'] is True
                            assert 'tests' in results
                            assert 'z_test' in results['tests']
                            assert results['tests']['z_test']['passed'] is True

def test_run_monte_carlo_validation_failure():
    """Test the main runner function when a test fails"""
    with patch('code.src.audit.monte_carlo_validation.NUM_REPLICATES', 5):
        with patch('code.src.audit.monte_carlo_validation.set_seeds'):
            with patch('code.src.audit.monte_carlo_validation.validate_z_test') as mock_z:
                with patch('code.src.audit.monte_carlo_validation.validate_fisher_exact') as mock_f:
                    with patch('code.src.audit.monte_carlo_validation.validate_welch_t_test') as mock_w:
                        with patch('code.src.audit.monte_carlo_validation.validate_binomial_test') as mock_b:
                            
                            mock_z.return_value = (False, 0.1, 0.5, {'diff': 0.4})
                            mock_f.return_value = (True, 0.5, 0.5, {})
                            mock_w.return_value = (True, 0.5, 0.5, {})
                            mock_b.return_value = (True, 0.5, 0.5, {})
                            
                            results = run_monte_carlo_validation()
                            
                            assert results['all_passed'] is False
                            assert results['tests']['z_test']['passed'] is False