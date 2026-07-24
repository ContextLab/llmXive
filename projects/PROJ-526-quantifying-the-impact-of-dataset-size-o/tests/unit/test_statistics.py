"""
Unit tests for statistical analysis functions (Pearson correlation and Permutation test).

These tests verify the core logic for User Story 3:
- Pearson correlation calculation and significance testing
- Permutation test implementation for small sample sizes (N < 5)

Note: This test file does NOT require external data sources. It uses synthetic
test data generated within the test functions to verify the statistical logic.
The actual implementation in code/analyze_physics.py will use real scaling results.
"""
import pytest
import numpy as np
from scipy import stats
from typing import List, Tuple

# Import the functions we are testing
# We will implement these in code/analyze_physics.py if they don't exist yet
# For now, we define them locally for testing purposes
# In the actual implementation, these would be imported from code/analyze_physics

def pearson_correlation_with_pvalue(
    x: List[float], 
    y: List[float]
) -> Tuple[float, float]:
    """
    Calculate Pearson correlation coefficient and p-value.
    
    Args:
        x: First array of values
        y: Second array of values
        
    Returns:
        Tuple of (correlation_coefficient, p_value)
        
    Raises:
        ValueError: If input arrays have different lengths or are too short
    """
    if len(x) != len(y):
        raise ValueError("Input arrays must have the same length")
    if len(x) < 2:
        raise ValueError("Input arrays must have at least 2 elements")
        
    # Use scipy for calculation
    corr, p_value = stats.pearsonr(x, y)
    return float(corr), float(p_value)


def permutation_test_two_sample(
    x: List[float], 
    y: List[float], 
    n_permutations: int = 10000, 
    alternative: str = 'two-sided',
    random_state: int = 42
) -> float:
    """
    Perform a permutation test to compare two samples.
    
    This is the primary statistical method for small sample sizes (N < 5)
    as mandated by the project amendment (T036).
    
    Args:
        x: First sample (list of values)
        y: Second sample (list of values)
        n_permutations: Number of permutations to perform
        alternative: Type of test ('two-sided', 'less', 'greater')
        random_state: Random seed for reproducibility
        
    Returns:
        p-value from the permutation test
        
    Raises:
        ValueError: If samples are empty or too small
    """
    if not x or not y:
        raise ValueError("Input samples cannot be empty")
    if len(x) < 2 or len(y) < 2:
        raise ValueError("Each sample must have at least 2 elements")
        
    np.random.seed(random_state)
    
    # Calculate observed statistic (difference in means)
    observed_diff = np.mean(x) - np.mean(y)
    
    # Combine samples
    combined = np.array(x + y)
    n_x = len(x)
    n_combined = len(combined)
    
    # Generate permutation distribution
    permutation_diffs = []
    for _ in range(n_permutations):
        # Shuffle combined sample
        shuffled = np.random.permutation(combined)
        # Split into two groups of original sizes
        perm_x = shuffled[:n_x]
        perm_y = shuffled[n_x:]
        # Calculate difference
        perm_diff = np.mean(perm_x) - np.mean(perm_y)
        permutation_diffs.append(perm_diff)
    
    permutation_diffs = np.array(permutation_diffs)
    
    # Calculate p-value based on alternative hypothesis
    if alternative == 'two-sided':
        # Two-sided test: count how extreme the observed difference is
        extreme_count = np.sum(np.abs(permutation_diffs) >= np.abs(observed_diff))
        p_value = (extreme_count + 1) / (n_permutations + 1)
    elif alternative == 'less':
        # One-sided: x < y
        extreme_count = np.sum(permutation_diffs <= observed_diff)
        p_value = (extreme_count + 1) / (n_permutations + 1)
    elif alternative == 'greater':
        # One-sided: x > y
        extreme_count = np.sum(permutation_diffs >= observed_diff)
        p_value = (extreme_count + 1) / (n_permutations + 1)
    else:
        raise ValueError(f"Invalid alternative: {alternative}")
        
    return float(p_value)


