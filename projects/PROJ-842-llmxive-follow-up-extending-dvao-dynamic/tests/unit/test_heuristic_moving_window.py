"""
Unit tests for the Moving Window Heuristic implementation.
"""
import pytest
import numpy as np
import sys
import os
from src.heuristic.moving_window import (
    MovingWindowVarianceHeuristic,
    calculate_windowed_variance,
    compare_heuristic_to_fullbatch
)

class TestMovingWindowVarianceHeuristic:
    def test_initialization(self):
        heuristic = MovingWindowVarianceHeuristic(k=5)
        assert heuristic.k == 5
        assert heuristic.count == 0
        assert heuristic.sum_val == 0.0
        assert heuristic.sum_sq == 0.0

    def test_update_with_insufficient_data(self):
        heuristic = MovingWindowVarianceHeuristic(k=5)
        var = heuristic.update(1.0)
        assert np.isnan(var)
        
        var = heuristic.update(2.0)
        assert np.isnan(var)

    def test_update_with_sufficient_data(self):
        heuristic = MovingWindowVarianceHeuristic(k=5)
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        for val in values:
            heuristic.update(val)
        
        # Variance of [1, 2, 3, 4, 5] is 2.5 (unbiased)
        expected_var = 2.5
        assert abs(heuristic.get_variance() - expected_var) < 1e-6

    def test_window_sliding(self):
        heuristic = MovingWindowVarianceHeuristic(k=3)
        # Add 1, 2, 3 -> variance of [1, 2, 3]
        heuristic.update(1.0)
        heuristic.update(2.0)
        heuristic.update(3.0)
        var1 = heuristic.get_variance()
        
        # Add 4 -> window becomes [2, 3, 4]
        heuristic.update(4.0)
        var2 = heuristic.get_variance()
        
        # Variance of [1, 2, 3] is 1.0
        assert abs(var1 - 1.0) < 1e-6
        # Variance of [2, 3, 4] is 1.0
        assert abs(var2 - 1.0) < 1e-6

    def test_reset(self):
        heuristic = MovingWindowVarianceHeuristic(k=5)
        heuristic.update(1.0)
        heuristic.update(2.0)
        heuristic.reset()
        
        assert heuristic.count == 0
        assert heuristic.sum_val == 0.0
        assert heuristic.sum_sq == 0.0
        assert np.isnan(heuristic.get_variance())

class TestCalculateWindowedVariance:
    def test_basic_functionality(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        k = 3
        results = calculate_windowed_variance(values, k)
        
        assert len(results) == len(values)
        # First two should be NaN
        assert np.isnan(results[0])
        assert np.isnan(results[1])
        # Third should be variance of [1, 2, 3] = 1.0
        assert abs(results[2] - 1.0) < 1e-6

    def test_constant_values(self):
        values = [5.0, 5.0, 5.0, 5.0]
        k = 2
        results = calculate_windowed_variance(values, k)
        
        # Variance of constant values is 0
        for i in range(1, len(results)):
            assert results[i] == 0.0

class TestCompareHeuristicToFullbatch:
    def test_identical_variance(self):
        # If k equals the full length, heuristic should match fullbatch
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        k = len(values)
        
        h_var, fb_var, ratio = compare_heuristic_to_fullbatch(values, k)
        
        assert abs(h_var - fb_var) < 1e-6
        assert abs(ratio - 1.0) < 1e-6

    def test_different_k(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 10.0, 20.0]
        k = 3
        
        h_var, fb_var, ratio = compare_heuristic_to_fullbatch(values, k)
        
        # Heuristic only sees last 3: [5, 10, 20] -> variance ~ 41.67
        # Full batch sees all -> variance will be much higher
        assert h_var < fb_var
        assert ratio < 1.0

    def test_single_value_error(self):
        with pytest.raises(ValueError):
            compare_heuristic_to_fullbatch([1.0], k=1)
        
        with pytest.raises(ValueError):
            compare_heuristic_to_fullbatch([], k=1)

class TestEdgeCases:
    def test_zero_variance(self):
        values = [5.0, 5.0, 5.0, 5.0]
        k = 2
        h_var, fb_var, ratio = compare_heuristic_to_fullbatch(values, k)
        
        assert fb_var == 0.0
        assert h_var == 0.0
        assert np.isnan(ratio)

    def test_large_k(self):
        values = list(range(100))
        k = 200  # k > len(values)
        
        h_var, fb_var, ratio = compare_heuristic_to_fullbatch(values, k)
        
        # Should still work, treating k as effectively len(values)
        assert abs(h_var - fb_var) < 1e-6