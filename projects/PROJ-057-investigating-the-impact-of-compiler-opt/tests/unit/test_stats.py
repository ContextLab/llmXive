"""
Unit tests for statistical analysis functions in code/analysis/stats.py
"""
import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.stats import (
    compute_block_averages,
    aggregate_block_averages,
    welch_ttest,
    MIN_BLOCKS_FOR_STATS,
    BLOCK_SIZE
)


class TestBlockAveraging:
    """Tests for block-averaging logic."""

    def test_compute_block_averages_basic(self):
        """Test basic block averaging with even division."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        block_size = 4
        
        result = compute_block_averages(data, block_size)
        
        # Expected: [(1+2+3+4)/4, (5+6+7+8)/4] = [2.5, 6.5]
        assert len(result) == 2
        assert np.isclose(result[0], 2.5)
        assert np.isclose(result[1], 6.5)

    def test_compute_block_averages_partial_block(self):
        """Test handling of partial final block."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
        block_size = 4
        
        result = compute_block_averages(data, block_size)
        
        # First block: [1,2,3,4] -> 2.5
        # Second block: [5,6,7] (3 items, >= half of 4) -> 6.0
        assert len(result) == 2
        assert np.isclose(result[0], 2.5)
        assert np.isclose(result[1], 6.0)

    def test_compute_block_averages_small_partial_block(self):
        """Test that very small partial blocks are excluded."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        block_size = 4
        
        result = compute_block_averages(data, block_size)
        
        # First block: [1,2,3,4] -> 2.5
        # Second block: [5] (1 item, < half of 4) -> excluded
        assert len(result) == 1
        assert np.isclose(result[0], 2.5)

    def test_compute_block_averages_empty(self):
        """Test empty input."""
        result = compute_block_averages([], 4)
        assert result == []

    def test_aggregate_block_averages_filters_insufficient(self):
        """Test that configs with too few blocks are filtered out."""
        data = {
            'config_a': [1.0] * 100,  # 4 blocks of 25
            'config_b': [1.0] * 50,   # 2 blocks of 25 (insufficient)
            'config_c': [1.0] * 200   # 8 blocks of 25
        }
        
        result = aggregate_block_averages(data, block_size=25, min_blocks=4)
        
        assert 'config_a' in result
        assert 'config_b' not in result  # Only 2 blocks
        assert 'config_c' in result


class TestWelchTTest:
    """Tests for Welch's t-test implementation."""

    def test_welch_ttest_significance(self):
        """
        Test Welch's t-test with clearly different means.
        
        This test verifies that the function correctly detects
        statistically significant differences between two samples.
        """
        # Sample 1: mean ~ 10, std ~ 2
        sample1 = np.random.RandomState(42).normal(10, 2, 50)
        # Sample 2: mean ~ 15, std ~ 2 (clearly different)
        sample2 = np.random.RandomState(43).normal(15, 2, 50)
        
        t_stat, p_val, info = welch_ttest(sample1, sample2)
        
        assert p_val < 0.05, "Should detect significant difference"
        assert info['null_rejected'] is True
        assert np.isclose(info['mean1'], 10, atol=1)
        assert np.isclose(info['mean2'], 15, atol=1)

    def test_welch_ttest_no_significance(self):
        """Test with samples that have similar means."""
        # Both samples from same distribution
        sample1 = np.random.RandomState(42).normal(10, 2, 50)
        sample2 = np.random.RandomState(43).normal(10, 2, 50)
        
        t_stat, p_val, info = welch_ttest(sample1, sample2)
        
        # With same distribution, p-value should typically be > 0.05
        # (Note: 5% chance of false positive, but unlikely with fixed seeds)
        assert info['null_rejected'] is False

    def test_welch_ttest_unequal_variance(self):
        """Test Welch's correction handles unequal variances."""
        # Sample 1: low variance
        sample1 = np.random.RandomState(42).normal(10, 1, 50)
        # Sample 2: high variance, same mean
        sample2 = np.random.RandomState(43).normal(10, 5, 50)
        
        t_stat, p_val, info = welch_ttest(sample1, sample2)
        
        # Should not reject null (means are equal)
        assert info['null_rejected'] is False

    def test_welch_ttest_insufficient_data(self):
        """Test error handling for insufficient data."""
        with pytest.raises(ValueError):
            welch_ttest([1.0], [2.0, 3.0, 4.0])

    def test_welch_ttest_returns_info_dict(self):
        """Test that result includes all expected fields."""
        sample1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        sample2 = [2.0, 3.0, 4.0, 5.0, 6.0]
        
        t_stat, p_val, info = welch_ttest(sample1, sample2)
        
        assert 'n1' in info
        assert 'n2' in info
        assert 'mean1' in info
        assert 'mean2' in info
        assert 'std1' in info
        assert 'std2' in info
        assert 'hypothesis' in info
        assert 'null_rejected' in info

    def test_welch_ttest_alternative_hypothesis(self):
        """Test different alternative hypotheses."""
        sample1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        sample2 = [6.0, 7.0, 8.0, 9.0, 10.0]
        
        # Two-sided (default)
        _, p_two, _ = welch_ttest(sample1, sample2, 'two-sided')
        # Less (sample1 < sample2)
        _, p_less, _ = welch_ttest(sample1, sample2, 'less')
        # Greater (sample1 > sample2)
        _, p_greater, _ = welch_ttest(sample1, sample2, 'greater')
        
        # Since sample2 > sample1, 'less' should have very low p-value
        assert p_less < 0.01
        # 'greater' should have high p-value
        assert p_greater > 0.9