class TestPearsonCorrelation:
    """Tests for Pearson correlation function."""
    
    def test_perfect_positive_correlation(self):
        """Test with perfectly correlated data."""
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        corr, p_value = pearson_correlation_with_pvalue(x, y)
        assert np.isclose(corr, 1.0, atol=1e-10)
        assert p_value == 0.0  # Perfect correlation, p-value should be 0
        
    def test_perfect_negative_correlation(self):
        """Test with perfectly negatively correlated data."""
        x = [1, 2, 3, 4, 5]
        y = [10, 8, 6, 4, 2]
        corr, p_value = pearson_correlation_with_pvalue(x, y)
        assert np.isclose(corr, -1.0, atol=1e-10)
        assert p_value == 0.0
        
    def test_no_correlation(self):
        """Test with uncorrelated data."""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)
        corr, p_value = pearson_correlation_with_pvalue(list(x), list(y))
        # With random data, correlation should be close to 0
        assert abs(corr) < 0.2
        # P-value should be high (not significant)
        assert p_value > 0.05
        
    def test_mismatched_lengths(self):
        """Test error handling for mismatched array lengths."""
        x = [1, 2, 3]
        y = [1, 2]
        with pytest.raises(ValueError):
            pearson_correlation_with_pvalue(x, y)
            
    def test_insufficient_data(self):
        """Test error handling for too few data points."""
        x = [1]
        y = [2]
        with pytest.raises(ValueError):
            pearson_correlation_with_pvalue(x, y)
            
    def test_realistic_materials_data(self):
        """Test with realistic materials science data pattern."""
        # Simulate a realistic correlation between property and scaling exponent
        # Higher spatial locality -> lower exponent (better scaling)
        np.random.seed(123)
        spatial_locality = np.random.uniform(0.1, 0.9, 20)
        # Add noise to the relationship
        scaling_exponent = 0.5 - 0.3 * spatial_locality + np.random.normal(0, 0.05, 20)
        
        corr, p_value = pearson_correlation_with_pvalue(
            list(spatial_locality), 
            list(scaling_exponent)
        )
        
        # Should show negative correlation
        assert corr < 0
        # With this sample size and effect size, p-value might be significant
        # Just verify the calculation works
        assert 0 <= p_value <= 1


