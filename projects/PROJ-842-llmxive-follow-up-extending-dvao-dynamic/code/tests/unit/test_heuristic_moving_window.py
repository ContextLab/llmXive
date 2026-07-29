"""
Unit tests for the Moving-Window Heuristic (T016).
"""
import pytest
import numpy as np
import sys
import os

# Add project root to path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_dir, "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.heuristic.moving_window import (
    MovingWindowVarianceHeuristic,
    calculate_windowed_variance,
    compare_heuristic_to_fullbatch
)


class TestMovingWindowVarianceHeuristic:
    """Tests for the MovingWindowVarianceHeuristic class."""

    def test_initialization(self):
        """Test that the heuristic initializes correctly."""
        heuristic = MovingWindowVarianceHeuristic(k=5)
        assert heuristic.k == 5
        assert len(heuristic) == 0
        assert heuristic.get_variance() is None

    def test_update_insufficient_data(self):
        """Test update with fewer than 2 values."""
        heuristic = MovingWindowVarianceHeuristic(k=5)
        assert heuristic.update(1.0) is None
        assert heuristic.update(2.0) is None # Still < 2? No, now 2.
        # Wait, update(1.0) -> size 1. update(2.0) -> size 2.
        # The update method returns variance if size >= 2.
        # Let's re-check the implementation logic.
        # In implementation: if len(self.window) < 2: self.window.append(value); return None
        # So first call: size 0 -> append -> size 1 -> return None.
        # Second call: size 1 -> append -> size 2 -> return None?
        # Ah, my implementation checks `if len(self.window) < 2` BEFORE appending?
        # No, I appended first in the code: `self.window.append(value)` then check.
        # Let's trace:
        # 1. update(1.0): window empty. append 1.0. len=1. returns None. Correct.
        # 2. update(2.0): window has 1.0. append 2.0. len=2. returns var([1,2])=0.5. Correct.
        # So first call returns None.
        
        heuristic = MovingWindowVarianceHeuristic(k=5)
        res1 = heuristic.update(1.0)
        assert res1 is None
        assert len(heuristic) == 1

        res2 = heuristic.update(2.0)
        assert res2 is not None
        assert len(heuristic) == 2

    def test_variance_calculation(self):
        """Test variance calculation with known values."""
        heuristic = MovingWindowVarianceHeuristic(k=3)
        
        # Add 3 values: 1, 2, 3
        # Variance of [1, 2, 3] (sample) = 1.0
        heuristic.update(1.0)
        heuristic.update(2.0)
        res = heuristic.update(3.0)
        
        expected = np.var([1.0, 2.0, 3.0], ddof=1)
        assert abs(res - expected) < 1e-6

    def test_window_sliding(self):
        """Test that the window slides correctly."""
        heuristic = MovingWindowVarianceHeuristic(k=2)
        
        # Add 1, 2 -> var(1,2)
        heuristic.update(1.0)
        heuristic.update(2.0)
        var1 = heuristic.get_variance()
        
        # Add 3 -> window is [2, 3] -> var(2,3)
        heuristic.update(3.0)
        var2 = heuristic.get_variance()
        
        expected1 = np.var([1.0, 2.0], ddof=1)
        expected2 = np.var([2.0, 3.0], ddof=1)
        
        assert abs(var1 - expected1) < 1e-6
        assert abs(var2 - expected2) < 1e-6

    def test_reset(self):
        """Test reset functionality."""
        heuristic = MovingWindowVarianceHeuristic(k=5)
        heuristic.update(1.0)
        heuristic.update(2.0)
        heuristic.reset()
        assert len(heuristic) == 0
        assert heuristic.get_variance() is None


class TestCalculateWindowedVariance:
    """Tests for the stateless calculate_windowed_variance function."""

    def test_basic_calculation(self):
        """Test basic variance calculation."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        k = 3
        # Last 3: [3, 4, 5]
        expected = np.var([3.0, 4.0, 5.0], ddof=1)
        result = calculate_windowed_variance(values, k)
        assert abs(result - expected) < 1e-6

    def test_insufficient_data(self):
        """Test with fewer values than k."""
        values = [1.0, 2.0]
        k = 5
        # Should return variance of all available if > 1
        expected = np.var([1.0, 2.0], ddof=1)
        result = calculate_windowed_variance(values, k)
        assert abs(result - expected) < 1e-6

    def test_single_value(self):
        """Test with a single value."""
        values = [1.0]
        k = 5
        result = calculate_windowed_variance(values, k)
        assert result is None

    def test_invalid_k(self):
        """Test with k < 2."""
        values = [1.0, 2.0, 3.0]
        with pytest.raises(ValueError):
            calculate_windowed_variance(values, 1)


class TestCompareHeuristicToFullbatch:
    """Tests for compare_heuristic_to_fullbatch."""

    def test_full_match(self):
        """Test when k equals the length of the list."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        k = 5
        
        h_var, f_var, ratio = compare_heuristic_to_fullbatch(values, k)
        
        expected_full = np.var(values, ddof=1)
        assert abs(f_var - expected_full) < 1e-6
        assert abs(h_var - expected_full) < 1e-6
        assert abs(ratio - 1.0) < 1e-6

    def test_partial_match(self):
        """Test when k is smaller than the length."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        k = 2
        
        h_var, f_var, ratio = compare_heuristic_to_fullbatch(values, k)
        
        expected_full = np.var(values, ddof=1)
        expected_heuristic = np.var([4.0, 5.0], ddof=1)
        
        assert abs(f_var - expected_full) < 1e-6
        assert abs(h_var - expected_heuristic) < 1e-6
        assert ratio is not None

    def test_insufficient_data(self):
        """Test with insufficient data."""
        values = [1.0]
        k = 5
        
        h_var, f_var, ratio = compare_heuristic_to_fullbatch(values, k)
        assert h_var is None
        assert f_var is None
        assert ratio is None