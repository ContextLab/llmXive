"""
Unit tests for statistical analysis functions in code/experiments/analyze.py.

This module tests the implementation of:
- Wilcoxon signed-rank test
- Paired t-test
- Benjamini-Hochberg correction
- Effect size computation (Cohen's d)

These tests verify the correctness of statistical functions used in US3
for hierarchical feature probing and statistical analysis.
"""

import pytest
import numpy as np
from scipy import stats

# Import functions from the analyze module
# Note: We add the code directory to path to import from experiments.analyze
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from experiments.analyze import (
    wilcoxon_signed_rank_test,
    paired_t_test,
    benjamini_hochberg_correction,
    compute_effect_size
)


class TestWilcoxonSignedRankTest:
    """Tests for the Wilcoxon signed-rank test implementation."""

    def test_wilcoxon_basic(self):
        """Test Wilcoxon test with simple paired data."""
        # Create paired data with known difference
        group1 = np.array([10, 12, 15, 11, 13, 14, 16, 12, 11, 13])
        group2 = np.array([9, 11, 14, 10, 12, 13, 15, 11, 10, 12])
        
        result = wilcoxon_signed_rank_test(group1, group2)
        
        # Verify result structure
        assert 'statistic' in result
        assert 'p_value' in result
        
        # Verify values are numeric
        assert isinstance(result['statistic'], (int, float))
        assert isinstance(result['p_value'], (int, float))
        
        # Verify p-value is in valid range
        assert 0 <= result['p_value'] <= 1
        
        # Verify statistic is non-negative
        assert result['statistic'] >= 0

    def test_wilcoxon_identical_groups(self):
        """Test Wilcoxon test with identical groups (should have high p-value)."""
        group = np.array([10, 12, 15, 11, 13])
        
        result = wilcoxon_signed_rank_test(group, group)
        
        # With identical groups, p-value should be 1.0 (or very close)
        assert result['p_value'] == 1.0

    def test_wilcoxon_against_scipy(self):
        """Compare our implementation with scipy's wilcoxon."""
        np.random.seed(42)
        group1 = np.random.normal(10, 2, 20)
        group2 = np.random.normal(10.5, 2, 20)
        
        our_result = wilcoxon_signed_rank_test(group1, group2)
        scipy_stat, scipy_p = stats.wilcoxon(group1, group2)
        
        # Allow for small numerical differences
        assert abs(our_result['statistic'] - scipy_stat) < 1e-6
        assert abs(our_result['p_value'] - scipy_p) < 1e-6


class TestPairedTTest:
    """Tests for the paired t-test implementation."""

    def test_ttest_basic(self):
        """Test paired t-test with simple data."""
        group1 = np.array([10, 12, 15, 11, 13, 14, 16, 12, 11, 13])
        group2 = np.array([9, 11, 14, 10, 12, 13, 15, 11, 10, 12])
        
        result = paired_t_test(group1, group2)
        
        # Verify result structure
        assert 'statistic' in result
        assert 'p_value' in result
        
        # Verify values are numeric
        assert isinstance(result['statistic'], (int, float))
        assert isinstance(result['p_value'], (int, float))
        
        # Verify p-value is in valid range
        assert 0 <= result['p_value'] <= 1

    def test_ttest_identical_groups(self):
        """Test paired t-test with identical groups."""
        group = np.array([10, 12, 15, 11, 13])
        
        result = paired_t_test(group, group)
        
        # With identical groups, p-value should be 1.0
        assert result['p_value'] == 1.0

    def test_ttest_against_scipy(self):
        """Compare our implementation with scipy's ttest_rel."""
        np.random.seed(42)
        group1 = np.random.normal(10, 2, 20)
        group2 = np.random.normal(10.5, 2, 20)
        
        our_result = paired_t_test(group1, group2)
        scipy_stat, scipy_p = stats.ttest_rel(group1, group2)
        
        # Allow for small numerical differences
        assert abs(our_result['statistic'] - scipy_stat) < 1e-6
        assert abs(our_result['p_value'] - scipy_p) < 1e-6


