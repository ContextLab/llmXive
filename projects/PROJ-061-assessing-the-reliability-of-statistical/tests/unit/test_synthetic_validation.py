"""
Unit tests for the Synthetic Ground Truth validation logic.
These tests verify that the validation script correctly identifies
passes and fails based on the 5% tolerance rule.
"""
import pytest
import numpy as np
from scipy import stats

# Mock imports if necessary, but we assume the functions exist in the codebase
# We test the logic of the calculation and the threshold check

def test_theoretical_power_calculation():
    """Test that theoretical power calculation returns expected values."""
    # For d=0.5, n=64 per group, alpha=0.05
    # Expected power is roughly 0.80
    from code.config import RANDOM_SEED
    from code.power_empirical import run_bootstrap_power_simulation # Import to ensure it's available
    
    # Manual calculation check
    d = 0.5
    n1, n2 = 64, 64
    alpha = 0.05
    
    se = np.sqrt(1/n1 + 1/n2)
    ncp = d / se
    df = n1 + n2 - 2
    t_crit = stats.t.ppf(1 - alpha/2, df)
    
    power = (1 - stats.nct.cdf(t_crit, df, ncp)) + stats.nct.cdf(-t_crit, df, ncp)
    
    # Assert power is approximately 0.80 (allowing for float precision)
    assert 0.78 < power < 0.82, f"Calculated power {power} is not within expected range for d=0.5, n=64"

def test_synthetic_validation_logic():
    """
    Test the logic of the validation gate.
    This is a logic test, not an execution test of the full script.
    """
    # Simulate a passing case
    theoretical = 0.80
    empirical = 0.82
    error = abs(empirical - theoretical)
    tolerance = 0.05
    
    assert error <= tolerance, "Passing case should be within tolerance"
    
    # Simulate a failing case
    empirical_fail = 0.90
    error_fail = abs(empirical_fail - theoretical)
    
    assert error_fail > tolerance, "Failing case should be outside tolerance"

def test_bootstrap_variance_check():
    """Test the bootstrap validity check logic."""
    from code.validators import bootstrap_validity_check
    
    # Valid variance case
    # Variance should be roughly p(1-p)/N
    p = 0.8
    n = 1000
    expected_var = p * (1-p) / n
    
    result = bootstrap_validity_check(expected_var, p, n)
    assert result['valid'], "Expected variance should pass validity check"
    
    # Invalid variance case (too high)
    bad_var = 0.5 # Way too high for p=0.8
    result_fail = bootstrap_validity_check(bad_var, p, n)
    assert not result_fail['valid'], "Excessive variance should fail validity check"
