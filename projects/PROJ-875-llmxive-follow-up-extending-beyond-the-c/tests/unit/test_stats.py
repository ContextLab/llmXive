"""
Unit tests for Mann-Whitney U test implementation in code/stats.py.

This module validates the statistical analysis logic required for User Story 3,
specifically the one-tailed Mann-Whitney U test (FR-005) used to compare
Memory Gap scores between Text Agent and Baseline Agent.
"""
import pytest
import numpy as np
from scipy import stats as scipy_stats
import sys
import os

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.stats import mann_whitney_u_test, calculate_effect_size

class TestMannWhitneyUTest:
    """Tests for the mann_whitney_u_test function."""

    def test_basic_one_tailed_greater(self):
        """Test standard one-tailed test (group1 > group2)."""
        group1 = [10, 12, 11, 13, 14]
        group2 = [5, 6, 7, 8, 9]
        
        # scipy returns two-tailed p-value, we need to convert for one-tailed
        # For one-tailed 'greater', if the statistic supports the direction, p/2
        u_stat, p_two_tailed = scipy_stats.mannwhitneyu(group1, group2, alternative='two-sided')
        
        result = mann_whitney_u_test(group1, group2, alternative='greater')
        
        assert result['statistic'] == pytest.approx(u_stat)
        # For 'greater' test where group1 is actually larger, p-value should be p_two_tailed / 2
        expected_p = p_two_tailed / 2
        assert result['p_value'] == pytest.approx(expected_p)
        assert result['alternative'] == 'greater'
        assert result['significant_at_0.05'] is True

    def test_basic_one_tailed_less(self):
        """Test standard one-tailed test (group1 < group2)."""
        group1 = [5, 6, 7, 8, 9]
        group2 = [10, 12, 11, 13, 14]
        
        result = mann_whitney_u_test(group1, group2, alternative='less')
        
        assert result['alternative'] == 'less'
        # group1 is smaller, so p-value should be small (significant)
        assert result['significant_at_0.05'] is True

    def test_equal_groups(self):
        """Test when groups are identical (should not be significant)."""
        group1 = [1, 2, 3, 4, 5]
        group2 = [1, 2, 3, 4, 5]
        
        result = mann_whitney_u_test(group1, group2, alternative='greater')
        
        assert result['p_value'] == pytest.approx(0.5)
        assert result['significant_at_0.05'] is False

    def test_different_sample_sizes(self):
        """Test with unequal sample sizes."""
        group1 = [10, 12, 11, 13, 14, 15, 16]
        group2 = [5, 6, 7]
        
        result = mann_whitney_u_test(group1, group2, alternative='greater')
        
        assert 'statistic' in result
        assert 'p_value' in result
        assert 0 <= result['p_value'] <= 1
        assert result['significant_at_0.05'] is True

    def test_with_ties(self):
        """Test handling of tied values."""
        group1 = [10, 10, 12, 12, 14]
        group2 = [8, 8, 9, 9, 11]
        
        result = mann_whitney_u_test(group1, group2, alternative='greater')
        
        assert 'statistic' in result
        assert 'p_value' in result
        assert result['significant_at_0.05'] is True

    def test_invalid_alternative(self):
        """Test that invalid alternative parameter raises error."""
        group1 = [1, 2, 3]
        group2 = [4, 5, 6]
        
        with pytest.raises(ValueError):
            mann_whitney_u_test(group1, group2, alternative='invalid')

    def test_empty_list(self):
        """Test handling of empty input lists."""
        group1 = []
        group2 = [1, 2, 3]
        
        with pytest.raises(ValueError):
            mann_whitney_u_test(group1, group2, alternative='greater')

    def test_single_sample(self):
        """Test with single sample in each group."""
        group1 = [5]
        group2 = [10]
        
        # Mann-Whitney U requires at least 2 samples for reliable p-value calculation
        # scipy will raise an error or return NaN for very small samples
        with pytest.raises(Exception):
            mann_whitney_u_test(group1, group2, alternative='greater')

    def test_all_identical_values(self):
        """Test when all values in both groups are identical."""
        group1 = [5, 5, 5, 5]
        group2 = [5, 5, 5, 5]
        
        result = mann_whitney_u_test(group1, group2, alternative='greater')
        
        assert result['p_value'] == pytest.approx(0.5)
        assert result['significant_at_0.05'] is False

    def test_memory_gap_scenario(self):
        """
        Test scenario relevant to Memory Gap analysis:
        Text Agent (group1) should have lower Memory Gap than Baseline (group2)
        if the hypothesis is that text-only agents retain state better.
        We test 'less' alternative.
        """
        # Simulated Memory Gap scores (lower is better)
        text_agent_scores = [0.12, 0.15, 0.11, 0.14, 0.13, 0.16, 0.10]
        baseline_scores = [0.25, 0.28, 0.22, 0.27, 0.24, 0.26, 0.23]
        
        result = mann_whitney_u_test(text_agent_scores, baseline_scores, alternative='less')
        
        assert result['alternative'] == 'less'
        assert result['significant_at_0.05'] is True
        assert result['p_value'] < 0.05

class TestCalculateEffectSize:
    """Tests for the calculate_effect_size function (common in Mann-Whitney analysis)."""

    def test_r_calculation(self):
        """Test calculation of r effect size statistic."""
        u_stat = 15.0
        n1 = 10
        n2 = 10
        
        result = calculate_effect_size(u_stat, n1, n2)
        
        # r = Z / sqrt(N) where Z is approximated from U
        # For U=15, n1=10, n2=10, expected r should be reasonable (0-1 range)
        assert 0 <= result <= 1

    def test_effect_size_interpretation(self):
        """Test that effect size follows standard interpretation guidelines."""
        # Small effect (r ≈ 0.1)
        small_result = calculate_effect_size(45, 10, 10)
        assert small_result >= 0.1  # Should be at least small effect

        # Large effect (r ≈ 0.5+)
        large_result = calculate_effect_size(5, 10, 10)
        assert large_result > 0.3  # Should be medium to large effect

if __name__ == '__main__':
    pytest.main([__file__, '-v'])