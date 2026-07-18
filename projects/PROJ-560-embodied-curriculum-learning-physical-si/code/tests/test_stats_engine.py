"""
Unit tests for statistical engine functions.

This module tests t-tests, effect sizes, and corrections.
"""
import pytest
import numpy as np
import json
import os
import tempfile
from typing import List, Tuple
from src.stats_engine import (
    run_t_test,
    calculate_effect_size,
    calculate_confidence_interval,
    apply_bonferroni_correction,
    check_collinearity,
    calculate_power
)


class TestStatsEngine:
    """Tests for statistical engine functions."""

    def test_welchs_t_test(self):
        """Test Welch's t-test logic.
        
        Verifies that Welch's t-test (unequal variance) correctly identifies
        a significant difference between two groups with different variances.
        """
        # Group 1: Higher mean, lower variance
        group1 = [10, 12, 14, 16, 18]
        # Group 2: Lower mean, higher variance (spread out)
        group2 = [2, 5, 9, 13, 21]
        
        # Run Welch's t-test (equal_var=False)
        t_stat, p_val = run_t_test(group1, group2, equal_var=False)

        assert isinstance(t_stat, float), "t-statistic should be a float"
        assert isinstance(p_val, float), "p-value should be a float"
        # With these values, we expect a significant difference
        assert p_val < 0.05, f"Expected p < 0.05 for distinct groups, got {p_val}"
        
        # Welch's should handle the variance difference without error
        assert not np.isnan(t_stat), "t-statistic should not be NaN"
        assert not np.isnan(p_val), "p-value should not be NaN"

    def test_students_t_test(self):
        """Test Student's t-test logic.
        
        Verifies that Student's t-test (equal variance) works correctly
        when variances are assumed equal.
        """
        group1 = [10, 12, 14, 16, 18]
        group2 = [11, 13, 15, 17, 19]
        
        # Run Student's t-test (equal_var=True)
        t_stat, p_val = run_t_test(group1, group2, equal_var=True)

        assert isinstance(t_stat, float), "t-statistic should be a float"
        assert isinstance(p_val, float), "p-value should be a float"
        # These groups are very similar, so p-value should be high
        assert p_val > 0.05, f"Expected p > 0.05 for similar groups, got {p_val}"

    def test_cohens_d(self):
        """Test Cohen's d calculation.
        
        Verifies that effect size is calculated correctly and reflects
        the magnitude of difference between groups.
        """
        group1 = [10, 12, 14, 16, 18]
        group2 = [5, 7, 9, 11, 13]
        
        d = calculate_effect_size(group1, group2)

        assert isinstance(d, float), "Cohen's d should be a float"
        assert d > 0, "Cohen's d should be positive when group1 > group2"
        
        # Calculate expected value manually for verification
        mean_diff = np.mean(group1) - np.mean(group2)
        pooled_std = np.sqrt((np.std(group1, ddof=1)**2 + np.std(group2, ddof=1)**2) / 2)
        expected_d = mean_diff / pooled_std
        
        assert np.isclose(d, expected_d), f"Cohen's d {d} != expected {expected_d}"

    def test_confidence_interval(self):
        """Test confidence interval calculation.
        
        Verifies that confidence intervals are calculated correctly
        and form a valid range.
        """
        group1 = [10, 12, 14, 16, 18]
        group2 = [5, 7, 9, 11, 13]
        
        ci = calculate_confidence_interval(group1, group2)

        assert isinstance(ci, tuple), "CI should be a tuple"
        assert len(ci) == 2, "CI should have exactly 2 elements"
        assert ci[0] < ci[1], "Lower bound should be less than upper bound"
        
        # The interval should contain the mean difference
        mean_diff = np.mean(group1) - np.mean(group2)
        assert ci[0] <= mean_diff <= ci[1], f"Mean diff {mean_diff} not in CI {ci}"

    def test_bonferroni_correction(self):
        """Test Bonferroni correction logic.
        
        Verifies that the correction properly adjusts alpha based on
        the number of comparisons.
        """
        alpha = 0.05
        n = 5
        adjusted = apply_bonferroni_correction(alpha, n)

        expected = alpha / n
        assert adjusted == expected, f"Expected {expected}, got {adjusted}"
        assert adjusted < alpha, "Adjusted alpha should be smaller than original"
        
        # Test edge case: single comparison
        single_adjusted = apply_bonferroni_correction(0.05, 1)
        assert single_adjusted == 0.05, "Single comparison should not adjust alpha"

    def test_collinearity_detection(self):
        """Test collinearity detection.
        
        Verifies that the function correctly identifies highly correlated
        predictors.
        """
        # Perfect collinearity: x2 = 2 * x1
        predictors = {
            "x1": [1, 2, 3, 4, 5],
            "x2": [2, 4, 6, 8, 10]
        }
        
        result = check_collinearity(predictors, threshold=0.8)

        assert result["flagged"] is True, "Should flag perfect collinearity"
        assert len(result["flagged_pairs"]) == 1, "Should have one flagged pair"
        assert ("x1", "x2") in result["flagged_pairs"] or ("x2", "x1") in result["flagged_pairs"]
        
        # Test with no collinearity
        independent = {
            "x1": [1, 2, 3, 4, 5],
            "x2": [5, 1, 3, 2, 4]  # Random order
        }
        result_indep = check_collinearity(independent, threshold=0.8)
        assert result_indep["flagged"] is False, "Should not flag independent variables"

    def test_power_calculation(self):
        """Test power calculation.
        
        Verifies that power is calculated correctly and returns
        appropriate status flags.
        """
        # Well-powered study
        power_res = calculate_power(effect_size=0.8, n1=50, n2=50)

        assert "power" in power_res, "Result should contain 'power' key"
        assert "status" in power_res, "Result should contain 'status' key"
        assert 0 <= power_res["power"] <= 1, "Power should be between 0 and 1"
        
        # Check status for well-powered study
        assert power_res["status"] == "adequate", f"Expected 'adequate', got {power_res['status']}"
        
        # Underpowered study
        underpowered_res = calculate_power(effect_size=0.2, n1=10, n2=10)
        assert underpowered_res["status"] == "underpowered", "Small effect + small N should be underpowered"

    def test_welchs_vs_students_sensitivity(self):
        """Test that Welch's and Student's t-tests give different results
        when variances are unequal.
        
        This validates that the equal_var parameter is actually being used.
        """
        # Create groups with very different variances
        group1 = [10, 12, 14, 16, 18]  # Low variance
        group2 = [2, 8, 14, 20, 26]    # High variance (same mean, but spread out)
        
        t_welch, p_welch = run_t_test(group1, group2, equal_var=False)
        t_student, p_student = run_t_test(group1, group2, equal_var=True)
        
        # With unequal variances, the results should differ
        # (though both might be non-significant for this small sample)
        assert t_welch != t_student or p_welch != p_student, \
            "Welch's and Student's should differ when variances are unequal"