class TestBenjaminiHochbergCorrection:
    """Tests for the Benjamini-Hochberg correction implementation."""

    def test_bh_basic(self):
        """Test BH correction with simple p-values."""
        p_values = np.array([0.01, 0.03, 0.05, 0.07, 0.10, 0.20])
        
        result = benjamini_hochberg_correction(p_values)
        
        # Verify result structure
        assert 'adjusted_p_values' in result
        assert 'significant' in result
        
        # Verify lengths match
        assert len(result['adjusted_p_values']) == len(p_values)
        assert len(result['significant']) == len(p_values)
        
        # Verify adjusted p-values are in valid range
        assert all(0 <= p <= 1 for p in result['adjusted_p_values'])
        
        # Verify significant is boolean array
        assert all(isinstance(s, bool) for s in result['significant'])

    def test_bh_monotonicity(self):
        """Test that adjusted p-values are monotonically increasing."""
        # Create p-values that are not sorted
        p_values = np.array([0.05, 0.01, 0.10, 0.03, 0.07])
        
        result = benjamini_hochberg_correction(p_values)
        adjusted = result['adjusted_p_values']
        
        # After BH correction, adjusted p-values should be monotonically increasing
        # when sorted by original p-value order
        sorted_indices = np.argsort(p_values)
        sorted_adjusted = adjusted[sorted_indices]
        
        # Check monotonicity
        for i in range(1, len(sorted_adjusted)):
            assert sorted_adjusted[i] >= sorted_adjusted[i-1] - 1e-10

    def test_bh_against_manual_calculation(self):
        """Test BH correction against manual calculation."""
        p_values = np.array([0.01, 0.04, 0.03, 0.20])
        n = len(p_values)
        
        # Manual BH calculation
        sorted_indices = np.argsort(p_values)
        sorted_p = p_values[sorted_indices]
        
        expected_adjusted = np.zeros(n)
        for i in range(n):
            expected_adjusted[sorted_indices[i]] = sorted_p[i] * n / (i + 1)
        
        # Ensure monotonicity (cumulative min from the end)
        for i in range(n-2, -1, -1):
            expected_adjusted[sorted_indices[i]] = min(
                expected_adjusted[sorted_indices[i]],
                expected_adjusted[sorted_indices[i+1]]
            )
        
        # Ensure values don't exceed 1
        expected_adjusted = np.clip(expected_adjusted, 0, 1)
        
        result = benjamini_hochberg_correction(p_values)
        
        # Compare with tolerance
        assert np.allclose(result['adjusted_p_values'], expected_adjusted, rtol=1e-5)

    def test_bh_significance_threshold(self):
        """Test BH significance at different thresholds."""
        p_values = np.array([0.001, 0.01, 0.02, 0.05, 0.10, 0.20])
        
        # Test at alpha = 0.05
        result = benjamini_hochberg_correction(p_values, alpha=0.05)
        
        # Count significant results
        significant_count = sum(result['significant'])
        
        # Should have some significant results but not all
        assert 0 < significant_count < len(p_values)

    def test_bh_empty_input(self):
        """Test BH correction with empty input."""
        p_values = np.array([])
        
        result = benjamini_hochberg_correction(p_values)
        
        assert len(result['adjusted_p_values']) == 0
        assert len(result['significant']) == 0


