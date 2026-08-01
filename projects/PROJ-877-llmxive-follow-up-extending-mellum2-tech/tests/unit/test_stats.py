"""
Unit tests for statistical analysis functions in code/analysis/stats.py.

These tests verify the correctness of the permutation test implementation,
specifically checking that labels are properly shuffled and that p-values
are computed correctly.
"""

import pytest
import numpy as np
from pathlib import Path
import sys
import json

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.stats import permutation_test, compute_pvalue


class TestPermutationTest:
    """Test suite for the permutation test functionality."""
    
    def test_permutation_test_shuffles_labels(self):
        """Test that permutation_test properly shuffles labels during resampling."""
        # Create synthetic but realistic data
        np.random.seed(42)
        complexity = np.random.normal(10, 3, 100)
        loss = np.random.normal(5, 1, 100)
        
        # Run permutation test with a small number of permutations for speed
        n_permutations = 100
        result = permutation_test(complexity, loss, n_permutations=n_permutations, 
                                random_state=42, method="two-sided")
        
        # Verify that the result contains expected keys
        assert "observed_statistic" in result
        assert "p_value" in result
        assert "permutation_statistics" in result
        assert "n_permutations" in result
        
        # Check that permutation statistics have the correct length
        assert len(result["permutation_statistics"]) == n_permutations
        
        # Verify that shuffling actually changes the statistic
        # (i.e., not all permutation statistics equal the observed statistic)
        unique_stats = np.unique(result["permutation_statistics"])
        assert len(unique_stats) > 1, "Labels were not shuffled properly"
        
        # Verify that the observed statistic is different from at least some
        # permutation statistics (unless by extreme coincidence)
        assert not np.allclose(result["permutation_statistics"], 
                             result["observed_statistic"], atol=1e-10), \
            "All permutation statistics equal observed - shuffling may be broken"
    
    def test_permutation_test_computes_pvalue(self):
        """Test that permutation_test computes p-values correctly."""
        np.random.seed(123)
        
        # Create data with a known correlation
        n_samples = 100
        complexity = np.random.normal(10, 3, n_samples)
        # Create loss with a positive correlation to complexity
        loss = 0.5 * complexity + np.random.normal(0, 1, n_samples)
        
        # Run permutation test
        n_permutations = 500
        result = permutation_test(complexity, loss, n_permutations=n_permutations,
                                random_state=123, method="two-sided")
        
        # Verify p-value is in valid range [0, 1]
        p_value = result["p_value"]
        assert 0.0 <= p_value <= 1.0, f"p-value {p_value} not in valid range [0, 1]"
        
        # Verify that p-value computation follows the formula:
        # p = (number of permuted stats >= |observed| + 1) / (n_permutations + 1)
        observed_abs = abs(result["observed_statistic"])
        extreme_count = np.sum(np.abs(result["permutation_statistics"]) >= observed_abs)
        expected_pvalue = (extreme_count + 1) / (n_permutations + 1)
        
        assert np.isclose(p_value, expected_pvalue), \
            f"p-value {p_value} does not match expected {expected_pvalue}"
        
        # For positively correlated data, we expect a relatively small p-value
        # (though not guaranteed, it's a reasonable sanity check)
        # With n=100 and effect size 0.5, p-value should typically be < 0.1
        # We use a lenient threshold to account for randomness
        assert p_value < 0.5, \
            f"p-value {p_value} unexpectedly high for correlated data"
    
    def test_permutation_test_handles_independent_data(self):
        """Test that permutation test correctly identifies independent variables."""
        np.random.seed(456)
        
        # Create completely independent data
        complexity = np.random.normal(10, 3, 100)
        loss = np.random.normal(5, 1, 100)  # No relationship to complexity
        
        result = permutation_test(complexity, loss, n_permutations=500,
                                random_state=456, method="two-sided")
        
        # For independent data, p-value should be uniformly distributed
        # We can't expect it to be exactly 0.5, but it should not be extremely small
        # A p-value < 0.01 would be suspicious for truly independent data
        assert result["p_value"] >= 0.01, \
            f"p-value {result['p_value']} unexpectedly small for independent data"
    
    def test_permutation_test_with_custom_statistic(self):
        """Test permutation test with a custom statistic function."""
        np.random.seed(789)
        
        complexity = np.random.normal(10, 3, 100)
        loss = 0.3 * complexity + np.random.normal(0, 1, 100)
        
        # Use Spearman correlation instead of Pearson
        def spearman_statistic(x, y):
            from scipy.stats import spearmanr
            return spearmanr(x, y)[0]
        
        result = permutation_test(complexity, loss, n_permutations=200,
                                random_state=789, method="two-sided",
                                statistic=spearman_statistic)
        
        assert "observed_statistic" in result
        assert "p_value" in result
        # Spearman correlation should be positive for this data
        assert result["observed_statistic"] > 0
    
    def test_permutation_test_edge_case_small_sample(self):
        """Test permutation test with very small sample size."""
        np.random.seed(999)
        
        complexity = np.array([1, 2, 3, 4, 5])
        loss = np.array([2, 4, 6, 8, 10])
        
        # With only 5 samples, max permutations = 5! = 120
        # But we request more, so it should handle gracefully
        result = permutation_test(complexity, loss, n_permutations=1000,
                                random_state=999, method="two-sided")
        
        assert result["p_value"] is not None
        assert 0.0 <= result["p_value"] <= 1.0

