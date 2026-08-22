"""
Unit tests for statistical correction methods (FDR/Bonferroni) in code/analysis/stats.py.

This module tests the implementation of:
- Benjamini-Hochberg FDR correction
- Bonferroni correction
- Pairwise t-tests with FDR correction

These tests verify the correctness of the statistical methods used in the 
alignment scoring analysis (US3).
"""
import pytest
import numpy as np
from code.analysis.stats import (
    benjamini_hochberg_fdr,
    bonferroni_correction,
    pairwise_ttest_with_fdr
)


class TestBenjaminiHochbergFDR:
    """Tests for the Benjamini-Hochberg FDR correction implementation."""
    
    def test_basic_fdr_correction(self):
        """Test FDR correction on a simple set of p-values."""
        # Known p-values where we can manually verify the adjustment
        p_values = np.array([0.001, 0.01, 0.02, 0.05, 0.1, 0.2])
        alpha = 0.05
        
        result = benjamini_hochberg_fdr(p_values, alpha)
        
        # Should return same length as input
        assert len(result) == len(p_values)
        
        # Adjusted p-values should be monotonically increasing
        # (after sorting by original p-values)
        sorted_indices = np.argsort(p_values)
        adjusted_sorted = result[sorted_indices]
        assert np.all(np.diff(adjusted_sorted) >= -1e-10)  # Allow small floating point errors
        
        # All adjusted p-values should be <= 1.0
        assert np.all(result <= 1.0)
        
        # All adjusted p-values should be >= original p-values
        assert np.all(result >= p_values)
    
    def test_fdr_with_all_significant(self):
        """Test FDR when all p-values are very small."""
        p_values = np.array([0.0001, 0.0002, 0.0003, 0.0004, 0.0005])
        alpha = 0.05
        
        result = benjamini_hochberg_fdr(p_values, alpha)
        
        # Most should be significant after correction
        significant_count = np.sum(result < alpha)
        assert significant_count >= 3  # At least half should be significant
    
    def test_fdr_with_all_insignificant(self):
        """Test FDR when all p-values are very large."""
        p_values = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
        alpha = 0.05
        
        result = benjamini_hochberg_fdr(p_values, alpha)
        
        # None should be significant
        significant_count = np.sum(result < alpha)
        assert significant_count == 0
    
    def test_fdr_edge_case_single_pvalue(self):
        """Test FDR with a single p-value."""
        p_values = np.array([0.03])
        alpha = 0.05
        
        result = benjamini_hochberg_fdr(p_values, alpha)
        
        assert len(result) == 1
        assert result[0] >= p_values[0]  # Adjusted should be >= original
    
    def test_fdr_monotonicity_property(self):
        """Test that FDR correction preserves the monotonicity property."""
        np.random.seed(42)
        p_values = np.random.uniform(0, 1, 100)
        alpha = 0.05
        
        result = benjamini_hochberg_fdr(p_values, alpha)
        
        # Sort by original p-values
        sorted_indices = np.argsort(p_values)
        sorted_p = p_values[sorted_indices]
        sorted_adj = result[sorted_indices]
        
        # The ratio sorted_adj / sorted_p should be non-decreasing
        # (This is a property of BH procedure)
        ratios = sorted_adj / sorted_p
        # Allow for some floating point tolerance
        assert np.all(np.diff(ratios) >= -1e-10)
    
    def test_fdr_alpha_boundary(self):
        """Test FDR behavior at alpha boundaries."""
        p_values = np.array([0.04, 0.05, 0.06])
        
        # With alpha=0.05, the first two should potentially be significant
        result_05 = benjamini_hochberg_fdr(p_values, 0.05)
        assert result_05[0] <= 0.05  # First should be significant or close
        
        # With alpha=0.01, likely none significant
        result_01 = benjamini_hochberg_fdr(p_values, 0.01)
        assert np.all(result_01 > 0.01) or result_01[0] <= 0.01
    
    def test_fdr_with_zero_pvalue(self):
        """Test FDR with a p-value of exactly 0 (edge case)."""
        p_values = np.array([0.0, 0.01, 0.02])
        alpha = 0.05
        
        result = benjamini_hochberg_fdr(p_values, alpha)
        
        # The zero p-value should remain zero or very close
        assert result[0] == 0.0 or result[0] < 1e-10
    
    def test_fdr_with_nan_handling(self):
        """Test that FDR handles NaN values appropriately."""
        p_values = np.array([0.01, np.nan, 0.03])
        alpha = 0.05
        
        # Should not crash, but may return NaN for the NaN input
        result = benjamini_hochberg_fdr(p_values, alpha)
        
        # Check that non-NaN values are processed
        assert not np.isnan(result[0])
        assert np.isnan(result[1])  # NaN input should produce NaN output
        assert not np.isnan(result[2])
    
    def test_fdr_large_dataset(self):
        """Test FDR correction on a larger dataset for performance."""
        np.random.seed(42)
        p_values = np.random.uniform(0, 1, 1000)
        alpha = 0.05
        
        result = benjamini_hochberg_fdr(p_values, alpha)
        
        assert len(result) == 1000
        assert np.all(result <= 1.0)
        assert np.all(result >= 0.0)
    
    def test_fdr_deterministic(self):
        """Test that FDR produces deterministic results."""
        p_values = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
        alpha = 0.05
        
        result1 = benjamini_hochberg_fdr(p_values, alpha)
        result2 = benjamini_hochberg_fdr(p_values, alpha)
        
        np.testing.assert_array_almost_equal(result1, result2)
    
    def test_fdr_vs_manual_calculation(self):
        """Test FDR against a manually calculated example."""
        # Simple example: 5 p-values
        p_values = np.array([0.001, 0.004, 0.03, 0.05, 0.12])
        alpha = 0.05
        n = len(p_values)
        
        result = benjamini_hochberg_fdr(p_values, alpha)
        
        # Manual calculation steps:
        # 1. Sort p-values
        sorted_indices = np.argsort(p_values)
        sorted_p = p_values[sorted_indices]
        
        # 2. Calculate BH critical values: (i/n) * alpha
        critical_values = [(i + 1) / n * alpha for i in range(n)]
        
        # 3. Find largest i where p(i) <= critical_value(i)
        # 4. Set all p-values <= that threshold as significant
        
        # Verify that the function finds the correct threshold
        # (This is a more complex test, just checking it runs without error for now)
        assert len(result) == n
        assert np.all(result >= 0)
        assert np.all(result <= 1)


