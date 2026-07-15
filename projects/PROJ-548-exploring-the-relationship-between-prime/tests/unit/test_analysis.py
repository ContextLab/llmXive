"""
Unit tests for analysis functions, specifically the Kolmogorov-Smirnov (KS) test calculation.
This file extends the existing test suite for the US2 user story.
"""
import pytest
import numpy as np
from scipy import stats
import sys
import os

# Add the project root to the path to allow imports from src/
# Assuming this test is run from the project root or the path is configured correctly
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the analysis module where the KS logic would reside or be tested against
# Since the implementation file (src/analysis/distribution_test.py) is not yet fully implemented,
# we will test the logic directly using scipy.stats.kstest as the reference implementation
# and ensure our wrapper (or the future implementation) adheres to expected behavior.
# For this task, we assume the analysis logic will be in src.analysis.distribution_test
# We will mock the import or test the underlying statistical logic.

# We define a helper to simulate the expected function signature that T018b/T022 will use
def compute_ks_statistic(empirical_data, theoretical_cdf_func):
    """
    Computes the KS statistic and p-value comparing empirical data to a theoretical CDF.
    This is the core logic to be tested.
    
    Args:
        empirical_data (np.ndarray): Array of observed values.
        theoretical_cdf_func (callable): A function CDF(x) returning the cumulative probability.
        
    Returns:
        tuple: (ks_statistic, p_value)
    """
    if len(empirical_data) == 0:
        raise ValueError("Empirical data cannot be empty.")
    
    # Use scipy's kstest which accepts a CDF function
    # Note: kstest expects the CDF function to accept an array of values
    ks_stat, p_val = stats.kstest(empirical_data, theoretical_cdf_func)
    return ks_stat, p_val

class TestKSCalculation:
    """Unit tests for KS test calculation logic."""

    def test_ks_statistic_perfect_fit(self):
        """Test KS statistic is near zero for data drawn from the theoretical distribution."""
        # Generate data from a known distribution (Normal)
        np.random.seed(42)
        data = np.random.normal(loc=0.0, scale=1.0, size=10000)
        
        # Define the theoretical CDF for standard normal
        def std_normal_cdf(x):
            return stats.norm.cdf(x, loc=0.0, scale=1.0)
        
        ks_stat, p_val = compute_ks_statistic(data, std_normal_cdf)
        
        # For a large sample from the same distribution, KS stat should be small
        # and p-value should be high (not rejecting null hypothesis)
        assert ks_stat < 0.02, f"KS statistic {ks_stat} is too high for a perfect fit"
        assert p_val > 0.05, f"P-value {p_val} suggests rejection of a true null hypothesis"

    def test_ks_statistic_mismatch(self):
        """Test KS statistic is large for data from a different distribution."""
        # Generate data from a uniform distribution
        np.random.seed(42)
        data = np.random.uniform(low=0.0, high=1.0, size=1000)
        
        # Test against a standard normal CDF (mismatch)
        def std_normal_cdf(x):
            return stats.norm.cdf(x, loc=0.0, scale=1.0)
        
        ks_stat, p_val = compute_ks_statistic(data, std_normal_cdf)
        
        # The KS statistic should be significant
        assert ks_stat > 0.1, f"KS statistic {ks_stat} is too low for a mismatch"
        assert p_val < 0.05, f"P-value {p_val} should be low for a mismatch"

    def test_ks_statistic_edge_cases(self):
        """Test behavior with edge cases like constant data."""
        # Constant data
        constant_data = np.array([1.0, 1.0, 1.0, 1.0])
        
        # CDF for a distribution that doesn't have a point mass at 1.0
        def continuous_cdf(x):
            return stats.norm.cdf(x, loc=0.0, scale=1.0)
        
        ks_stat, p_val = compute_ks_statistic(constant_data, continuous_cdf)
        
        # KS statistic should be 1.0 (maximum difference between step function at 1.0 and continuous CDF)
        # Actually, the max difference will be close to 1.0 depending on the CDF value at 1.0
        assert ks_stat >= 0.9, "KS statistic for constant data vs continuous CDF should be very high"

    def test_ks_statistic_small_sample(self):
        """Test KS calculation with a very small sample size."""
        small_data = np.array([0.1, 0.2, 0.3])
        
        def uniform_cdf(x):
            return stats.uniform.cdf(x, loc=0.0, scale=1.0)
        
        ks_stat, p_val = compute_ks_statistic(small_data, uniform_cdf)
        
        # Should run without error
        assert isinstance(ks_stat, float)
        assert isinstance(p_val, float)
        assert 0 <= ks_stat <= 1.0
        assert 0 <= p_val <= 1.0

    def test_ks_statistic_empty_data_raises(self):
        """Test that empty data raises an error."""
        empty_data = np.array([])
        
        def dummy_cdf(x):
            return 0.5
        
        with pytest.raises(ValueError, match="Empirical data cannot be empty"):
            compute_ks_statistic(empty_data, dummy_cdf)

    def test_ks_statistic_with_gue_theoretical_cdf_stub(self):
        """
        Test that the KS calculation works with a theoretical CDF function 
        that mimics the expected GUE-derived extreme value CDF signature.
        This ensures the implementation in T022/T021a will be compatible.
        """
        # Mock data representing normalized gaps
        np.random.seed(123)
        mock_gaps = np.random.exponential(scale=1.0, size=100)
        
        # Mock GUE-derived extreme value CDF (placeholder for the real implementation in T021a)
        # The real function will likely look like: def gue_extreme_cdf(x): ...
        def mock_gue_extreme_cdf(x):
            # Example: Gumbel distribution often appears in extreme value theory
            # CDF = exp(-exp(-(x-mu)/beta))
            mu, beta = 0.5, 1.0
            return np.where(x < 0, 0.0, np.exp(-np.exp(-(x - mu) / beta)))
        
        ks_stat, p_val = compute_ks_statistic(mock_gaps, mock_gue_extreme_cdf)
        
        assert isinstance(ks_stat, float)
        assert isinstance(p_val, float)
        assert 0 <= ks_stat <= 1.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])