class TestComputePvalue:
    """Test suite for the compute_pvalue helper function."""
    
    def test_compute_pvalue_basic(self):
        """Test basic p-value computation."""
        observed = 0.5
        permuted = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9])
        
        p_value = compute_pvalue(observed, permuted, method="two-sided")
        
        # For two-sided test, count how many |permuted| >= |observed|
        # |observed| = 0.5
        # |permuted| >= 0.5: 0.6, 0.7, 0.8, 0.9 (4 values)
        # p = (4 + 1) / (8 + 1) = 5/9 ≈ 0.556
        expected = 5 / 9
        assert np.isclose(p_value, expected), f"Expected {expected}, got {p_value}"
    
    def test_compute_pvalue_one_sided_greater(self):
        """Test one-sided (greater) p-value computation."""
        observed = 0.5
        permuted = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9])
        
        p_value = compute_pvalue(observed, permuted, method="greater")
        
        # Count how many permuted >= observed
        # 0.6, 0.7, 0.8, 0.9 (4 values)
        # p = (4 + 1) / (8 + 1) = 5/9
        expected = 5 / 9
        assert np.isclose(p_value, expected)
    
    def test_compute_pvalue_one_sided_less(self):
        """Test one-sided (less) p-value computation."""
        observed = 0.5
        permuted = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9])
        
        p_value = compute_pvalue(observed, permuted, method="less")
        
        # Count how many permuted <= observed
        # 0.1, 0.2, 0.3, 0.4 (4 values)
        # p = (4 + 1) / (8 + 1) = 5/9
        expected = 5 / 9
        assert np.isclose(p_value, expected)
    
    def test_compute_pvalue_all_extreme(self):
        """Test p-value when all permuted values are more extreme."""
        observed = 0.5
        permuted = np.array([0.6, 0.7, 0.8, 0.9, 1.0])
        
        p_value = compute_pvalue(observed, permuted, method="greater")
        
        # All 5 permuted >= observed
        # p = (5 + 1) / (5 + 1) = 1.0
        expected = 1.0
        assert np.isclose(p_value, expected)
    
    def test_compute_pvalue_no_extreme(self):
        """Test p-value when no permuted values are more extreme."""
        observed = 0.5
        permuted = np.array([0.1, 0.2, 0.3, 0.4])
        
        p_value = compute_pvalue(observed, permuted, method="greater")
        
        # None of the permuted >= observed
        # p = (0 + 1) / (4 + 1) = 0.2
        expected = 0.2
        assert np.isclose(p_value, expected)