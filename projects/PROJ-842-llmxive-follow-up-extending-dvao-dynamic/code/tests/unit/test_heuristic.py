"""
Unit tests for the Moving-Window Heuristic variance estimation.

These tests verify that the heuristic correctly calculates variance using only
the last k steps, as required by T032.
"""
import pytest
import numpy as np
import sys
import os
from collections import deque

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.simulation.heuristic import (
    MovingWindowVarianceHeuristic,
    calculate_windowed_variance,
    compare_heuristic_to_fullbatch
)


class TestMovingWindowVarianceHeuristic:
    """Tests for the MovingWindowVarianceHeuristic class."""

    def test_initialization(self):
        """Test that the heuristic initializes correctly."""
        heuristic = MovingWindowVarianceHeuristic(window_size=10)
        assert heuristic.window_size == 10
        assert len(heuristic.window) == 0
        assert len(heuristic.squared_window) == 0

    def test_invalid_window_size(self):
        """Test that initialization fails for invalid window sizes."""
        with pytest.raises(ValueError):
            MovingWindowVarianceHeuristic(window_size=0)
        with pytest.raises(ValueError):
            MovingWindowVarianceHeuristic(window_size=-5)

    def test_update_with_insufficient_data(self):
        """Test that update returns 0.0 when window is not full."""
        heuristic = MovingWindowVarianceHeuristic(window_size=10)
        
        # Add 9 values (less than window size)
        for i in range(9):
            var = heuristic.update(float(i))
            assert var == 0.0, "Variance should be 0.0 when window is not full"
        
        assert len(heuristic.window) == 9

    def test_update_with_exact_window(self):
        """Test variance calculation when window is exactly full."""
        heuristic = MovingWindowVarianceHeuristic(window_size=5)
        
        # Add 5 identical values
        for _ in range(5):
            heuristic.update(10.0)
        
        # Variance of identical values should be 0
        assert heuristic.get_current_variance() == 0.0

    def test_update_with_varying_values(self):
        """Test variance calculation with varying values."""
        heuristic = MovingWindowVarianceHeuristic(window_size=5)
        
        # Add values: 1, 2, 3, 4, 5
        expected_values = [1, 2, 3, 4, 5]
        for val in expected_values:
            heuristic.update(float(val))
        
        # Calculate expected variance manually
        # Mean = 3, Variance = ((1-3)^2 + (2-3)^2 + (3-3)^2 + (4-3)^2 + (5-3)^2) / 5
        # = (4 + 1 + 0 + 1 + 4) / 5 = 10 / 5 = 2.0
        expected_variance = 2.0
        actual_variance = heuristic.get_current_variance()
        
        assert np.isclose(actual_variance, expected_variance), \
            f"Expected {expected_variance}, got {actual_variance}"

    def test_sliding_window_behavior(self):
        """Test that the window slides correctly, dropping old values."""
        heuristic = MovingWindowVarianceHeuristic(window_size=3)
        
        # Add 1, 2, 3 -> Window: [1, 2, 3]
        heuristic.update(1.0)
        heuristic.update(2.0)
        heuristic.update(3.0)
        var1 = heuristic.get_current_variance()
        
        # Add 4 -> Window: [2, 3, 4]
        heuristic.update(4.0)
        var2 = heuristic.get_current_variance()
        
        # Variance of [1, 2, 3] = 2/3 ≈ 0.6667
        # Variance of [2, 3, 4] = 2/3 ≈ 0.6667
        # But let's use a more distinct example
        
        # Reset and try again with more distinct values
        heuristic = MovingWindowVarianceHeuristic(window_size=3)
        heuristic.update(10.0)  # [10]
        heuristic.update(10.0)  # [10, 10]
        heuristic.update(10.0)  # [10, 10, 10] -> Var = 0
        assert heuristic.get_current_variance() == 0.0
        
        heuristic.update(20.0)  # [10, 10, 20] -> Var = 6.666...
        expected_new_var = ( (10-13.333)**2 + (10-13.333)**2 + (20-13.333)**2 ) / 3
        # Mean = 40/3 ≈ 13.333
        # Var = (11.111 + 11.111 + 44.444) / 3 = 66.666 / 3 ≈ 22.222
        # Actually:
        # Values: 10, 10, 20. Mean = 40/3.
        # Sq diffs: (10 - 40/3)^2 = (-10/3)^2 = 100/9
        # (10 - 40/3)^2 = 100/9
        # (20 - 40/3)^2 = (20/3)^2 = 400/9
        # Sum = 600/9 = 200/3. Var = (200/3)/3 = 200/9 ≈ 22.222
        expected_new_var = 200/9
        actual_new_var = heuristic.get_current_variance()
        
        assert np.isclose(actual_new_var, expected_new_var), \
            f"Expected {expected_new_var}, got {actual_new_var}"

    def test_reset(self):
        """Test that reset clears the window."""
        heuristic = MovingWindowVarianceHeuristic(window_size=5)
        for i in range(5):
            heuristic.update(float(i))
        
        assert len(heuristic.window) == 5
        
        heuristic.reset()
        
        assert len(heuristic.window) == 0
        assert len(heuristic.squared_window) == 0
        assert heuristic.get_current_variance() == 0.0


