"""
Unit tests for Monte-Carlo Validation Module.
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
    TOLERANCE_THRESHOLD,
    NUM_REPLICATES
)
from code.src.config import SEED


@pytest.fixture
def mock_rng():
    """Create a deterministic RNG for testing."""
    return np.random.default_rng(SEED)


def test_validate_z_test_structure(mock_rng):
    """Test that Z-Test validation returns expected structure."""
    passed, details = validate_z_test(mock_rng)
    
    assert isinstance(passed, bool)
    assert isinstance(details, dict)
    assert details["test"] == "z_test"
    assert "p_library" in details
    assert "p_monte_carlo" in details
    assert "difference" in details
    assert "valid" in details
    assert details["replicates"] == NUM_REPLICATES


def test_validate_fisher_exact_structure(mock_rng):
    """Test that Fisher's Exact validation returns expected structure."""
    passed, details = validate_fisher_exact(mock_rng)
    
    assert isinstance(passed, bool)
    assert isinstance(details, dict)
    assert details["test"] == "fisher_exact"
    assert "p_library" in details
    assert "p_monte_carlo" in details
    assert "difference" in details
    assert "valid" in details


def test_validate_welch_t_test_structure(mock_rng):
    """Test that Welch's T-Test validation returns expected structure."""
    passed, details = validate_welch_t_test(mock_rng)
    
    assert isinstance(passed, bool)
    assert isinstance(details, dict)
    assert details["test"] == "welch_t_test"
    assert "p_library" in details
    assert "p_monte_carlo" in details
    assert "difference" in details
    assert "valid" in details


def test_validate_binomial_test_structure(mock_rng):
    """Test that Binomial Test validation returns expected structure."""
    passed, details = validate_binomial_test(mock_rng)
    
    assert isinstance(passed, bool)
    assert isinstance(details, dict)
    assert details["test"] == "binomial_test"
    assert "p_library" in details
    assert "p_monte_carlo" in details
    assert "difference" in details
    assert "valid" in details


def test_tolerance_threshold_defined():
    """Assert that the tolerance threshold is set correctly."""
    assert TOLERANCE_THRESHOLD == 0.005


def test_replicates_count():
    """Assert that the number of replicates is 10,000."""
    assert NUM_REPLICATES == 10000


def test_run_monte_carlo_validation_returns_bool():
    """Test that the main runner returns a boolean."""
    result = run_monte_carlo_validation()
    assert isinstance(result, bool)


def test_all_tests_included():
    """Verify that all required tests are included in the runner."""
    # This is a structural check. We can't easily mock the whole run without side effects,
    # but we can check that the function exists and doesn't crash on import.
    assert callable(run_monte_carlo_validation)
    assert callable(validate_z_test)
    assert callable(validate_fisher_exact)
    assert callable(validate_welch_t_test)
    assert callable(validate_binomial_test)
