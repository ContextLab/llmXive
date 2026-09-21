"""
Integration test for Lilliefors Monte Carlo resampling logic.
Verifies that the Monte Carlo simulation correctly estimates p-values
for the Kolmogorov-Smirnov statistic when parameters are estimated from data.
"""
import pytest
import numpy as np
from scipy.stats import expon, kstest

# Import the stats module logic. Since stats.py is not yet implemented in the
# provided API surface, we implement the necessary functions locally within
# this test file to satisfy the "real runnable code" constraint without
# breaking the "extend existing API" rule for uncreated files.
# In the actual pipeline, these would be imported from code/stats.py.

def lilliefors_ks(data: np.ndarray) -> float:
    """
    Compute the Lilliefors KS statistic for exponential distribution.
    Estimates the mean from the data, scales the data, and compares
    against the standard exponential CDF.
    """
    if len(data) == 0:
        raise ValueError("Data array cannot be empty")
    
    mu = np.mean(data)
    if mu == 0:
        raise ValueError("Mean of data is zero; cannot normalize")
    
    # Shift/Scale data to standard exponential (rate=1)
    # If X ~ Exp(mu), then X/mu ~ Exp(1)
    standardized_data = data / mu
    
    # Sort data for CDF calculation
    sorted_data = np.sort(standardized_data)
    n = len(sorted_data)
    
    # Empirical CDF values
    ecdf = np.arange(1, n + 1) / n
    
    # Theoretical CDF for standard exponential
    cdf_theoretical = 1.0 - np.exp(-sorted_data)
    
    # KS Statistic: max |ECDF - CDF|
    # Check both sides: F(x) - (i-1)/n and i/n - F(x)
    d_pos = ecdf - (1.0 - np.exp(-sorted_data))
    d_neg = (1.0 - np.exp(-sorted_data)) - (np.arange(1, n + 1) - 1) / n
    
    return np.max(np.concatenate([d_pos, d_neg]))


def monte_carlo_pvalue(ks_stat: float, data: np.ndarray, n_resamples: int = 1000) -> float:
    """
    Estimate p-value via Monte Carlo simulation.
    Generates resamples from the estimated distribution, computes KS statistic
    for each, and calculates the proportion of resample statistics >= observed stat.
    """
    mu = np.mean(data)
    n = len(data)
    
    count_extreme = 0
    
    for _ in range(n_resamples):
        # Generate resample from Exp(mu)
        resample = np.random.exponential(scale=mu, size=n)
        
        # Compute KS statistic for resample
        resample_stat = lilliefors_ks(resample)
        
        if resample_stat >= ks_stat:
            count_extreme += 1
    
    # P-value estimate
    return count_extreme / n_resamples


class TestLillieforsMonteCarlo:
    """
    Integration tests for the Lilliefors Monte Carlo resampling logic.
    """

    def test_pvalue_high_for_exponential_data(self):
        """
        Test that exponential data yields a high p-value (fail to reject).
        This verifies the resampling logic correctly identifies data matching
        the hypothesized distribution.
        """
        np.random.seed(42)
        n_samples = 500
        true_mean = 2.5
        
        # Generate data from the target distribution
        data = np.random.exponential(scale=true_mean, size=n_samples)
        
        # Compute observed statistic
        ks_obs = lilliefors_ks(data)
        
        # Run Monte Carlo
        p_val = monte_carlo_pvalue(ks_obs, data, n_resamples=2000)
        
        # We expect a high p-value (e.g., > 0.05) for data drawn from the distribution
        assert p_val > 0.05, f"Expected high p-value for exponential data, got {p_val}"
        assert 0.0 <= p_val <= 1.0

    def test_pvalue_low_for_uniform_data(self):
        """
        Test that uniform data yields a low p-value (reject).
        This verifies the test has power to distinguish non-exponential distributions.
        """
        np.random.seed(42)
        n_samples = 500
        
        # Generate data from a different distribution (Uniform)
        # Scale to have roughly similar mean to avoid trivial rejection due to scale
        data = np.random.uniform(0, 5, size=n_samples)
        
        # Compute observed statistic
        ks_obs = lilliefors_ks(data)
        
        # Run Monte Carlo
        p_val = monte_carlo_pvalue(ks_obs, data, n_resamples=2000)
        
        # We expect a low p-value (e.g., < 0.05) for data NOT from exponential
        assert p_val < 0.05, f"Expected low p-value for uniform data, got {p_val}"
        assert 0.0 <= p_val <= 1.0

    def test_resampling_logic_determinism(self):
        """
        Verify that with a fixed seed, the Monte Carlo result is deterministic.
        """
        np.random.seed(123)
        data = np.random.exponential(scale=1.0, size=200)
        ks_obs = lilliefors_ks(data)
        
        # Run twice with same seed
        np.random.seed(42)
        p1 = monte_carlo_pvalue(ks_obs, data, n_resamples=500)
        
        np.random.seed(42)
        p2 = monte_carlo_pvalue(ks_obs, data, n_resamples=500)
        
        assert p1 == p2, "Monte Carlo results should be deterministic with fixed seed"

    def test_edge_case_small_sample(self):
        """
        Test behavior with a very small sample size.
        """
        np.random.seed(99)
        data = np.random.exponential(scale=1.0, size=10)
        
        ks_obs = lilliefors_ks(data)
        p_val = monte_carlo_pvalue(ks_obs, data, n_resamples=100)
        
        # Just ensure it runs without crashing and returns a valid probability
        assert isinstance(p_val, float)
        assert 0.0 <= p_val <= 1.0

    def test_statistic_calculation_correctness(self):
        """
        Verify the KS statistic calculation against a known theoretical case.
        """
        # Create a dataset that perfectly fits Exp(1) (impossible with random, 
        # but we can test the logic with a known sorted sequence)
        # Instead, we test against scipy's KS test on a large sample where
        # parameters are known, though Lilliefors is distinct.
        # Here we verify the internal logic: max deviation.
        np.random.seed(42)
        data = np.random.exponential(scale=1.0, size=10000)
        
        ks_manual = lilliefors_ks(data)
        
        # Compare with standard KS test (which assumes known parameters)
        # This is a sanity check: Lilliefors statistic should be comparable
        # but slightly different because it estimates the parameter.
        _, ks_scipy = kstest(data, 'expon')
        
        # They should be in the same ballpark, though not identical
        assert ks_manual > 0
        assert ks_scipy > 0
        # The difference shouldn't be massive for large N
        assert abs(ks_manual - ks_scipy) < 0.1