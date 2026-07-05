"""
Unit tests for statistical power calculation logic.

This module tests the statistical power analysis functions used in the
predictive modeling pipeline (User Story 2). It verifies that:
1. Power calculations are mathematically correct for known effect sizes
2. The paired t-test power function handles edge cases properly
3. Power increases with sample size as expected
"""

import pytest
import numpy as np
from scipy import stats
from scipy.stats import ttest_rel, ttest_1samp

# Import the function to be tested (will be added to code/modeling/evaluate.py)
# Since it doesn't exist yet, we define a minimal implementation here for testing
# In the actual implementation, this would be imported from code/modeling/evaluate.py

def calculate_statistical_power(effect_size, sample_size, alpha=0.05, two_tailed=True):
    """
    Calculate statistical power for a paired t-test.
    
    Args:
        effect_size: Cohen's d effect size
        sample_size: Number of paired observations
        alpha: Significance level (default 0.05)
        two_tailed: Whether to use two-tailed test (default True)
        
    Returns:
        float: Statistical power (1 - beta)
    """
    # Degrees of freedom
    df = sample_size - 1
    
    # Critical t-value
    if two_tailed:
        alpha_adj = alpha / 2
    else:
        alpha_adj = alpha
        
    t_crit = stats.t.ppf(1 - alpha_adj, df)
    
    # Non-centrality parameter
    ncp = effect_size * np.sqrt(sample_size)
    
    # Power = P(t > t_crit | H1) + P(t < -t_crit | H1) for two-tailed
    if two_tailed:
        power = (1 - stats.nct.cdf(t_crit, df, ncp)) + stats.nct.cdf(-t_crit, df, ncp)
    else:
        power = 1 - stats.nct.cdf(t_crit, df, ncp)
        
    return max(0.0, min(1.0, power))


def calculate_effect_size_cohens_d(mean_diff, std_diff):
    """
    Calculate Cohen's d effect size for paired samples.
    
    Args:
        mean_diff: Mean of differences between paired samples
        std_diff: Standard deviation of differences
        
    Returns:
        float: Cohen's d effect size
    """
    if std_diff == 0:
        return 0.0
    return mean_diff / std_diff


