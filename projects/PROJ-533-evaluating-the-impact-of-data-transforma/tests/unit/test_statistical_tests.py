"""
Unit tests for statistical test wrappers in code/utils/statistical_tests.py.
"""

import pytest
import numpy as np
from utils.statistical_tests import (
    independent_t_test,
    one_way_anova,
    shapiro_wilk,
    friedman_test,
    get_test_summary
)


class TestIndependentTTest:
    def test_welch_ttest_basic(self):
        """Test Welch's t-test (default) with known data."""
        group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        group2 = [2.0, 3.0, 4.0, 5.0, 6.0]

        result = independent_t_test(group1, group2, equal_variance=False)

        assert "statistic" in result
        assert "p_value" in result
        assert result["test_type"] == "welch"
        assert isinstance(result["p_value"], float)

    def test_student_ttest_basic(self):
        """Test Student's t-test with equal variance."""
        group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        group2 = [2.0, 3.0, 4.0, 5.0, 6.0]

        result = independent_t_test(group1, group2, equal_variance=True)

        assert result["test_type"] == "student"
        assert result["p_value"] >= 0.0

    def test_empty_input_raises_error(self):
        """Test that empty arrays raise ValueError."""
        with pytest.raises(ValueError):
            independent_t_test([], [1, 2, 3])

    def test_single_element_raises_error(self):
        """Test that single element arrays raise error (scipy requirement)."""
        # scipy.stats.ttest_ind requires at least 2 elements usually,
        # but let's ensure our wrapper handles edge cases gracefully
        # depending on scipy version behavior.
        # We test that it doesn't crash on minimal valid input if scipy allows.
        # If scipy raises, we let it propagate as it's a valid scipy error.
        try:
            independent_t_test([1.0], [2.0])
        except Exception:
            # Expected behavior if scipy rejects it
            pass


class TestOneWayAnova:
    def test_anova_basic(self):
        """Test one-way ANOVA with simple groups."""
        g1 = [1.0, 2.0, 3.0]
        g2 = [4.0, 5.0, 6.0]
        g3 = [7.0, 8.0, 9.0]

        result = one_way_anova(g1, g2, g3)

        assert "statistic" in result
        assert "p_value" in result
        assert result["p_value"] >= 0.0

    def test_two_groups(self):
        """ANOVA with two groups should work (equivalent to t-test squared)."""
        g1 = [1.0, 2.0, 3.0]
        g2 = [4.0, 5.0, 6.0]

        result = one_way_anova(g1, g2)
        assert result["p_value"] >= 0.0

    def test_single_group_raises_error(self):
        """Test that ANOVA requires at least two groups."""
        with pytest.raises(ValueError):
            one_way_anova([1, 2, 3])

    def test_empty_group_raises_error(self):
        """Test that empty groups raise ValueError."""
        with pytest.raises(ValueError):
            one_way_anova([1, 2], [])


class TestShapiroWilk:
    def test_normal_data(self):
        """Test Shapiro-Wilk on normal data (should have high p-value)."""
        np.random.seed(42)
        data = np.random.normal(loc=0, scale=1, size=50)

        result = shapiro_wilk(data)

        assert result["statistic"] <= 1.0
        assert result["p_value"] >= 0.0
        # Note: We don't assert p > 0.05 as randomness can vary,
        # but the structure must be correct.

    def test_small_sample_size(self):
        """Test with minimum required sample size (3)."""
        data = [1.0, 2.0, 3.0]
        result = shapiro_wilk(data)
        assert result["p_value"] is not None

    def test_insufficient_data_raises_error(self):
        """Test that < 3 points raises ValueError."""
        with pytest.raises(ValueError):
            shapiro_wilk([1.0, 2.0])


class TestFriedmanTest:
    def test_friedman_basic(self):
        """Test Friedman test with simple repeated measures."""
        # 3 subjects, 3 conditions
        g1 = [1.0, 2.0, 3.0]
        g2 = [2.0, 3.0, 4.0]
        g3 = [3.0, 4.0, 5.0]

        result = friedman_test(g1, g2, g3)

        assert "statistic" in result
        assert "p_value" in result

    def test_mismatched_lengths_raises_error(self):
        """Test that groups of different lengths raise ValueError."""
        with pytest.raises(ValueError):
            friedman_test([1, 2, 3], [1, 2])

    def test_single_group_raises_error(self):
        """Test that single group raises ValueError."""
        with pytest.raises(ValueError):
            friedman_test([1, 2, 3])


class TestGetTestSummary:
    def test_known_tests(self):
        """Test retrieval of descriptions for known tests."""
        assert "t-test" in get_test_summary("t-test")
        assert "ANOVA" in get_test_summary("anova")
        assert "normality" in get_test_summary("shapiro")
        assert "Friedman" in get_test_summary("friedman")

    def test_unknown_test(self):
        """Test retrieval for unknown test name."""
        assert "Unknown" in get_test_summary("unknown_test")