class TestCalculateWindowedVariance:
    """Tests for the calculate_windowed_variance function."""

    def test_basic_calculation(self):
        """Test basic variance calculation."""
        values = [1, 2, 3, 4, 5]
        k = 5
        result = calculate_windowed_variance(values, k)
        expected = 2.0  # Population variance
        assert np.isclose(result, expected)

    def test_partial_window(self):
        """Test calculation when k < len(values)."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        k = 5
        result = calculate_windowed_variance(values, k)
        # Last 5 values: [6, 7, 8, 9, 10]
        # Mean = 8, Var = 2.0
        expected = 2.0
        assert np.isclose(result, expected)

    def test_k_greater_than_length(self):
        """Test when k > len(values) - should use all values."""
        values = [1, 2, 3]
        k = 10
        result = calculate_windowed_variance(values, k)
        # All values: [1, 2, 3]
        # Mean = 2, Var = 2/3 ≈ 0.6667
        expected = 2/3
        assert np.isclose(result, expected)

    def test_k_equals_one(self):
        """Test when k = 1 - variance should be 0."""
        values = [5, 10, 15]
        k = 1
        result = calculate_windowed_variance(values, k)
        assert result == 0.0

    def test_empty_list(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError):
            calculate_windowed_variance([], 5)

    def test_invalid_k(self):
        """Test that k < 1 raises ValueError."""
        with pytest.raises(ValueError):
            calculate_windowed_variance([1, 2, 3], 0)
        with pytest.raises(ValueError):
            calculate_windowed_variance([1, 2, 3], -1)


class TestCompareHeuristicToFullbatch:
    """Tests for the compare_heuristic_to_fullbatch function."""

    def test_identical_values(self):
        """Test when all values are identical."""
        values = [5.0] * 10
        k = 5
        result = compare_heuristic_to_fullbatch(values, k)
        
        assert result['heuristic_variance'] == 0.0
        assert result['fullbatch_variance'] == 0.0
        assert result['relative_error'] == 0.0
        assert result['is_acceptable'] == True

    def test_varying_values(self):
        """Test with varying values."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        k = 5
        result = compare_heuristic_to_fullbatch(values, k)
        
        # Full batch variance of 1..10
        fullbatch_var = np.var(values, ddof=0)
        # Heuristic variance of last 5 (6..10)
        heuristic_var = np.var(values[-5:], ddof=0)
        
        assert np.isclose(result['fullbatch_variance'], fullbatch_var)
        assert np.isclose(result['heuristic_variance'], heuristic_var)
        
        # Check relative error calculation
        if fullbatch_var != 0:
            expected_error = abs(heuristic_var - fullbatch_var) / fullbatch_var
            assert np.isclose(result['relative_error'], expected_error)

    def test_empty_list(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError):
            compare_heuristic_to_fullbatch([], 5)

    def test_threshold_behavior(self):
        """Test is_acceptable flag with different thresholds."""
        values = list(range(1, 21))
        k = 5
        
        # Default threshold is 0.1
        result_default = compare_heuristic_to_fullbatch(values, k, threshold=0.1)
        
        # With a very high threshold, should be acceptable
        result_high = compare_heuristic_to_fullbatch(values, k, threshold=10.0)
        assert result_high['is_acceptable'] == True

    def test_single_value(self):
        """Test with a single value."""
        values = [5.0]
        k = 1
        result = compare_heuristic_to_fullbatch(values, k)
        
        assert result['heuristic_variance'] == 0.0
        assert result['fullbatch_variance'] == 0.0
        assert result['relative_error'] == 0.0


class TestWindowedVarianceCorrectness:
    """Additional tests to ensure mathematical correctness."""

    def test_variance_formula(self):
        """Test that the variance calculation matches the formula."""
        # E[X^2] - (E[X])^2
        values = [2, 4, 6, 8, 10]
        k = 5
        
        result = calculate_windowed_variance(values, k)
        
        # Manual calculation
        mean = np.mean(values)
        expected = np.mean(np.array(values)**2) - mean**2
        
        assert np.isclose(result, expected)

    def test_large_numbers(self):
        """Test with large numbers to check for numerical stability."""
        values = [1e6, 1e6 + 1, 1e6 + 2, 1e6 + 3, 1e6 + 4]
        k = 5
        
        result = calculate_windowed_variance(values, k)
        # Variance should be the same as [0, 1, 2, 3, 4] due to shift invariance
        expected = np.var([0, 1, 2, 3, 4], ddof=0)
        
        assert np.isclose(result, expected)

    def test_negative_numbers(self):
        """Test with negative numbers."""
        values = [-5, -3, -1, 1, 3]
        k = 5
        
        result = calculate_windowed_variance(values, k)
        expected = np.var(values, ddof=0)
        
        assert np.isclose(result, expected)

    def test_float_values(self):
        """Test with float values."""
        values = [1.5, 2.7, 3.2, 4.8, 5.1]
        k = 5
        
        result = calculate_windowed_variance(values, k)
        expected = np.var(values, ddof=0)
        
        assert np.isclose(result, expected)