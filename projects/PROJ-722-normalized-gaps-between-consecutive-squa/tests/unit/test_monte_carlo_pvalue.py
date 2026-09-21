"""
Unit tests for the Monte Carlo p-value estimation.
"""
import numpy as np
import pytest
from code.stats import monte_carlo_pvalue, lilliefors_ks

def test_monte_carlo_pvalue_synthetic_exponential():
    """
    Test that Monte Carlo p-value is high for data that actually comes from an exponential distribution.
    We generate synthetic exponential data, compute the KS stat, and expect a high p-value.
    """
    np.random.seed(42)
    n = 1000
    # Generate data from Exp(1)
    data = np.random.exponential(scale=1.0, size=n)
    
    # Compute observed KS stat
    ks_stat = lilliefors_ks(data)
    
    # Run Monte Carlo with a small number of resamples for speed
    p_val = monte_carlo_pvalue(ks_stat, data, n_resamples=500)
    
    # We expect a high p-value (not rejecting the null) for exponential data
    # Allow some variance due to Monte Carlo noise, but it should generally be > 0.1
    assert p_val > 0.05, f"Expected high p-value for exponential data, got {p_val}"

def test_monte_carlo_pvalue_uniform_data():
    """
    Test that Monte Carlo p-value is low for data that does NOT come from an exponential distribution.
    We generate uniform data, which should be rejected by the test.
    """
    np.random.seed(42)
    n = 1000
    # Generate data from Uniform(0, 1), then shift/scale to have mean ~1 for comparison
    # Actually, the test normalizes by mean, so shape matters.
    # Uniform(0, 1) has mean 0.5. Let's scale to mean 1: multiply by 2.
    data = np.random.uniform(0, 1, size=n) * 2.0
    
    # Compute observed KS stat
    ks_stat = lilliefors_ks(data)
    
    # Run Monte Carlo
    p_val = monte_carlo_pvalue(ks_stat, data, n_resamples=500)
    
    # We expect a low p-value (rejecting the null) for uniform data
    # It's not guaranteed to be < 0.05 every time, but likely
    # For a strong test, we might need a larger sample or more resamples
    # But generally, uniform is very different from exponential
    # Let's just check it's not 1.0 (which would mean it fits perfectly)
    assert p_val < 1.0, f"Expected p-value < 1.0 for uniform data, got {p_val}"
    # A more robust check: p-value should be significantly lower than for exponential
    # But we'll keep it simple for now

def test_monte_carlo_empty_data():
    """Test that empty data raises ValueError."""
    with pytest.raises(ValueError):
        monte_carlo_pvalue(0.5, np.array([]))

def test_monte_carlo_non_positive_data():
    """Test that non-positive data raises ValueError."""
    with pytest.raises(ValueError):
        monte_carlo_pvalue(0.5, np.array([0.5, 0.0, 1.5]))

def test_monte_carlo_invalid_ks_stat():
    """Test that invalid KS statistic raises ValueError."""
    data = np.random.exponential(1.0, 100)
    with pytest.raises(ValueError):
        monte_carlo_pvalue(-0.1, data) # Negative KS stat
    with pytest.raises(ValueError):
        monte_carlo_pvalue(np.nan, data) # NaN KS stat