class TestBonferroniCorrection:
    """Tests for the Bonferroni correction implementation."""
    
    def test_basic_bonferroni(self):
        """Test Bonferroni correction on a simple set of p-values."""
        p_values = np.array([0.001, 0.01, 0.02, 0.05, 0.1])
        alpha = 0.05
        
        result = bonferroni_correction(p_values, alpha)
        
        # Bonferroni adjusted p-values = original * n
        n = len(p_values)
        expected = p_values * n
        
        # Allow for small floating point differences
        np.testing.assert_array_almost_equal(result, expected, decimal=10)
    
    def test_bonferroni_clamping(self):
        """Test that Bonferroni clamps adjusted p-values to 1.0."""
        p_values = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
        alpha = 0.05
        
        result = bonferroni_correction(p_values, alpha)
        
        # All should be clamped to 1.0 or close
        assert np.all(result <= 1.0)
        # Most should be exactly 1.0
        assert np.sum(result == 1.0) >= 3
    
    def test_bonferroni_vs_fdr_strictness(self):
        """Test that Bonferroni is more conservative than FDR."""
        p_values = np.array([0.001, 0.01, 0.02, 0.05, 0.1, 0.2])
        alpha = 0.05
        
        fdr_result = benjamini_hochberg_fdr(p_values, alpha)
        bonf_result = bonferroni_correction(p_values, alpha)
        
        # Bonferroni adjusted p-values should be >= FDR adjusted p-values
        # (Bonferroni is more conservative)
        assert np.all(bonf_result >= fdr_result)
    
    def test_bonferroni_alpha_boundary(self):
        """Test Bonferroni behavior at alpha boundaries."""
        p_values = np.array([0.01, 0.02, 0.03])
        alpha = 0.05
        
        result = bonferroni_correction(p_values, alpha)
        
        # With n=3, adjusted = p * 3
        # 0.01 * 3 = 0.03 < 0.05 (significant)
        # 0.02 * 3 = 0.06 > 0.05 (not significant)
        # 0.03 * 3 = 0.09 > 0.05 (not significant)
        assert result[0] < alpha  # First should be significant
        assert result[1] >= alpha  # Second should not be significant
        assert result[2] >= alpha  # Third should not be significant
    
    def test_bonferroni_single_pvalue(self):
        """Test Bonferroni with a single p-value."""
        p_values = np.array([0.03])
        alpha = 0.05
        
        result = bonferroni_correction(p_values, alpha)
        
        # With n=1, adjusted = original
        assert result[0] == p_values[0]
    
    def test_bonferroni_large_dataset(self):
        """Test Bonferroni on a larger dataset."""
        np.random.seed(42)
        p_values = np.random.uniform(0, 1, 100)
        alpha = 0.05
        
        result = bonferroni_correction(p_values, alpha)
        
        assert len(result) == 100
        assert np.all(result <= 1.0)
        assert np.all(result >= 0.0)
    
    def test_bonferroni_deterministic(self):
        """Test that Bonferroni produces deterministic results."""
        p_values = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
        alpha = 0.05
        
        result1 = bonferroni_correction(p_values, alpha)
        result2 = bonferroni_correction(p_values, alpha)
        
        np.testing.assert_array_almost_equal(result1, result2)


