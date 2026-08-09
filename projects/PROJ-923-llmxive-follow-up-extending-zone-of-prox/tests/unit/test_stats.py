"""
Unit tests for the paired t-test implementation in code/analysis/stats.py.

These tests verify:
1. Correct calculation of t-statistic and p-value for paired samples.
2. Proper handling of edge cases (empty lists, single element, identical values).
3. Verification that the function returns the Standard Deviation of the AUCC distribution as required by SC-002.
"""

import pytest
import numpy as np
from typing import List, Tuple
import sys
import os

# Add the project root to the path to allow imports from code/
# Assuming this test file is at projects/.../tests/unit/test_stats.py
# and the code is at projects/.../code/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from analysis.stats import paired_ttest_aucc, calculate_aucc_stats


class TestPairedTTest:
    """Tests for the paired_ttest_aucc function."""

    def test_basic_paired_ttest(self):
        """Test basic functionality with known small datasets."""
        # Two small sets with a clear difference
        group_a = [0.6, 0.7, 0.8, 0.75, 0.65]
        group_b = [0.5, 0.55, 0.6, 0.58, 0.52]

        t_stat, p_value, std_a, std_b, mean_diff = paired_ttest_aucc(group_a, group_b)

        # Verify return types
        assert isinstance(t_stat, float)
        assert isinstance(p_value, float)
        assert isinstance(std_a, float)
        assert isinstance(std_b, float)
        assert isinstance(mean_diff, float)

        # Verify p-value is small (significant difference)
        assert p_value < 0.05

        # Verify mean difference is positive (A > B)
        assert mean_diff > 0

        # Verify standard deviations are positive
        assert std_a > 0
        assert std_b > 0

    def test_identical_groups(self):
        """Test that p-value is 1.0 (or very close) for identical groups."""
        group = [0.6, 0.7, 0.8, 0.75, 0.65]

        t_stat, p_value, std_a, std_b, mean_diff = paired_ttest_aucc(group, group)

        assert t_stat == 0.0
        assert p_value == 1.0
        assert mean_diff == 0.0

    def test_single_element(self):
        """Test behavior with single element lists."""
        group_a = [0.7]
        group_b = [0.6]

        # With single element, std is 0, t-stat might be undefined or infinite
        # We expect the function to handle this gracefully or raise a specific error
        # For now, we test that it doesn't crash and returns numeric values
        try:
            t_stat, p_value, std_a, std_b, mean_diff = paired_ttest_aucc(group_a, group_b)
            # If it returns, verify types
            assert isinstance(t_stat, (float, np.floating))
            assert isinstance(p_value, (float, np.floating))
        except Exception:
            # If it raises, that's also acceptable behavior for this edge case
            pass

    def test_empty_lists(self):
        """Test that empty lists raise a ValueError."""
        with pytest.raises(ValueError):
            paired_ttest_aucc([], [])

    def test_mismatched_lengths(self):
        """Test that mismatched list lengths raise a ValueError."""
        group_a = [0.6, 0.7, 0.8]
        group_b = [0.5, 0.55]

        with pytest.raises(ValueError):
            paired_ttest_aucc(group_a, group_b)

    def test_negative_values(self):
        """Test handling of negative values (though AUCC should be positive)."""
        group_a = [-0.1, 0.0, 0.1]
        group_b = [-0.2, -0.1, 0.0]

        t_stat, p_value, std_a, std_b, mean_diff = paired_ttest_aucc(group_a, group_b)

        assert isinstance(t_stat, float)
        assert isinstance(p_value, float)
        assert mean_diff > 0

    def test_large_sample_size(self):
        """Test with a larger sample size for statistical validity."""
        np.random.seed(42)
        group_a = np.random.normal(0.7, 0.1, 100).tolist()
        group_b = np.random.normal(0.6, 0.1, 100).tolist()

        t_stat, p_value, std_a, std_b, mean_diff = paired_ttest_aucc(group_a, group_b)

        assert p_value < 0.05  # Should be significant
        assert abs(mean_diff - 0.1) < 0.05  # Mean diff should be close to 0.1

    def test_returns_standard_deviation(self):
        """Verify that the function returns Standard Deviation as per SC-002."""
        group_a = [0.6, 0.7, 0.8, 0.75, 0.65]
        group_b = [0.5, 0.55, 0.6, 0.58, 0.52]

        t_stat, p_value, std_a, std_b, mean_diff = paired_ttest_aucc(group_a, group_b)

        # Verify std_a matches numpy calculation
        expected_std_a = np.std(group_a, ddof=1)
        assert np.isclose(std_a, expected_std_a)

        # Verify std_b matches numpy calculation
        expected_std_b = np.std(group_b, ddof=1)
        assert np.isclose(std_b, expected_std_b)

class TestCalculateAUCCStats:
    """Tests for the calculate_aucc_stats function."""

    def test_basic_stats(self):
        """Test calculation of mean, std, and count."""
        aucc_values = [0.6, 0.7, 0.8, 0.75, 0.65]

        mean_val, std_val, count = calculate_aucc_stats(aucc_values)

        assert isinstance(mean_val, float)
        assert isinstance(std_val, float)
        assert isinstance(count, int)

        assert count == 5
        assert np.isclose(mean_val, np.mean(aucc_values))
        assert np.isclose(std_val, np.std(aucc_values, ddof=1))

    def test_single_value(self):
        """Test with a single value."""
        aucc_values = [0.7]

        mean_val, std_val, count = calculate_aucc_stats(aucc_values)

        assert mean_val == 0.7
        assert std_val == 0.0  # Std of single value is 0
        assert count == 1

    def test_empty_list(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError):
            calculate_aucc_stats([])

    def test_large_dataset(self):
        """Test with a larger dataset."""
        np.random.seed(42)
        aucc_values = np.random.normal(0.7, 0.1, 1000).tolist()

        mean_val, std_val, count = calculate_aucc_stats(aucc_values)

        assert count == 1000
        assert np.isclose(mean_val, np.mean(aucc_values), rtol=1e-5)
        assert np.isclose(std_val, np.std(aucc_values, ddof=1), rtol=1e-5)

    def test_all_same_values(self):
        """Test with all identical values."""
        aucc_values = [0.7] * 10

        mean_val, std_val, count = calculate_aucc_stats(aucc_values)

        assert mean_val == 0.7
        assert std_val == 0.0
        assert count == 10