class TestComputeEffectSize:
    """Tests for effect size computation (Cohen's d)."""

    def test_effect_size_basic(self):
        """Test effect size with simple data."""
        group1 = np.array([10, 12, 15, 11, 13])
        group2 = np.array([9, 11, 14, 10, 12])
        
        result = compute_effect_size(group1, group2)
        
        # Verify result structure
        assert 'cohen_d' in result
        assert 'interpretation' in result
        
        # Verify cohen_d is numeric
        assert isinstance(result['cohen_d'], (int, float))
        
        # Verify interpretation is a string
        assert isinstance(result['interpretation'], str)

    def test_effect_size_identical_groups(self):
        """Test effect size with identical groups (should be 0)."""
        group = np.array([10, 12, 15, 11, 13])
        
        result = compute_effect_size(group, group)
        
        assert result['cohen_d'] == 0.0
        assert 'none' in result['interpretation'].lower()

    def test_effect_size_large_difference(self):
        """Test effect size with large difference between groups."""
        group1 = np.array([10, 12, 15, 11, 13])
        group2 = np.array([20, 22, 25, 21, 23])
        
        result = compute_effect_size(group1, group2)
        
        # Large difference should give large effect size
        assert abs(result['cohen_d']) > 2.0
        assert 'large' in result['interpretation'].lower()

    def test_effect_size_negative(self):
        """Test effect size when group2 > group1."""
        group1 = np.array([20, 22, 25, 21, 23])
        group2 = np.array([10, 12, 15, 11, 13])
        
        result = compute_effect_size(group1, group2)
        
        # Should be negative
        assert result['cohen_d'] < 0

    def test_effect_size_interpretation_ranges(self):
        """Test that interpretation matches standard Cohen's d ranges."""
        # Small effect (~0.2)
        group1 = np.random.normal(0, 1, 100)
        group2 = np.random.normal(0.2, 1, 100)
        result = compute_effect_size(group1, group2)
        assert 'small' in result['interpretation'].lower() or 'negligible' in result['interpretation'].lower()
        
        # Medium effect (~0.5)
        group2 = np.random.normal(0.5, 1, 100)
        result = compute_effect_size(group1, group2)
        assert 'medium' in result['interpretation'].lower()
        
        # Large effect (~0.8)
        group2 = np.random.normal(0.8, 1, 100)
        result = compute_effect_size(group1, group2)
        assert 'large' in result['interpretation'].lower()

    def test_effect_size_against_manual_calculation(self):
        """Compare effect size with manual calculation."""
        group1 = np.array([10, 12, 15, 11, 13, 14, 16, 12, 11, 13])
        group2 = np.array([9, 11, 14, 10, 12, 13, 15, 11, 10, 12])
        
        # Manual Cohen's d calculation
        mean_diff = np.mean(group1) - np.mean(group2)
        pooled_std = np.sqrt((np.var(group1, ddof=1) + np.var(group2, ddof=1)) / 2)
        expected_d = mean_diff / pooled_std
        
        result = compute_effect_size(group1, group2)
        
        assert abs(result['cohen_d'] - expected_d) < 1e-6


class TestIntegration:
    """Integration tests for the complete analysis pipeline."""

    def test_full_analysis_workflow(self):
        """Test the complete workflow from test data to results."""
        # Simulate probe results from multiple layers
        np.random.seed(42)
        
        # Create synthetic probe results (in practice, these come from probe.py)
        n_layers = 5
        n_seeds = 10
        
        baseline_scores = np.random.normal(0.85, 0.02, (n_layers, n_seeds))
        dendritic_scores = np.random.normal(0.87, 0.02, (n_layers, n_seeds))
        
        results = []
        for layer_idx in range(n_layers):
            # Perform statistical tests
            t_test_result = paired_t_test(
                baseline_scores[layer_idx],
                dendritic_scores[layer_idx]
            )
            
            wilcoxon_result = wilcoxon_signed_rank_test(
                baseline_scores[layer_idx],
                dendritic_scores[layer_idx]
            )
            
            effect_size_result = compute_effect_size(
                baseline_scores[layer_idx],
                dendritic_scores[layer_idx]
            )
            
            results.append({
                'layer': layer_idx,
                't_test': t_test_result,
                'wilcoxon': wilcoxon_result,
                'effect_size': effect_size_result,
                'baseline_mean': np.mean(baseline_scores[layer_idx]),
                'dendritic_mean': np.mean(dendritic_scores[layer_idx])
            })
        
        # Collect all p-values for BH correction
        all_p_values = np.array([r['t_test']['p_value'] for r in results])
        
        # Apply BH correction
        bh_result = benjamini_hochberg_correction(all_p_values)
        
        # Verify results structure
        assert len(results) == n_layers
        assert len(bh_result['adjusted_p_values']) == n_layers
        assert len(bh_result['significant']) == n_layers
        
        # Verify at least some results are processed
        assert all(r['baseline_mean'] > 0 for r in results)
        assert all(r['dendritic_mean'] > 0 for r in results)

    def test_consistency_across_tests(self):
        """Test that t-test and Wilcoxon give consistent directions."""
        np.random.seed(42)
        
        # Create data where we expect a difference
        group1 = np.random.normal(0.85, 0.02, 20)
        group2 = np.random.normal(0.90, 0.02, 20)
        
        t_result = paired_t_test(group1, group2)
        w_result = wilcoxon_signed_rank_test(group1, group2)
        
        # Both tests should agree on significance (both significant or both not)
        # This is a soft check - they don't have to be identical
        t_significant = t_result['p_value'] < 0.05
        w_significant = w_result['p_value'] < 0.05
        
        # They should generally agree (80%+ of the time in repeated trials)
        # For this single test, we just check they're not contradictory
        # (e.g., one extremely significant, one not significant at all)
        assert not (t_result['p_value'] < 0.001 and w_result['p_value'] > 0.5)
        assert not (w_result['p_value'] < 0.001 and t_result['p_value'] > 0.5)