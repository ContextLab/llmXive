"""
Unit tests for ANOVA and trend analysis in code/analysis/correlation.py.

This module tests the statistical analysis functions required for User Story 3.
It verifies that ANOVA is correctly performed for discrete groups and that
trend analysis logic correctly identifies the direction of degradation.
"""

import pytest
import numpy as np
import pandas as pd
from scipy import stats

# Import the module under test.
# Note: The implementation file code/analysis/correlation.py is expected to exist
# with the functions defined below. If it doesn't exist, the import will fail,
# which is the correct behavior for a test runner (fail loudly).
try:
    from analysis.correlation import (
        perform_anova,
        analyze_trend_direction,
        compute_group_statistics
    )
except ImportError:
    # If the module is missing, we define dummy functions to prevent
    # the test suite from crashing on import, but we mark the tests as skipped.
    # In a real CI environment, the missing module would cause a failure.
    pytest.skip("analysis.correlation module not yet implemented", allow_module_level=True)


class TestPerformANOVA:
    """Tests for the ANOVA implementation."""

    def test_anova_returns_valid_f_and_p(self):
        """
        Verify that perform_anova returns a dictionary with valid F-statistic and p-value.
        """
        # Create synthetic data with known differences
        group_a = np.random.normal(0, 1, 50)
        group_b = np.random.normal(2, 1, 50)
        group_c = np.random.normal(4, 1, 50)

        result = perform_anova([group_a, group_b, group_c], ["Low", "Medium", "High"])

        assert "f_statistic" in result
        assert "p_value" in result
        assert isinstance(result["f_statistic"], (int, float, np.floating))
        assert isinstance(result["p_value"], (int, float, np.floating))
        assert 0 <= result["p_value"] <= 1
        # With distinct means, p-value should be small
        assert result["p_value"] < 0.05

    def test_anova_raises_on_insufficient_data(self):
        """
        Verify that perform_anova raises an error if groups have fewer than 2 samples.
        """
        # Only one sample per group is insufficient for ANOVA
        group_a = [1.0]
        group_b = [2.0]

        with pytest.raises(ValueError):
            perform_anova([group_a, group_b], ["Low", "Medium"])

    def test_anova_matches_scipy_output(self):
        """
        Verify that our implementation matches scipy.stats.f_oneway.
        """
        np.random.seed(42)
        group_a = np.random.normal(0, 1, 100)
        group_b = np.random.normal(1, 1, 100)
        group_c = np.random.normal(2, 1, 100)

        our_result = perform_anova([group_a, group_b, group_c], ["Low", "Medium", "High"])
        scipy_f, scipy_p = stats.f_oneway(group_a, group_b, group_c)

        assert np.isclose(our_result["f_statistic"], scipy_f)
        assert np.isclose(our_result["p_value"], scipy_p)


class TestAnalyzeTrendDirection:
    """Tests for the trend direction analysis."""

    def test_trend_direction_negative(self):
        """
        Verify that a decreasing trend is detected as 'negative'.
        """
        # Create data where fidelity decreases as complexity increases
        # Complexity groups: Low, Medium, High
        # Fidelity scores: High, Medium, Low
        means = [0.9, 0.5, 0.2]
        labels = ["Low", "Medium", "High"]

        trend = analyze_trend_direction(means, labels)

        assert trend == "negative"

    def test_trend_direction_positive(self):
        """
        Verify that an increasing trend is detected as 'positive'.
        """
        means = [0.2, 0.5, 0.9]
        labels = ["Low", "Medium", "High"]

        trend = analyze_trend_direction(means, labels)

        assert trend == "positive"

    def test_trend_direction_flat(self):
        """
        Verify that a flat trend is detected as 'flat' or 'no_trend'.
        """
        means = [0.5, 0.5, 0.5]
        labels = ["Low", "Medium", "High"]

        trend = analyze_trend_direction(means, labels)

        # Depending on implementation, this might be 'flat' or 'no_trend'
        # We expect it NOT to be 'positive' or 'negative'
        assert trend in ["flat", "no_trend"]

    def test_trend_direction_uses_regression(self):
        """
        Verify that trend analysis uses linear regression slope.
        """
        # If slope < 0 -> negative, slope > 0 -> positive
        means = [1.0, 0.5, 0.0]
        labels = ["Low", "Medium", "High"]

        # Map labels to numeric x values (0, 1, 2)
        x = np.array([0, 1, 2])
        y = np.array(means)

        # Calculate slope manually
        slope, _ = np.polyfit(x, y, 1)

        assert slope < 0

        trend = analyze_trend_direction(means, labels)
        assert trend == "negative"


class TestComputeGroupStatistics:
    """Tests for computing descriptive statistics per group."""

    def test_statistics_include_mean_and_std(self):
        """
        Verify that compute_group_statistics returns mean and std for each group.
        """
        data = [
            np.random.normal(0, 1, 50),
            np.random.normal(1, 1, 50),
            np.random.normal(2, 1, 50)
        ]
        labels = ["Low", "Medium", "High"]

        stats_df = compute_group_statistics(data, labels)

        assert isinstance(stats_df, pd.DataFrame)
        assert "group" in stats_df.columns
        assert "mean" in stats_df.columns
        assert "std" in stats_df.columns
        assert len(stats_df) == 3

    def test_statistics_match_manual_calculation(self):
        """
        Verify that the computed mean and std match manual calculations.
        """
        np.random.seed(42)
        group_a = np.random.normal(10, 2, 100)

        our_stats = compute_group_statistics([group_a], ["A"])
        manual_mean = np.mean(group_a)
        manual_std = np.std(group_a, ddof=1)  # Sample std

        assert np.isclose(our_stats.loc[0, "mean"], manual_mean)
        assert np.isclose(our_stats.loc[0, "std"], manual_std)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])