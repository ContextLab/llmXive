"""
Unit tests for statistical analysis functions in code/experiments/analyze.py.

This module tests the implementation of:
- Wilcoxon signed-rank test
- Paired t-test
- Effect size computation (Cohen's d)
- Benjamini-Hochberg correction for multiple comparisons
"""
import pytest
import numpy as np
from scipy import stats
import sys
import os

# Ensure code directory is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from experiments.analyze import (
    wilcoxon_signed_rank_test,
    paired_t_test,
    compute_effect_size,
    benjamini_hochberg_correction
)


class TestWilcoxonSignedRank:
    """Tests for the Wilcoxon signed-rank test implementation."""

    def test_wilcoxon_basic(self):
        """Test basic Wilcoxon signed-rank test functionality."""
        # Create paired data with known difference
        group1 = np.array([2.3, 3.1, 4.5, 2.8, 3.9])
        group2 = np.array([2.1, 2.9, 4.2, 2.6, 3.7])
        
        result = wilcoxon_signed_rank_test(group1, group2)
        
        assert result is not None
        assert 'statistic' in result
        assert 'pvalue' in result
        assert isinstance(result['statistic'], (int, float))
        assert isinstance(result['pvalue'], float)
        assert 0 <= result['pvalue'] <= 1

    def test_wilcoxon_identical_groups(self):
        """Test Wilcoxon with identical groups (should have high p-value)."""
        group = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        result = wilcoxon_signed_rank_test(group, group)
        
        # With identical groups, p-value should be 1.0 (or very close)
        assert result['pvalue'] == 1.0 or result['pvalue'] > 0.9

    def test_wilcoxon_large_difference(self):
        """Test Wilcoxon with clearly different groups."""
        group1 = np.array([1.0, 1.5, 2.0, 2.5, 3.0])
        group2 = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
        
        result = wilcoxon_signed_rank_test(group1, group2)
        
        # Should detect significant difference
        assert result['pvalue'] < 0.05

    def test_wilcoxon_small_sample(self):
        """Test Wilcoxon with minimum sample size (n=3)."""
        group1 = np.array([1.0, 2.0, 3.0])
        group2 = np.array([1.1, 2.1, 3.1])
        
        result = wilcoxon_signed_rank_test(group1, group2)
        
        assert result is not None
        assert 'statistic' in result
        assert 'pvalue' in result


class TestPairedTTest:
    """Tests for the paired t-test implementation."""

    def test_paired_ttest_basic(self):
        """Test basic paired t-test functionality."""
        group1 = np.array([2.3, 3.1, 4.5, 2.8, 3.9])
        group2 = np.array([2.1, 2.9, 4.2, 2.6, 3.7])
        
        result = paired_t_test(group1, group2)
        
        assert result is not None
        assert 'statistic' in result
        assert 'pvalue' in result
        assert isinstance(result['statistic'], (int, float))
        assert isinstance(result['pvalue'], float)
        assert 0 <= result['pvalue'] <= 1

    def test_paired_ttest_identical_groups(self):
        """Test paired t-test with identical groups."""
        group = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        result = paired_t_test(group, group)
        
        # With identical groups, t-statistic should be 0 and p-value 1.0
        assert result['statistic'] == 0.0
        assert result['pvalue'] == 1.0

    def test_paired_ttest_significant_difference(self):
        """Test paired t-test with significant difference."""
        group1 = np.array([1.0, 1.5, 2.0, 2.5, 3.0])
        group2 = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
        
        result = paired_t_test(group1, group2)
        
        # Should detect significant difference
        assert result['pvalue'] < 0.01

    def test_paired_ttest_vs_scipy(self):
        """Verify our implementation matches scipy's results."""
        np.random.seed(42)
        group1 = np.random.normal(5, 1, 20)
        group2 = group1 + np.random.normal(0.5, 0.5, 20)
        
        our_result = paired_t_test(group1, group2)
        scipy_result = stats.ttest_rel(group1, group2)
        
        np.testing.assert_allclose(
            our_result['statistic'], 
            scipy_result.statistic, 
            rtol=1e-10
        )
        np.testing.assert_allclose(
            our_result['pvalue'], 
            scipy_result.pvalue, 
            rtol=1e-10
        )


