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
        """Test Welch's t-test logic."""
        group1 = [10, 12, 14, 16, 18]
        group2 = [5, 7, 9, 11, 13]
        t_stat, p_val = run_t_test(group1, group2, equal_var=False)

        assert isinstance(t_stat, float)
        assert isinstance(p_val, float)
        assert p_val < 0.05  # Should be significant

    def test_students_t_test(self):
        """Test Student's t-test logic."""
        group1 = [10, 12, 14, 16, 18]
        group2 = [11, 13, 15, 17, 19]
        t_stat, p_val = run_t_test(group1, group2, equal_var=True)

        assert isinstance(t_stat, float)
        assert isinstance(p_val, float)

    def test_cohens_d(self):
        """Test Cohen's d calculation."""
        group1 = [10, 12, 14, 16, 18]
        group2 = [5, 7, 9, 11, 13]
        d = calculate_effect_size(group1, group2)

        assert isinstance(d, float)
        assert d > 0  # Group 1 has higher mean

    def test_confidence_interval(self):
        """Test confidence interval calculation."""
        group1 = [10, 12, 14, 16, 18]
        group2 = [5, 7, 9, 11, 13]
        ci = calculate_confidence_interval(group1, group2)

        assert isinstance(ci, tuple)
        assert len(ci) == 2
        assert ci[0] < ci[1]

    def test_bonferroni_correction(self):
        """Test Bonferroni correction logic."""
        alpha = 0.05
        n = 5
        adjusted = apply_bonferroni_correction(alpha, n)

        assert adjusted == alpha / n
        assert adjusted < alpha

    def test_collinearity_detection(self):
        """Test collinearity detection."""
        # Perfect collinearity
        predictors = {
            "x1": [1, 2, 3, 4, 5],
            "x2": [2, 4, 6, 8, 10]  # x2 = 2 * x1
        }
        result = check_collinearity(predictors, threshold=0.8)

        assert result["flagged"] is True
        assert len(result["flagged_pairs"]) == 1

    def test_power_calculation(self):
        """Test power calculation."""
        power_res = calculate_power(effect_size=0.8, n1=50, n2=50)

        assert "power" in power_res
        assert "status" in power_res
        assert 0 <= power_res["power"] <= 1