class TestPowerAnalysis:
    """Test suite for statistical power calculations."""
    
    def test_power_increases_with_sample_size(self):
        """Power should increase as sample size increases for fixed effect size."""
        effect_size = 0.5  # Medium effect
        alpha = 0.05
        
        powers = []
        sample_sizes = [5, 10, 20, 30, 50, 100]
        
        for n in sample_sizes:
            power = calculate_statistical_power(effect_size, n, alpha)
            powers.append(power)
        
        # Verify powers are monotonically increasing
        for i in range(1, len(powers)):
            assert powers[i] >= powers[i-1], f"Power decreased from {powers[i-1]} to {powers[i]}"
        
        # Verify power approaches 1 for large samples
        assert powers[-1] > 0.9, f"Power should be > 0.9 for n=100, got {powers[-1]}"
    
    def test_power_increases_with_effect_size(self):
        """Power should increase as effect size increases for fixed sample size."""
        sample_size = 30
        alpha = 0.05
        
        effect_sizes = [0.2, 0.5, 0.8, 1.2]  # Small to large
        powers = []
        
        for es in effect_sizes:
            power = calculate_statistical_power(es, sample_size, alpha)
            powers.append(power)
        
        # Verify powers are monotonically increasing
        for i in range(1, len(powers)):
            assert powers[i] >= powers[i-1], f"Power decreased from {powers[i-1]} to {powers[i]}"
        
        # Large effect should have high power
        assert powers[-1] > 0.8, f"Power for large effect should be > 0.8, got {powers[-1]}"
    
    def test_power_below_threshold_for_small_sample(self):
        """Small samples should have low power even with moderate effect."""
        effect_size = 0.5
        sample_size = 5
        alpha = 0.05
        
        power = calculate_statistical_power(effect_size, sample_size, alpha)
        
        # Small sample should have low power (< 0.5)
        assert power < 0.5, f"Power for n=5 should be < 0.5, got {power}"
    
    def test_cohen_d_calculation(self):
        """Test Cohen's d calculation with known values."""
        # Example: mean diff = 10, std diff = 5 -> d = 2.0
        mean_diff = 10.0
        std_diff = 5.0
        
        d = calculate_effect_size_cohens_d(mean_diff, std_diff)
        
        assert d == 2.0, f"Cohen's d should be 2.0, got {d}"
    
    def test_cohen_d_zero_std(self):
        """Cohen's d should handle zero standard deviation."""
        mean_diff = 10.0
        std_diff = 0.0
        
        d = calculate_effect_size_cohens_d(mean_diff, std_diff)
        
        assert d == 0.0, f"Cohen's d with zero std should be 0.0, got {d}"
    
    def test_power_calculation_consistency_with_scipy(self):
        """Verify our power calculation is consistent with scipy's nct distribution."""
        # Use a specific case to verify
        effect_size = 0.5
        sample_size = 20
        alpha = 0.05
        
        power = calculate_statistical_power(effect_size, sample_size, alpha)
        
        # Manual verification using scipy's non-central t-distribution
        df = sample_size - 1
        t_crit = stats.t.ppf(1 - alpha/2, df)
        ncp = effect_size * np.sqrt(sample_size)
        
        expected_power = (1 - stats.nct.cdf(t_crit, df, ncp)) + stats.nct.cdf(-t_crit, df, ncp)
        
        # Allow small numerical tolerance
        assert abs(power - expected_power) < 1e-10, f"Power mismatch: {power} vs {expected_power}"
    
    def test_power_bounds(self):
        """Power should always be between 0 and 1."""
        test_cases = [
            (0.1, 5),
            (0.2, 10),
            (0.5, 30),
            (1.0, 50),
            (2.0, 100),
        ]
        
        for effect_size, sample_size in test_cases:
            power = calculate_statistical_power(effect_size, sample_size)
            assert 0.0 <= power <= 1.0, f"Power {power} out of bounds [0, 1]"
    
    def test_power_for_typical_research_scenario(self):
        """Test power for a typical research scenario in materials science."""
        # Typical scenario: n=20 samples, medium effect size (d=0.5)
        # Should have power around 0.56
        sample_size = 20
        effect_size = 0.5
        alpha = 0.05
        
        power = calculate_statistical_power(effect_size, sample_size, alpha)
        
        # Power should be in a reasonable range for this scenario
        assert 0.4 < power < 0.7, f"Power for n=20, d=0.5 should be ~0.56, got {power}"
    
    def test_power_calculation_edge_case_very_large_effect(self):
        """Test power with very large effect size."""
        effect_size = 3.0  # Very large effect
        sample_size = 10
        alpha = 0.05
        
        power = calculate_statistical_power(effect_size, sample_size, alpha)
        
        # Very large effect with even small sample should have high power
        assert power > 0.95, f"Power for very large effect should be > 0.95, got {power}"
    
    def test_power_calculation_edge_case_very_small_effect(self):
        """Test power with very small effect size."""
        effect_size = 0.1  # Very small effect
        sample_size = 10
        alpha = 0.05
        
        power = calculate_statistical_power(effect_size, sample_size, alpha)
        
        # Very small effect should have low power
        assert power < 0.2, f"Power for very small effect should be < 0.2, got {power}"
    
    def test_power_calculation_one_tailed(self):
        """Test power calculation for one-tailed test."""
        effect_size = 0.5
        sample_size = 30
        alpha = 0.05
        
        power_two_tailed = calculate_statistical_power(effect_size, sample_size, alpha, two_tailed=True)
        power_one_tailed = calculate_statistical_power(effect_size, sample_size, alpha, two_tailed=False)
        
        # One-tailed test should have slightly higher power
        assert power_one_tailed > power_two_tailed, "One-tailed power should be higher than two-tailed"
        
        # Both should be reasonable values
        assert 0.5 < power_two_tailed < 0.9, f"Two-tailed power should be in [0.5, 0.9], got {power_two_tailed}"
        assert 0.6 < power_one_tailed < 0.95, f"One-tailed power should be in [0.6, 0.95], got {power_one_tailed}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])