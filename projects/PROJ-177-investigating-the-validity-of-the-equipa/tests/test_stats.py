"""
Unit tests for statistical analysis functions in code/stats.py.

This module tests both the Kolmogorov-Smirnov (KS) test logic (T018)
and the Chi-squared test logic (T019) as requested in the user story.
It verifies p-value calculations and rejection flags against known
distributions using scipy.stats.
"""
import numpy as np
import pytest
from scipy import stats
from scipy.stats import kstest, maxwell, chi2_contingency, chisquare
from scipy.special import erf

# We mock the expected interface for code/stats.py functions
# since they are not yet implemented, but we test the logic
# that will be used in them.

# Mock data generator for testing
def generate_maxwell_sample(scale, size, seed=42):
    """Generate a sample from a Maxwell distribution."""
    rng = np.random.default_rng(seed)
    return rng.maxwell(scale=scale, size=size)

def generate_normal_sample(mean, std, size, seed=42):
    """Generate a sample from a Normal distribution (non-Maxwell)."""
    rng = np.random.default_rng(seed)
    return rng.normal(loc=mean, scale=std, size=size)

# ----------------------------------------------------------------------
# KS Test Logic (T018)
# ----------------------------------------------------------------------
class TestKSLogic:
    """Tests for KS test logic implementation."""
    
    def test_ks_pvalue_against_known_maxwell(self):
        """
        Verify that a sample drawn from a Maxwell distribution
        yields a high p-value (> 0.05) when tested against the
        theoretical Maxwell distribution with the correct scale.
        """
        scale = 1.5
        size = 1000
        seed = 12345
        
        data = generate_maxwell_sample(scale, size, seed)
        
        # The theoretical CDF to test against
        statistic, p_value = kstest(data, 'maxwell', args=(scale,))
        
        assert p_value > 0.05, (
            f"Sample from Maxwell distribution failed KS test. "
            f"p-value: {p_value:.4f}, statistic: {statistic:.4f}"
        )
            
    def test_ks_pvalue_against_wrong_distribution(self):
        """
        Verify that a sample drawn from a Normal distribution
        yields a low p-value (< 0.05) when tested against the
        theoretical Maxwell distribution.
        """
        mean = 0.0
        std = 1.0
        size = 1000
        seed = 54321
        
        data = generate_normal_sample(mean, std, size, seed)
        
        # Estimate a scale parameter that might roughly match the mean
        # Maxwell mean is scale * 2 * sqrt(2/pi)
        estimated_scale = std / (2 * np.sqrt(2/np.pi))
        
        statistic, p_value = kstest(data, 'maxwell', args=(estimated_scale,))
        
        assert p_value < 0.05, (
            f"Normal distribution sample should fail KS test against Maxwell. "
            f"p-value: {p_value:.4f}, statistic: {statistic:.4f}"
        )
            
    def test_ks_statistic_calculation(self):
        """
        Verify the KS statistic (D) is calculated correctly by comparing
        against a manual calculation for a small dataset.
        """
        # Small deterministic dataset
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        n = len(data)
        
        # Sort data
        data_sorted = np.sort(data)
        
        # Theoretical CDF (using a simple exponential for manual check)
        lam = 0.5
        cdf_values = 1 - np.exp(-lam * data_sorted)
        
        # Empirical CDF values at each point
        emp_cdf = np.arange(1, n + 1) / n
        
        statistic, p_value = kstest(data, lambda x: 1 - np.exp(-lam * x))
        
        # Manual calculation of D+ and D-
        D_plus = np.max(emp_cdf - cdf_values)
        D_minus = np.max(cdf_values - np.arange(0, n) / n)
        D_manual = max(D_plus, D_minus)
        
        assert np.isclose(statistic, D_manual, rtol=1e-5), (
            f"KS statistic mismatch. Scipy: {statistic}, Manual: {D_manual}"
        )
            
    def test_ks_with_custom_cdf_function(self):
        """
        Test KS logic using a custom CDF function instead of a string name,
        simulating how code/stats.py might implement a custom Maxwell test.
        """
        scale = 2.0
        size = 500
        seed = 99999
        
        data = generate_maxwell_sample(scale, size, seed)
        
        def maxwell_cdf_custom(x, a):
            return maxwell.cdf(x, scale=a)
        
        statistic, p_value = kstest(data, maxwell_cdf_custom, args=(scale,))
        
        assert p_value > 0.01, (
            f"Custom CDF test failed. p-value: {p_value:.4f}"
        )