class TestPermutationTest:
    """Tests for permutation test function."""
    
    def test_identical_samples(self):
        """Test with identical samples (should give high p-value)."""
        x = [1, 2, 3, 4, 5]
        y = [1, 2, 3, 4, 5]
        p_value = permutation_test_two_sample(x, y, n_permutations=1000, random_state=42)
        # With identical samples, p-value should be high (not significant)
        assert p_value > 0.05
        
    def test_different_samples(self):
        """Test with clearly different samples."""
        x = [1, 2, 3, 4, 5]
        y = [10, 11, 12, 13, 14]
        p_value = permutation_test_two_sample(x, y, n_permutations=1000, random_state=42)
        # With very different samples, p-value should be low (significant)
        assert p_value < 0.05
        
    def test_one_sided_less(self):
        """Test one-sided alternative 'less'."""
        x = [1, 2, 3]
        y = [10, 11, 12]
        # x < y, so for alternative='less', we expect low p-value
        p_value = permutation_test_two_sample(
            x, y, n_permutations=1000, alternative='less', random_state=42
        )
        assert p_value < 0.05
        
    def test_one_sided_greater(self):
        """Test one-sided alternative 'greater'."""
        x = [10, 11, 12]
        y = [1, 2, 3]
        # x > y, so for alternative='greater', we expect low p-value
        p_value = permutation_test_two_sample(
            x, y, n_permutations=1000, alternative='greater', random_state=42
        )
        assert p_value < 0.05
        
    def test_small_sample_size(self):
        """Test with small sample sizes (N=2-3 per group)."""
        # This is the critical case for our project (N < 5)
        x = [0.1, 0.2, 0.3]
        y = [0.6, 0.7, 0.8]
        p_value = permutation_test_two_sample(
            x, y, n_permutations=1000, random_state=42
        )
        # Should still work with small samples
        assert 0 <= p_value <= 1
        # With these clearly different values, should be significant
        assert p_value < 0.05
        
    def test_empty_samples(self):
        """Test error handling for empty samples."""
        with pytest.raises(ValueError):
            permutation_test_two_sample([], [1, 2, 3])
            
    def test_single_element_samples(self):
        """Test error handling for single element samples."""
        with pytest.raises(ValueError):
            permutation_test_two_sample([1], [2])
            
    def test_reproducibility(self):
        """Test that results are reproducible with same random state."""
        x = [1, 2, 3, 4, 5]
        y = [6, 7, 8, 9, 10]
        
        p1 = permutation_test_two_sample(x, y, n_permutations=1000, random_state=42)
        p2 = permutation_test_two_sample(x, y, n_permutations=1000, random_state=42)
        
        assert p1 == p2
        
    def test_materials_electronic_vs_mechanical(self):
        """
        Test with simulated electronic vs mechanical property scaling exponents.
        
        This mimics the actual use case where we compare two classes of properties.
        """
        # Simulate electronic properties (typically better scaling, lower exponents)
        electronic_exponents = [0.15, 0.18, 0.22, 0.19, 0.16]
        # Simulate mechanical properties (typically worse scaling, higher exponents)
        mechanical_exponents = [0.35, 0.38, 0.42, 0.39, 0.36]
        
        p_value = permutation_test_two_sample(
            electronic_exponents, 
            mechanical_exponents, 
            n_permutations=10000, 
            random_state=42
        )
        
        # With these clearly different distributions, should be significant
        assert p_value < 0.05
        
        # Also test the reverse order (should give same p-value for two-sided)
        p_value_reverse = permutation_test_two_sample(
            mechanical_exponents, 
            electronic_exponents, 
            n_permutations=10000, 
            random_state=42
        )
        
        assert abs(p_value - p_value_reverse) < 1e-10


class TestIntegrationStatistics:
    """Integration tests for statistical functions working together."""
    
    def test_correlation_then_permutation(self):
        """Test workflow: correlate metrics with exponents, then compare classes."""
        # Simulate data for 5 properties with different characteristics
        np.random.seed(456)
        
        # Spatial locality scores (0-1)
        spatial_locality = np.random.uniform(0.2, 0.8, 5)
        # Scaling exponents (correlated with spatial locality)
        scaling_exponents = 0.4 - 0.25 * spatial_locality + np.random.normal(0, 0.03, 5)
        
        # Calculate correlation
        corr, p_corr = pearson_correlation_with_pvalue(
            list(spatial_locality), 
            list(scaling_exponents)
        )
        
        # Verify correlation is negative (higher locality -> lower exponent)
        assert corr < 0
        assert 0 <= p_corr <= 1
        
        # Split into two classes (simulating electronic vs mechanical)
        electronic_exps = [scaling_exponents[0], scaling_exponents[1]]
        mechanical_exps = [scaling_exponents[2], scaling_exponents[3], scaling_exponents[4]]
        
        # Perform permutation test
        p_perm = permutation_test_two_sample(
            electronic_exps, 
            mechanical_exps, 
            n_permutations=1000, 
            random_state=42
        )
        
        assert 0 <= p_perm <= 1
        
    def test_edge_case_very_small_samples(self):
        """Test with the smallest possible valid samples (N=2 per group)."""
        x = [0.1, 0.2]
        y = [0.5, 0.6]
        
        # This should work even with N=2
        p_value = permutation_test_two_sample(
            x, y, n_permutations=1000, random_state=42
        )
        
        assert 0 <= p_value <= 1
        # With such different values, should be significant
        assert p_value < 0.1  # More lenient for tiny samples


if __name__ == '__main__':
    pytest.main([__file__, '-v'])