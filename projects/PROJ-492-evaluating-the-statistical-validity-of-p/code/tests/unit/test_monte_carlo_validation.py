"""
Unit tests for Monte-Carlo validation module.
"""
import pytest
import sys
from pathlib import Path
import logging

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.audit.monte_carlo_validation import (
    validate_z_test,
    validate_fisher_exact,
    validate_welch_t_test,
    validate_binomial_test,
    run_monte_carlo_validation,
    TOLERANCE,
    NUM_REPLICATES
)
from code.src.utils.logger import get_default_logger, AuditLogger

@pytest.fixture
def logger():
    return get_default_logger()

def test_validate_z_test_structure(logger):
    """Test that z-test validation returns correct structure."""
    passed, empirical_p, library_p, details = validate_z_test(logger)
    
    assert isinstance(passed, bool)
    assert isinstance(empirical_p, float)
    assert isinstance(library_p, float)
    assert isinstance(details, dict)
    assert "z-test" in details["test"]
    assert details["replicates"] == NUM_REPLICATES
    assert "difference" in details
    assert "tolerance" in details
    assert abs(details["difference"]) <= 1.0  # P-values are between 0 and 1

def test_validate_fisher_exact_structure(logger):
    """Test that Fisher's exact validation returns correct structure."""
    passed, empirical_p, library_p, details = validate_fisher_exact(logger)
    
    assert isinstance(passed, bool)
    assert isinstance(empirical_p, float)
    assert isinstance(library_p, float)
    assert isinstance(details, dict)
    assert "fisher_exact" in details["test"]
    assert details["replicates"] == NUM_REPLICATES

def test_validate_welch_t_test_structure(logger):
    """Test that Welch's t-test validation returns correct structure."""
    passed, empirical_p, library_p, details = validate_welch_t_test(logger)
    
    assert isinstance(passed, bool)
    assert isinstance(empirical_p, float)
    assert isinstance(library_p, float)
    assert isinstance(details, dict)
    assert "welch_t" in details["test"]
    assert details["replicates"] == NUM_REPLICATES

def test_validate_binomial_test_structure(logger):
    """Test that binomial test validation returns correct structure."""
    passed, empirical_p, library_p, details = validate_binomial_test(logger)
    
    assert isinstance(passed, bool)
    assert isinstance(empirical_p, float)
    assert isinstance(library_p, float)
    assert isinstance(details, dict)
    assert "binomial" in details["test"]
    assert details["replicates"] == NUM_REPLICATES

def test_tolerance_check(logger):
    """Test that the tolerance check is applied correctly."""
    # Run one test and verify the difference is within tolerance (or at least calculated)
    passed, _, _, details = validate_z_test(logger)
    
    diff = details["difference"]
    tol = details["tolerance"]
    
    # The test should pass if diff <= tol
    assert passed == (diff <= tol)

def test_run_monte_carlo_validation_returns_dict():
    """Test that the full validation suite returns a dictionary."""
    results = run_monte_carlo_validation()
    
    assert isinstance(results, dict)
    assert "overall_passed" in results
    assert "tests" in results
    assert "z_test" in results["tests"]
    assert "fisher_exact" in results["tests"]
    assert "welch_t" in results["tests"]
    assert "binomial" in results["tests"]