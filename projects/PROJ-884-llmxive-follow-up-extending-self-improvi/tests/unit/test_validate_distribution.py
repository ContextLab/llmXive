"""
Unit tests for code/dataset/validate_distribution.py
"""
import json
import math
import os
import tempfile
from pathlib import Path
import pytest

# We need to add the project root to sys.path to import the module
# Assuming this test runs from the project root or similar context
import sys
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.dataset.validate_distribution import (
    calculate_chi_square,
    validate_complexity_scaling,
    calculate_power_estimate
)


class TestChiSquare:
    def test_perfect_fit(self):
        # If observed matches expected exactly, chi-square should be 0
        observed = {"sudoku": 50, "pathfinding": 50}
        expected = {"sudoku": 0.5, "pathfinding": 0.5}
        stat, p_val = calculate_chi_square(observed, expected)
        assert math.isclose(stat, 0.0, abs_tol=1e-5)
        # p-value should be 1.0 for perfect fit (or very close)
        assert p_val >= 0.99

    def test_moderate_deviation(self):
        observed = {"sudoku": 60, "pathfinding": 40}
        expected = {"sudoku": 0.5, "pathfinding": 0.5}
        stat, p_val = calculate_chi_square(observed, expected)
        # Stat should be > 0
        assert stat > 0.0
        # P-value should be < 1.0
        assert p_val < 1.0

    def test_empty_observed(self):
        observed = {}
        expected = {"sudoku": 0.5}
        stat, p_val = calculate_chi_square(observed, expected)
        assert stat == 0.0
        assert p_val == 1.0

    def test_zero_expected_with_observed(self):
        # If expected is 0 but we have observed, it should be a huge deviation
        observed = {"sudoku": 10}
        expected = {"sudoku": 0.0}
        stat, p_val = calculate_chi_square(observed, expected)
        # Should be inf or very large
        assert stat == float('inf') or stat > 10000


class TestComplexityScaling:
    def test_valid_continuous_scaling(self):
        data = [
            {"n": 10, "count": 10},
            {"n": 20, "count": 10},
            {"n": 30, "count": 10}
        ]
        schema_constraints = {"min": 10, "max": 30, "step": 10}
        is_valid, msg = validate_complexity_scaling(data, schema_constraints)
        assert is_valid is True

    def test_gap_in_scaling(self):
        data = [
            {"n": 10, "count": 10},
            {"n": 50, "count": 10} # Gap from 10 to 50
        ]
        schema_constraints = {"min": 10, "max": 50, "step": 10}
        is_valid, msg = validate_complexity_scaling(data, schema_constraints)
        assert is_valid is False
        assert "Gap detected" in msg

    def test_below_min(self):
        data = [
            {"n": 5, "count": 10}
        ]
        schema_constraints = {"min": 10, "max": 50, "step": 10}
        is_valid, msg = validate_complexity_scaling(data, schema_constraints)
        assert is_valid is False
        assert "below schema minimum" in msg


class TestPowerEstimate:
    def test_large_sample_high_power(self):
        # Large N should yield high power
        power = calculate_power_estimate(total_count=1000, effect_size=0.5)
        assert power > 0.8

    def test_small_sample_low_power(self):
        # Small N should yield low power
        power = calculate_power_estimate(total_count=10, effect_size=0.5)
        assert power < 0.8

    def test_zero_sample(self):
        power = calculate_power_estimate(total_count=0)
        assert power == 0.0