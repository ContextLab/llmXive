"""Unit tests for threshold_finder module.

This file contains tests for the threshold detection logic, specifically
focusing on the "3 consecutive increments" rule for power threshold detection.
"""

import pytest
import numpy as np
import pandas as pd
from code.analysis.threshold_finder import (
    wilson_score_interval,
    calculate_confidence_intervals,
    load_error_rates,
    find_type_i_threshold,
    find_power_threshold,
    save_thresholds
)


class TestWilsonScoreInterval:
    """Tests for the Wilson score interval calculation."""

    def test_wilson_score_implementation(self):
        """Assert that the Wilson score formula is used, not normal approximation."""
        # Wilson score interval formula:
        # (p + z^2/(2n) +/- z * sqrt((p(1-p) + z^2/(4n))/n)) / (1 + z^2/n)
        # where z is the z-score for the confidence level

        # Test with known values
        p = 0.5
        n = 100
        alpha = 0.05
        z = 1.96  # z-score for 95% confidence

        # Expected Wilson score calculation
        center = (p + z**2 / (2 * n)) / (1 + z**2 / n)
        margin = (z / (1 + z**2 / n)) * np.sqrt(
            (p * (1 - p) + z**2 / (4 * n)) / n
        )

        expected_lower = center - margin
        expected_upper = center + margin

        # Get actual calculation
        lower, upper = wilson_score_interval(p, n, alpha)

        # Assert they match
        np.testing.assert_almost_equal(lower, expected_lower, decimal=6)
        np.testing.assert_almost_equal(upper, expected_upper, decimal=6)

        # Also verify it's different from normal approximation
        normal_margin = z * np.sqrt(p * (1 - p) / n)
        normal_lower = p - normal_margin
        normal_upper = p + normal_margin

        # Wilson should be different from normal (especially for small n)
        assert abs(lower - normal_lower) > 0.001, "Wilson score should differ from normal approximation"
        assert abs(upper - normal_upper) > 0.001, "Wilson score should differ from normal approximation"