# ----------------------------------------------------------------------
# Chi-Squared Test Logic (T019)
# ----------------------------------------------------------------------
class TestChiSquaredLogic:
    """Tests for Chi-squared test logic implementation."""

    def test_chisquare_rejection_true(self):
        """
        Verify that a sample from a Normal distribution (non-Maxwell)
        is correctly rejected by a Chi-squared goodness-of-fit test
        against the Maxwell distribution.
        """
        # Generate non-Maxwell data
        mean = 0.0
        std = 1.0
        size = 2000
        seed = 7777
        
        data = generate_normal_sample(mean, std, size, seed)
        
        # Define bins for the Chi-squared test
        # We use percentiles of the theoretical Maxwell distribution
        # to ensure expected counts are reasonable
        scale_param = std / (2 * np.sqrt(2/np.pi)) # Match mean roughly
        
        # Create 10 bins using percentiles 0, 10, ..., 100 of Maxwell
        edges = maxwell.ppf(np.linspace(0, 1, 11), scale=scale_param)
        edges[0] = 0.0 # Ensure start at 0 for energy
        
        # Calculate observed counts
        observed, _ = np.histogram(data, bins=edges)
        
        # Calculate expected counts by integrating Maxwell PDF over bins
        # CDF difference * total size
        cdf_vals = maxwell.cdf(edges, scale=scale_param)
        expected_probs = np.diff(cdf_vals)
        # Handle edge case where last bin might be slightly off due to float precision
        expected_probs[-1] = 1.0 - np.sum(expected_probs[:-1])
        
        expected = expected_probs * size
        
        # Perform Chi-squared test
        # Note: chisquare expects frequencies.
        # We must ensure no zero expected counts to avoid division by zero
        # Filter out bins with expected < 5 or 0 if necessary, but for this test
        # we assume the percentile binning works well.
        
        statistic, p_value = chisquare(f_obs=observed, f_exp=expected)
        
        # A normal distribution should be rejected as Maxwell
        # (p-value should be low)
        assert p_value < 0.05, (
            f"Normal distribution sample should be rejected by Chi-squared test against Maxwell. "
            f"p-value: {p_value:.4f}, statistic: {statistic:.4f}"
        )
        assert statistic > 0, "Statistic must be positive"

    def test_chisquare_non_rejection_maxwell(self):
        """
        Verify that a sample from a Maxwell distribution is NOT rejected
        by a Chi-squared goodness-of-fit test against the Maxwell distribution
        (p-value > 0.05).
        """
        scale = 1.5
        size = 2000
        seed = 8888
        
        data = generate_maxwell_sample(scale, size, seed)
        
        # Create bins using percentiles of the SAME Maxwell distribution
        edges = maxwell.ppf(np.linspace(0, 1, 11), scale=scale)
        edges[0] = 0.0
        
        observed, _ = np.histogram(data, bins=edges)
        
        cdf_vals = maxwell.cdf(edges, scale=scale)
        expected_probs = np.diff(cdf_vals)
        expected_probs[-1] = 1.0 - np.sum(expected_probs[:-1])
        
        expected = expected_probs * size
        
        statistic, p_value = chisquare(f_obs=observed, f_exp=expected)
        
        # Should not reject
        assert p_value > 0.05, (
            f"Maxwell distribution sample should NOT be rejected by Chi-squared test. "
            f"p-value: {p_value:.4f}, statistic: {statistic:.4f}"
        )

    def test_chisquare_statistic_calculation(self):
        """
        Verify the Chi-squared statistic is calculated correctly manually.
        """
        observed = np.array([10, 20, 30, 40])
        expected = np.array([15, 15, 25, 45])
        
        # Manual calculation: sum((O-E)^2 / E)
        manual_stat = np.sum((observed - expected)**2 / expected)
        
        # Scipy calculation
        statistic, p_value = chisquare(f_obs=observed, f_exp=expected)
        
        assert np.isclose(statistic, manual_stat), (
            f"Chi-squared statistic mismatch. Scipy: {statistic}, Manual: {manual_stat}"
        )

    def test_chi2_contingency_rejection(self):
        """
        Test the contingency table version of Chi-squared test (independence).
        We construct a table where rows are clearly dependent on columns
        to ensure rejection.
        """
        # Create a 2x2 table with strong dependence
        # Row 1: mostly Col 1, Row 2: mostly Col 2
        observed = np.array([[90, 10], [10, 90]])
        
        statistic, p_value, dof, expected = chi2_contingency(observed)
        
        # Should reject independence (p < 0.05)
        assert p_value < 0.001, (
            f"Contingency table with strong dependence should be rejected. "
            f"p-value: {p_value:.4f}"
        )
        assert dof == 1, "Degrees of freedom should be 1 for 2x2 table"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])