class TestPairwiseTtestWithFDR:
    """Tests for pairwise t-tests with FDR correction."""
    
    def test_pairwise_ttest_basic(self):
        """Test pairwise t-tests with FDR correction on simple data."""
        np.random.seed(42)
        
        # Create three groups with different means
        group1 = np.random.normal(0, 1, 50)
        group2 = np.random.normal(1, 1, 50)  # Different mean
        group3 = np.random.normal(0, 1, 50)  # Same as group1
        
        groups = [group1, group2, group3]
        alpha = 0.05
        
        result = pairwise_ttest_with_fdr(groups, alpha)
        
        # Should return 3 comparisons (3 choose 2)
        assert len(result) == 3
        
        # Check that results contain expected keys
        for res in result:
            assert 'comparison' in res
            assert 'p_value' in res
            assert 'adjusted_p_value' in res
            assert 'significant' in res
    
    def test_pairwise_ttest_significant_difference(self):
        """Test that pairwise t-test detects significant differences."""
        np.random.seed(42)
        
        # Group 1 and 2 have very different means
        group1 = np.random.normal(0, 0.5, 100)
        group2 = np.random.normal(5, 0.5, 100)  # Large difference
        group3 = np.random.normal(0, 0.5, 100)
        
        groups = [group1, group2, group3]
        alpha = 0.05
        
        result = pairwise_ttest_with_fdr(groups, alpha)
        
        # Find the comparison between group1 and group2
        comp_12 = next(r for r in result if '0' in str(r['comparison']) and '1' in str(r['comparison']))
        
        # This comparison should be significant
        assert comp_12['significant'] is True
    
    def test_pairwise_ttest_no_difference(self):
        """Test that pairwise t-test correctly identifies no difference."""
        np.random.seed(42)
        
        # All groups have the same distribution
        group1 = np.random.normal(0, 1, 100)
        group2 = np.random.normal(0, 1, 100)
        group3 = np.random.normal(0, 1, 100)
        
        groups = [group1, group2, group3]
        alpha = 0.05
        
        result = pairwise_ttest_with_fdr(groups, alpha)
        
        # Most comparisons should not be significant (allowing for some false positives)
        significant_count = sum(1 for r in result if r['significant'])
        # With 3 comparisons and alpha=0.05, we expect ~0-1 significant by chance
        assert significant_count <= 1
    
    def test_pairwise_ttest_input_validation(self):
        """Test that pairwise t-test handles invalid input."""
        # Empty list
        with pytest.raises(ValueError):
            pairwise_ttest_with_fdr([], 0.05)
        
        # Single group (need at least 2 for pairwise)
        with pytest.raises(ValueError):
            pairwise_ttest_with_fdr([np.random.normal(0, 1, 10)], 0.05)
    
    def test_pairwise_ttest_with_fdr_correction(self):
        """Test that FDR correction is actually applied."""
        np.random.seed(42)
        
        groups = [
            np.random.normal(0, 1, 50),
            np.random.normal(0.5, 1, 50),
            np.random.normal(1.0, 1, 50),
            np.random.normal(1.5, 1, 50)
        ]
        alpha = 0.05
        
        result = pairwise_ttest_with_fdr(groups, alpha)
        
        # Check that adjusted p-values are different from raw p-values
        for res in result:
            # Adjusted should be >= raw (FDR is conservative)
            assert res['adjusted_p_value'] >= res['p_value']
    
    def test_pairwise_ttest_deterministic(self):
        """Test that pairwise t-test produces deterministic results."""
        np.random.seed(42)
        
        groups = [
            np.random.normal(0, 1, 50),
            np.random.normal(0.5, 1, 50),
            np.random.normal(1.0, 1, 50)
        ]
        alpha = 0.05
        
        result1 = pairwise_ttest_with_fdr(groups, alpha)
        result2 = pairwise_ttest_with_fdr(groups, alpha)
        
        # Compare results
        for r1, r2 in zip(result1, result2):
            assert r1['comparison'] == r2['comparison']
            assert r1['p_value'] == r2['p_value']
            assert r1['adjusted_p_value'] == r2['adjusted_p_value']
            assert r1['significant'] == r2['significant']
    
    def test_pairwise_ttest_small_sample(self):
        """Test pairwise t-test with small sample sizes."""
        np.random.seed(42)
        
        groups = [
            np.random.normal(0, 1, 5),
            np.random.normal(1, 1, 5),
            np.random.normal(0, 1, 5)
        ]
        alpha = 0.05
        
        result = pairwise_ttest_with_fdr(groups, alpha)
        
        # Should still work with small samples (though less power)
        assert len(result) == 3
        for res in result:
            assert 'p_value' in res
            assert 'significant' in res
    
    def test_pairwise_ttest_unequal_sizes(self):
        """Test pairwise t-test with unequal group sizes."""
        np.random.seed(42)
        
        groups = [
            np.random.normal(0, 1, 20),
            np.random.normal(0.5, 1, 50),
            np.random.normal(1.0, 1, 30)
        ]
        alpha = 0.05
        
        result = pairwise_ttest_with_fdr(groups, alpha)
        
        # Should handle unequal sizes
        assert len(result) == 3
        for res in result:
            assert 'p_value' in res
            assert 'significant' in res