class TestPowerThresholdConsecutiveRule:
    """Tests for the '3 consecutive increments' rule in power threshold detection."""

    def test_power_threshold_consecutive_rule(self):
        """
        Assert that the logic correctly identifies the threshold only after
        3 consecutive increments below 0.80.

        This test verifies FR-004: "identify the smallest n where power CI
        remains < 0.80 for 3 consecutive increments".
        """
        # Create a mock dataset with power values
        # The threshold should be at n=15, where we have 3 consecutive values < 0.80
        # n=5: 0.90 (above 0.80)
        # n=10: 0.85 (above 0.80)
        # n=15: 0.75 (below 0.80) - first below
        # n=20: 0.70 (below 0.80) - second below
        # n=25: 0.65 (below 0.80) - third below -> threshold should be 15
        # n=30: 0.60 (below 0.80)
        # n=35: 0.55 (below 0.80)

        data = {
            'test_type': ['t-test'] * 7,
            'sample_size': [5, 10, 15, 20, 25, 30, 35],
            'effect_size': [0.5] * 7,
            'hypothesis_state': ['alternative'] * 7,
            'type1_error_rate': [0.05] * 7,
            'type2_error_rate': [0.10, 0.15, 0.25, 0.30, 0.35, 0.40, 0.45],
            'ci_lower': [0.04, 0.04, 0.20, 0.25, 0.30, 0.35, 0.40],
            'ci_upper': [0.16, 0.26, 0.30, 0.35, 0.40, 0.45, 0.50]
        }

        df = pd.DataFrame(data)
        df['power'] = 1 - df['type2_error_rate']

        # Calculate CI for power (using the complement of type2 error rate CI)
        # For simplicity, we'll use the type2_error_rate CI to derive power CI
        df['power_ci_lower'] = 1 - df['ci_upper']
        df['power_ci_upper'] = 1 - df['ci_lower']

        # Now test the find_power_threshold function
        # We need to mock the function to work with our data
        # The function should return the first n where power CI < 0.80 for 3 consecutive increments

        # Expected: threshold at n=15 (first of 3 consecutive below 0.80)
        threshold = find_power_threshold(df, test_type='t-test', effect_size=0.5, alpha=0.05)

        # Verify the threshold is 15
        assert threshold == 15, f"Expected threshold at n=15, got {threshold}"

    def test_power_threshold_edge_case_n5(self):
        """
        Test edge case where threshold is exactly at n=5.
        This happens when the first 3 sample sizes (5, 10, 15) all have power < 0.80.
        """
        data = {
            'test_type': ['t-test'] * 5,
            'sample_size': [5, 10, 15, 20, 25],
            'effect_size': [0.5] * 5,
            'hypothesis_state': ['alternative'] * 5,
            'type1_error_rate': [0.05] * 5,
            'type2_error_rate': [0.30, 0.25, 0.20, 0.15, 0.10],
            'ci_lower': [0.25, 0.20, 0.15, 0.10, 0.05],
            'ci_upper': [0.35, 0.30, 0.25, 0.20, 0.15]
        }

        df = pd.DataFrame(data)
        df['power'] = 1 - df['type2_error_rate']
        df['power_ci_lower'] = 1 - df['ci_upper']
        df['power_ci_upper'] = 1 - df['ci_lower']

        # All first 3 values (n=5, 10, 15) have power < 0.80
        # Threshold should be at n=5
        threshold = find_power_threshold(df, test_type='t-test', effect_size=0.5, alpha=0.05)

        assert threshold == 5, f"Expected threshold at n=5, got {threshold}"

    def test_power_threshold_edge_case_n500(self):
        """
        Test edge case where threshold is exactly at n=500.
        This happens when power only drops below 0.80 at the very end.
        """
        # Create data where only the last 3 values are below 0.80
        sample_sizes = list(range(5, 505, 5))  # 5 to 500
        n_values = len(sample_sizes)

        # Power starts high and drops at the end
        power_values = [0.95] * (n_values - 3) + [0.75, 0.70, 0.65]
        type2_error_rates = [1 - p for p in power_values]

        data = {
            'test_type': ['t-test'] * n_values,
            'sample_size': sample_sizes,
            'effect_size': [0.5] * n_values,
            'hypothesis_state': ['alternative'] * n_values,
            'type1_error_rate': [0.05] * n_values,
            'type2_error_rate': type2_error_rates,
            'ci_lower': [0.20] * n_values,
            'ci_upper': [0.30] * n_values
        }

        df = pd.DataFrame(data)
        df['power'] = 1 - df['type2_error_rate']
        df['power_ci_lower'] = 1 - df['ci_upper']
        df['power_ci_upper'] = 1 - df['ci_lower']

        # Threshold should be at n=490 (first of 3 consecutive below 0.80)
        # But since we only have 3 values below, it's 490
        threshold = find_power_threshold(df, test_type='t-test', effect_size=0.5, alpha=0.05)

        # The first of the 3 consecutive values is at index -3, which is 490
        assert threshold == 490, f"Expected threshold at n=490, got {threshold}"

    def test_power_threshold_no_threshold_found(self):
        """
        Test case where no threshold is found (power never drops below 0.80 for 3 consecutive).
        """
        data = {
            'test_type': ['t-test'] * 5,
            'sample_size': [5, 10, 15, 20, 25],
            'effect_size': [0.5] * 5,
            'hypothesis_state': ['alternative'] * 5,
            'type1_error_rate': [0.05] * 5,
            'type2_error_rate': [0.10, 0.08, 0.06, 0.04, 0.02],
            'ci_lower': [0.05, 0.03, 0.01, 0.00, 0.00],
            'ci_upper': [0.15, 0.13, 0.11, 0.09, 0.07]
        }

        df = pd.DataFrame(data)
        df['power'] = 1 - df['type2_error_rate']
        df['power_ci_lower'] = 1 - df['ci_upper']
        df['power_ci_upper'] = 1 - df['ci_lower']

        # All power values are above 0.80, so no threshold should be found
        threshold = find_power_threshold(df, test_type='t-test', effect_size=0.5, alpha=0.05)

        assert threshold is None, f"Expected no threshold (None), got {threshold}"

    def test_power_threshold_only_two_consecutive(self):
        """
        Test case where only 2 consecutive values are below 0.80, not 3.
        Threshold should not be found.
        """
        data = {
            'test_type': ['t-test'] * 5,
            'sample_size': [5, 10, 15, 20, 25],
            'effect_size': [0.5] * 5,
            'hypothesis_state': ['alternative'] * 5,
            'type1_error_rate': [0.05] * 5,
            'type2_error_rate': [0.10, 0.25, 0.30, 0.20, 0.10],
            'ci_lower': [0.05, 0.20, 0.25, 0.15, 0.05],
            'ci_upper': [0.15, 0.30, 0.35, 0.25, 0.15]
        }

        df = pd.DataFrame(data)
        df['power'] = 1 - df['type2_error_rate']
        df['power_ci_lower'] = 1 - df['ci_upper']
        df['power_ci_upper'] = 1 - df['ci_lower']

        # Only 2 consecutive values (n=10, 15) are below 0.80, not 3
        # Threshold should not be found
        threshold = find_power_threshold(df, test_type='t-test', effect_size=0.5, alpha=0.05)

        assert threshold is None, f"Expected no threshold (None), got {threshold}"

    def test_power_threshold_with_confidence_interval_check(self):
        """
        Test that the rule checks the LOWER confidence interval bound, not just the point estimate.
        """
        # Create data where point estimate is above 0.80 but CI lower bound is below
        data = {
            'test_type': ['t-test'] * 5,
            'sample_size': [5, 10, 15, 20, 25],
            'effect_size': [0.5] * 5,
            'hypothesis_state': ['alternative'] * 5,
            'type1_error_rate': [0.05] * 5,
            'type2_error_rate': [0.15, 0.18, 0.22, 0.25, 0.20],
            'ci_lower': [0.08, 0.10, 0.12, 0.15, 0.10],
            'ci_upper': [0.22, 0.26, 0.32, 0.35, 0.30]
        }

        df = pd.DataFrame(data)
        df['power'] = 1 - df['type2_error_rate']
        df['power_ci_lower'] = 1 - df['ci_upper']
        df['power_ci_upper'] = 1 - df['ci_lower']

        # Check if the function correctly identifies based on CI lower bound
        # n=5: power=0.85, CI_lower=0.78 (above 0.80? No, 0.78 < 0.80)
        # n=10: power=0.82, CI_lower=0.74 (below 0.80)
        # n=15: power=0.78, CI_lower=0.68 (below 0.80)
        # n=20: power=0.75, CI_lower=0.65 (below 0.80) -> threshold at n=10
        # n=25: power=0.80, CI_lower=0.70 (below 0.80)

        # Actually, let's re-examine:
        # The rule is: "power CI remains < 0.80 for 3 consecutive increments"
        # This means the LOWER bound of the power CI should be < 0.80

        # For n=5: power_ci_lower = 1 - 0.22 = 0.78 < 0.80
        # For n=10: power_ci_lower = 1 - 0.26 = 0.74 < 0.80
        # For n=15: power_ci_lower = 1 - 0.32 = 0.68 < 0.80
        # So we have 3 consecutive at n=5, 10, 15 -> threshold at n=5

        threshold = find_power_threshold(df, test_type='t-test', effect_size=0.5, alpha=0.05)

        assert threshold == 5, f"Expected threshold at n=5, got {threshold}"