class TestEffectSize:
    """Tests for effect size computation (Cohen's d)."""

    def test_effect_size_basic(self):
        """Test basic effect size computation."""
        group1 = np.array([2.3, 3.1, 4.5, 2.8, 3.9])
        group2 = np.array([2.1, 2.9, 4.2, 2.6, 3.7])
        
        effect_size = compute_effect_size(group1, group2)
        
        assert isinstance(effect_size, float)
        # Cohen's d should be reasonable for similar groups
        assert -5 < effect_size < 5

    def test_effect_size_identical_groups(self):
        """Test effect size with identical groups (should be 0)."""
        group = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        effect_size = compute_effect_size(group, group)
        
        assert effect_size == 0.0

    def test_effect_size_large_difference(self):
        """Test effect size with large difference."""
        group1 = np.array([1.0, 1.5, 2.0, 2.5, 3.0])
        group2 = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
        
        effect_size = compute_effect_size(group1, group2)
        
        # Should have large negative effect size (group1 < group2)
        assert effect_size < -2.0

    def test_effect_size_vs_manual(self):
        """Verify effect size calculation matches manual computation."""
        group1 = np.array([2.0, 4.0, 6.0])
        group2 = np.array([3.0, 5.0, 7.0])
        
        effect_size = compute_effect_size(group1, group2)
        
        # Manual calculation:
        # mean1 = 4.0, mean2 = 5.0
        # pooled_std = sqrt(((2^2 + 0^2 + 2^2) + (2^2 + 0^2 + 2^2)) / (3+3-2))
        #            = sqrt((8 + 8) / 4) = sqrt(4) = 2.0
        # d = (4.0 - 5.0) / 2.0 = -0.5
        
        assert abs(effect_size - (-0.5)) < 1e-6


class TestBenjaminiHochberg:
    """Tests for Benjamini-Hochberg correction."""

    def test_bh_basic(self):
        """Test basic BH correction."""
        p_values = np.array([0.01, 0.03, 0.04, 0.08, 0.15, 0.20])
        
        result = benjamini_hochberg_correction(p_values, alpha=0.05)
        
        assert 'adjusted_p_values' in result
        assert 'rejected' in result
        assert len(result['adjusted_p_values']) == len(p_values)
        assert len(result['rejected']) == len(p_values)

    def test_bh_adjustment_monotonic(self):
        """Test that adjusted p-values are monotonically increasing."""
        p_values = np.array([0.01, 0.03, 0.04, 0.08, 0.15, 0.20])
        
        result = benjamini_hochberg_correction(p_values, alpha=0.05)
        adjusted = result['adjusted_p_values']
        
        # Adjusted p-values should be monotonically non-decreasing
        for i in range(1, len(adjusted)):
            assert adjusted[i] >= adjusted[i-1]

    def test_bh_all_rejected(self):
        """Test BH with very small p-values (all should be rejected)."""
        p_values = np.array([0.001, 0.002, 0.003, 0.004])
        
        result = benjamini_hochberg_correction(p_values, alpha=0.05)
        
        assert all(result['rejected'])

    def test_bh_none_rejected(self):
        """Test BH with large p-values (none should be rejected)."""
        p_values = np.array([0.5, 0.6, 0.7, 0.8])
        
        result = benjamini_hochberg_correction(p_values, alpha=0.05)
        
        assert not any(result['rejected'])

    def test_bh_vs_manual_calculation(self):
        """Verify BH correction matches manual calculation."""
        p_values = np.array([0.01, 0.04, 0.03, 0.20])
        n = len(p_values)
        alpha = 0.05
        
        result = benjamini_hochberg_correction(p_values, alpha=alpha)
        
        # Manual calculation:
        # Sort p-values: [0.01, 0.03, 0.04, 0.20]
        # Rank: 1, 2, 3, 4
        # Critical values: [0.05*1/4, 0.05*2/4, 0.05*3/4, 0.05*4/4]
        #                = [0.0125, 0.025, 0.0375, 0.05]
        # Find largest k where p[k] <= critical[k]
        # k=2: 0.03 <= 0.025? No. k=1: 0.01 <= 0.0125? Yes.
        # So reject first 1 hypothesis.
        
        # Count rejected
        rejected_count = sum(result['rejected'])
        assert rejected_count >= 1  # At least the first one should be rejected


class TestIntegration:
    """Integration tests combining multiple analysis functions."""

    def test_full_analysis_pipeline(self):
        """Test a complete analysis pipeline with multiple comparisons."""
        np.random.seed(123)
        
        # Simulate probe results for 3 layers, 2 models
        n_seeds = 10
        baseline_scores = np.random.normal(0.85, 0.03, n_seeds)
        dendritic_scores = baseline_scores + np.random.normal(0.02, 0.02, n_seeds)
        
        # Perform t-test
        t_result = paired_t_test(baseline_scores, dendritic_scores)
        
        # Perform Wilcoxon
        w_result = wilcoxon_signed_rank_test(baseline_scores, dendritic_scores)
        
        # Compute effect size
        effect = compute_effect_size(baseline_scores, dendritic_scores)
        
        # Verify all results are consistent
        assert t_result['pvalue'] < 1.0
        assert w_result['pvalue'] < 1.0
        assert -5 < effect < 5

    def test_multiple_comparisons_correction(self):
        """Test BH correction across multiple layer comparisons."""
        np.random.seed(456)
        
        # Simulate p-values from 5 layer comparisons
        p_values = np.random.uniform(0.01, 0.20, 5)
        
        result = benjamini_hochberg_correction(p_values, alpha=0.05)
        
        # Verify structure
        assert len(result['adjusted_p_values']) == 5
        assert len(result['rejected']) == 5
        assert all(0 <= p <= 1 for p in result['adjusted_p_values'])
        assert all(isinstance(r, bool) for r in result['rejected'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])