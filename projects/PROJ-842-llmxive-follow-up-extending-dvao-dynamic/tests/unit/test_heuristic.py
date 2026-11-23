"""
Unit tests for src/simulation/heuristic.py
"""
import pytest
import numpy as np
import sys
import os
from collections import deque

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.simulation.heuristic import (
    MovingWindowVarianceHeuristic,
    calculate_windowed_variance,
    compare_heuristic_to_fullbatch
)


class TestMovingWindowVarianceHeuristic:
    """Tests for the MovingWindowVarianceHeuristic class."""

    def test_init(self):
        """Test initialization."""
        heuristic = MovingWindowVarianceHeuristic(5)
        assert heuristic.window_size == 5
        assert len(heuristic.window) == 0
        assert heuristic.count == 0

    def test_init_invalid_size(self):
        """Test initialization with invalid size."""
        with pytest.raises(ValueError):
            MovingWindowVarianceHeuristic(0)
        with pytest.raises(ValueError):
            MovingWindowVarianceHeuristic(-1)

    def test_update_single_value(self):
        """Test updating with a single value (variance should be NaN)."""
        heuristic = MovingWindowVarianceHeuristic(5)
        var = heuristic.update(10.0)
        assert np.isnan(var)
        assert heuristic.count == 1

    def test_update_two_values(self):
        """Test updating with two values."""
        heuristic = MovingWindowVarianceHeuristic(5)
        heuristic.update(10.0)
        var = heuristic.update(20.0)
        # Variance of [10, 20] with ddof=1: ((10-15)^2 + (20-15)^2) / 1 = 50
        assert np.isclose(var, 50.0)
        assert heuristic.count == 2

    def test_window_overflow(self):
        """Test that old values are removed when window is full."""
        heuristic = MovingWindowVarianceHeuristic(3)
        
        # Fill window: [1, 2, 3]
        heuristic.update(1.0)
        heuristic.update(2.0)
        v1 = heuristic.update(3.0)
        
        # Add new value: [2, 3, 4] (1 is dropped)
        v2 = heuristic.update(4.0)
        
        # Verify window contents
        assert list(heuristic.window) == [2.0, 3.0, 4.0]
        
        # Verify variance calculation for [2, 3, 4]
        # Mean = 3.0
        # Var = ((2-3)^2 + (3-3)^2 + (4-3)^2) / 2 = (1 + 0 + 1) / 2 = 1.0
        assert np.isclose(v2, 1.0)

    def test_reset(self):
        """Test reset functionality."""
        heuristic = MovingWindowVarianceHeuristic(5)
        heuristic.update(1.0)
        heuristic.update(2.0)
        heuristic.reset()
        
        assert len(heuristic.window) == 0
        assert heuristic.count == 0
        assert np.isnan(heuristic.get_variance())


class TestCalculateWindowedVariance:
    """Tests for the calculate_windowed_variance function."""

    def test_basic_calculation(self):
        """Test basic variance calculation."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        k = 3
        # Last 3 values: [3, 4, 5]
        # Mean = 4.0
        # Var = ((3-4)^2 + (4-4)^2 + (5-4)^2) / 2 = 1.0
        result = calculate_windowed_variance(values, k)
        assert np.isclose(result, 1.0)

    def test_k_larger_than_values(self):
        """Test when k is larger than the number of values."""
        values = [1.0, 2.0]
        k = 5
        # Should use all values
        # Mean = 1.5
        # Var = ((1-1.5)^2 + (2-1.5)^2) / 1 = 0.5
        result = calculate_windowed_variance(values, k)
        assert np.isclose(result, 0.5)

    def test_insufficient_values(self):
        """Test when fewer than 2 values are available."""
        values = [1.0]
        k = 3
        result = calculate_windowed_variance(values, k)
        assert np.isnan(result)

    def test_invalid_k(self):
        """Test with invalid k."""
        with pytest.raises(ValueError):
            calculate_windowed_variance([1.0, 2.0], 0)


class TestCompareHeuristicToFullbatch:
    """Tests for the compare_heuristic_to_fullbatch function."""

    def test_return_structure(self):
        """Test that the function returns the expected structure."""
        trajectory = [1.0, 2.0, 3.0, 4.0, 5.0]
        k_values = [2, 3]
        
        results = compare_heuristic_to_fullbatch(trajectory, k_values)
        
        assert 'heuristic_estimates' in results
        assert 'fullbatch_estimates' in results
        assert 'metrics' in results
        
        assert len(results['heuristic_estimates']) == len(k_values)
        for k in k_values:
            assert k in results['heuristic_estimates']
            assert len(results['heuristic_estimates'][k]) == len(trajectory)
        
        assert len(results['fullbatch_estimates']) == len(trajectory)
        assert len(results['metrics']) == len(k_values)

    def test_metrics_calculation(self):
        """Test that metrics are calculated correctly."""
        # Create a trajectory where full-batch variance is constant (easy to verify)
        # Actually, variance changes as we add points.
        # Let's just verify the correlation is high for a deterministic sequence.
        np.random.seed(42)
        trajectory = np.random.randn(100).tolist()
        k_values = [10, 20]
        
        results = compare_heuristic_to_fullbatch(trajectory, k_values)
        
        for k in k_values:
            assert 'mean_abs_error' in results['metrics'][k]
            assert 'correlation' in results['metrics'][k]
            # Correlation should be high (not NaN) for a reasonable sequence
            assert not np.isnan(results['metrics'][k]['correlation'])

    def test_empty_trajectory(self):
        """Test with empty trajectory."""
        trajectory = []
        k_values = [5]
        results = compare_heuristic_to_fullbatch(trajectory, k_values)
        
        assert len(results['heuristic_estimates'][5]) == 0
        assert len(results['fullbatch_estimates']) == 0

    def test_short_trajectory(self):
        """Test with trajectory shorter than k."""
        trajectory = [1.0, 2.0]
        k_values = [5]
        results = compare_heuristic_to_fullbatch(trajectory, k_values)
        
        # Should handle gracefully
        assert len(results['heuristic_estimates'][5]) == 2
        assert len(results['fullbatch_estimates']) == 2