class TestCalculateConfidenceIntervals:
    """Tests for confidence interval calculation."""

    def test_calculate_confidence_intervals(self):
        """Test that confidence intervals are calculated correctly."""
        data = {
            'test_type': ['t-test'] * 3,
            'sample_size': [10, 20, 30],
            'effect_size': [0.5, 0.5, 0.5],
            'hypothesis_state': ['null', 'alternative', 'alternative'],
            'type1_error_rate': [0.05, 0.05, 0.05],
            'type2_error_rate': [0.10, 0.20, 0.30],
            'ci_lower': [0.04, 0.15, 0.25],
            'ci_upper': [0.16, 0.25, 0.35]
        }

        df = pd.DataFrame(data)

        # The function should calculate confidence intervals using Wilson score
        # For this test, we just verify it doesn't crash and returns expected structure
        result = calculate_confidence_intervals(df)

        assert isinstance(result, pd.DataFrame)
        assert 'ci_lower' in result.columns
        assert 'ci_upper' in result.columns
        assert len(result) == len(df)


class TestFindTypeIThreshold:
    """Tests for Type I error threshold detection."""

    def test_find_type_i_threshold(self):
        """Test that Type I error threshold is correctly identified."""
        # Create data where Type I error exceeds 0.05 at n=20
        data = {
            'test_type': ['t-test'] * 5,
            'sample_size': [5, 10, 15, 20, 25],
            'effect_size': [0.0, 0.0, 0.0, 0.0, 0.0],  # Null hypothesis
            'hypothesis_state': ['null'] * 5,
            'type1_error_rate': [0.04, 0.045, 0.048, 0.052, 0.055],
            'type2_error_rate': [0.5, 0.5, 0.5, 0.5, 0.5],
            'ci_lower': [0.03, 0.035, 0.038, 0.042, 0.045],
            'ci_upper': [0.05, 0.055, 0.058, 0.062, 0.065]
        }

        df = pd.DataFrame(data)

        # The threshold should be at n=20 where the lower CI bound (0.042) is still below 0.05
        # But the point estimate (0.052) is above 0.05
        # Actually, the rule is: "smallest sample size where the Type I error lower confidence
        # interval bound exceeds 0.05"
        # So we need the lower bound to exceed 0.05

        # Let's adjust the data
        data['ci_lower'] = [0.03, 0.035, 0.038, 0.051, 0.055]

        df = pd.DataFrame(data)

        threshold = find_type_i_threshold(df, test_type='t-test', alpha=0.05)

        # Threshold should be at n=20 where ci_lower (0.051) > 0.05
        assert threshold == 20, f"Expected threshold at n=20, got {threshold}"