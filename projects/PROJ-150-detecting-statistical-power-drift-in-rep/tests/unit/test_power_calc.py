"""
Unit tests for power calculation logic, specifically handling of NaN values.
This module tests the behavior of power calculation functions when encountering
invalid or missing data points (NaN).
"""

import numpy as np
import pytest
from scipy import stats

# Helper function mimicking the core power calculation logic
# This represents the logic that would be in code/power_calc.py (to be implemented later)
def calculate_power(effect_size, sample_size, alpha=0.05):
    """
    Calculate statistical power for a two-sample t-test.
    
    Parameters:
    -----------
    effect_size : float
        Cohen's d effect size.
    sample_size : int or float
        Number of observations per group.
    alpha : float
        Significance level (default 0.05).
        
    Returns:
    --------
    float
        Calculated power (probability of rejecting null hypothesis).
        Returns np.nan if inputs are invalid.
    """
    # Handle NaN inputs explicitly
    if np.isnan(effect_size) or np.isnan(sample_size) or np.isnan(alpha):
        return np.nan
    
    # Handle zero or negative sample size
    if sample_size <= 0:
        return np.nan
    
    # Calculate non-centrality parameter
    # For two-sample t-test: ncp = d * sqrt(n/2)
    ncp = effect_size * np.sqrt(sample_size / 2)
    
    # Critical t-value
    df = 2 * sample_size - 2
    if df <= 0:
        return np.nan
        
    t_crit = stats.t.ppf(1 - alpha/2, df)
    
    # Power calculation using non-central t-distribution
    # Power = P(|T| > t_crit | H1 is true)
    power = 1 - stats.nct.cdf(t_crit, df, ncp) + stats.nct.cdf(-t_crit, df, ncp)
    
    return power

def test_power_calc_handles_nan():
    """
    Test that power calculation returns NaN when any input is NaN.
    
    This test verifies FR-008 (Error handling for missing data) by ensuring
    that NaN values in effect_size, sample_size, or alpha result in NaN output
    rather than causing an exception or producing garbage values.
    """
    # Test case 1: NaN in effect_size
    result = calculate_power(np.nan, sample_size=30, alpha=0.05)
    assert np.isnan(result), f"Expected NaN for NaN effect_size, got {result}"
    
    # Test case 2: NaN in sample_size
    result = calculate_power(effect_size=0.5, sample_size=np.nan, alpha=0.05)
    assert np.isnan(result), f"Expected NaN for NaN sample_size, got {result}"
    
    # Test case 3: NaN in alpha
    result = calculate_power(effect_size=0.5, sample_size=30, alpha=np.nan)
    assert np.isnan(result), f"Expected NaN for NaN alpha, got {result}"
    
    # Test case 4: Multiple NaNs
    result = calculate_power(np.nan, sample_size=np.nan, alpha=np.nan)
    assert np.isnan(result), f"Expected NaN for multiple NaN inputs, got {result}"
    
    # Test case 5: Valid inputs should NOT return NaN
    result = calculate_power(effect_size=0.5, sample_size=30, alpha=0.05)
    assert not np.isnan(result), f"Expected valid power for valid inputs, got NaN"
    assert 0 <= result <= 1, f"Power should be between 0 and 1, got {result}"
    
    # Test case 6: Zero sample size (edge case)
    result = calculate_power(effect_size=0.5, sample_size=0, alpha=0.05)
    assert np.isnan(result), f"Expected NaN for zero sample_size, got {result}"
    
    # Test case 7: Negative sample size (edge case)
    result = calculate_power(effect_size=0.5, sample_size=-10, alpha=0.05)
    assert np.isnan(result), f"Expected NaN for negative sample_size, got {result}"

def test_power_calc_valid_inputs():
    """
    Test power calculation with valid inputs to ensure correctness.
    """
    # Standard case: medium effect size, reasonable sample
    result = calculate_power(effect_size=0.5, sample_size=64, alpha=0.05)
    assert 0 <= result <= 1
    assert result > 0.8, "Power should be high for medium effect and n=64"
    
    # Large effect size
    result = calculate_power(effect_size=0.8, sample_size=30, alpha=0.05)
    assert 0 <= result <= 1
    
    # Small effect size
    result = calculate_power(effect_size=0.2, sample_size=30, alpha=0.05)
    assert 0 <= result <= 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