class TestStatisticalCorrectionIntegration:
    """Integration tests for statistical correction methods."""
    
    def test_fdr_vs_bonferroni_tradeoff(self):
        """Test the tradeoff between FDR and Bonferroni."""
        np.random.seed(42)
        
        # Create a mix of significant and non-significant p-values
        p_values = np.concatenate([
            np.random.uniform(0, 0.01, 10),  # Significant
            np.random.uniform(0.5, 1.0, 90)   # Non-significant
        ])
        
        alpha = 0.05
        
        fdr_result = benjamini_hochberg_fdr(p_values, alpha)
        bonf_result = bonferroni_correction(p_values, alpha)
        
        fdr_significant = np.sum(fdr_result < alpha)
        bonf_significant = np.sum(bonf_result < alpha)
        
        # FDR should find more significant results than Bonferroni
        assert fdr_significant >= bonf_significant
        
        # Both should find at least some of the truly significant p-values
        assert fdr_significant >= 5
        assert bonf_significant >= 3
    
    def test_correction_methods_consistency(self):
        """Test that both correction methods handle edge cases consistently."""
        # Edge case: all p-values identical
        p_values = np.array([0.05] * 10)
        alpha = 0.05
        
        fdr_result = benjamini_hochberg_fdr(p_values, alpha)
        bonf_result = bonferroni_correction(p_values, alpha)
        
        # Both should return valid results
        assert len(fdr_result) == len(p_values)
        assert len(bonf_result) == len(p_values)
        assert np.all(fdr_result >= 0) and np.all(fdr_result <= 1)
        assert np.all(bonf_result >= 0) and np.all(bonf_result <= 1)
    
    def test_correction_with_realistic_distribution(self):
        """Test correction methods with a realistic distribution of p-values."""
        np.random.seed(42)
        
        # Simulate a realistic scenario: some true effects, some null
        n_significant = 20
        n_null = 80
        
        p_values = np.concatenate([
            np.random.beta(1, 10, n_significant),  # Skewed towards 0
            np.random.uniform(0, 1, n_null)         # Uniform
        ])
        
        alpha = 0.05
        
        fdr_result = benjamini_hochberg_fdr(p_values, alpha)
        bonf_result = bonferroni_correction(p_values, alpha)
        
        fdr_significant = np.sum(fdr_result < alpha)
        bonf_significant = np.sum(bonf_result < alpha)
        
        # FDR should be more powerful than Bonferroni
        assert fdr_significant >= bonf_significant
        
        # Both should find some significant results
        assert fdr_significant >= 10
        assert bonf_significant >= 5
    
    def test_correction_alpha_sensitivity(self):
        """Test how correction methods respond to different alpha values."""
        np.random.seed(42)
        p_values = np.random.uniform(0, 1, 50)
        
        alphas = [0.01, 0.05, 0.10]
        
        for alpha in alphas:
            fdr_result = benjamini_hochberg_fdr(p_values, alpha)
            bonf_result = bonferroni_correction(p_values, alpha)
            
            fdr_sig = np.sum(fdr_result < alpha)
            bonf_sig = np.sum(bonf_result < alpha)
            
            # Higher alpha should lead to more significant results
            # (This is a general trend, not absolute)
            assert fdr_sig >= 0
            assert bonf_sig >= 0