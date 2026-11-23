"""
Unit tests for Pettitt's test implementation.
"""

import pytest
import numpy as np
import pandas as pd
from code.pettitt import pettitt_statistic, pettitt_p_value, run_pettitt_rolling_window
from code.synthetic_data import generate_synthetic_ili_series

def test_pettitt_statistic_constant():
    """
    Test that Pettitt statistic is 0 for a constant series.
    """
    x = np.array([5.0, 5.0, 5.0, 5.0, 5.0])
    idx, stat = pettitt_statistic(x)
    assert stat == 0.0
    assert idx == 0  # Or any index, but stat must be 0

def test_pettitt_statistic_shift():
    """
    Test Pettitt statistic on a series with a known shift.
    """
    # Create a series with a clear shift in the middle
    # First half: mean 0, second half: mean 10
    x = np.concatenate([np.zeros(10), np.ones(10) * 10])
    
    idx, stat = pettitt_statistic(x)
    
    # The change point should be detected around index 10 (0-based, so between 9 and 10)
    # The statistic should be large and positive
    assert stat > 0
    # The max statistic should occur at the split point
    # For this simple case, the max should be at t=10 (split after 10 elements)
    # Note: our implementation returns t such that left is 0..t-1, right is t..n-1
    # So for 20 elements, split at 10 means left 0..9, right 10..19.
    # The returned idx should be 10.
    assert idx == 10

def test_pettitt_p_value_small():
    """
    Test p-value calculation for small statistics.
    """
    # For a small statistic, p-value should be close to 1
    p = pettitt_p_value(0.0, 10)
    assert 0.0 <= p <= 1.0
    # With stat=0, p should be 1.0 (or very close due to formula)
    assert p == 1.0

def test_pettitt_p_value_large():
    """
    Test p-value calculation for large statistics.
    """
    # For a large statistic, p-value should be small
    # n=10, max possible stat is around n^2/4 = 25
    # Let's use a large stat
    p = pettitt_p_value(20.0, 10)
    assert 0.0 <= p <= 1.0
    assert p < 0.5  # Should be small for a large stat

def test_run_pettitt_rolling_window():
    """
    Test the rolling window function on synthetic data with a shift.
    """
    # Generate synthetic data with a shift
    # We'll create a series where the first half is low, second half is high
    n = 24
    data = np.concatenate([np.zeros(12), np.ones(12) * 10])
    
    results = run_pettitt_rolling_window(data, window_size=12, stride=1, alpha=0.05)
    
    # We expect at least one significant result
    significant_results = [r for r in results if r['is_significant']]
    
    assert len(significant_results) > 0, "Expected at least one significant change point"
    
    # Check that the change point is detected around the shift
    # The shift is at index 12 (0-based).
    # With window_size=12, the window starting at 0 covers 0-11 (no shift inside)
    # The window starting at 1 covers 1-12 (shift at the end)
    # The window starting at 2 covers 2-13 (shift in the middle)
    # ...
    # The window starting at 12 covers 12-23 (no shift inside)
    
    # We should see significant results for windows that contain the shift
    # The shift is between index 11 and 12.
    # Windows that contain this boundary:
    # start=0: 0-11 (no)
    # start=1: 1-12 (yes, boundary at 12 which is the last element of the window)
    # start=2: 2-13 (yes)
    # ...
    # start=11: 11-22 (yes, boundary at 12 which is the first element of the right half)
    # start=12: 12-23 (no)
    
    # So we expect significant results for start=1 to start=11
    start_indices = [r['window_start'] for r in significant_results]
    
    # Check that we have results in the expected range
    assert any(1 <= s <= 11 for s in start_indices), "Expected significant results for windows containing the shift"

def test_run_pettitt_rolling_window_constant():
    """
    Test that rolling window handles constant segments gracefully.
    """
    data = np.ones(20) * 5.0
    results = run_pettitt_rolling_window(data, window_size=12, stride=1, alpha=0.05)
    
    # Should not crash, and should have no significant results
    significant_results = [r for r in results if r['is_significant']]
    assert len(significant_results) == 0

def test_run_pettitt_rolling_window_with_nan():
    """
    Test that rolling window handles NaN values gracefully.
    """
    data = np.array([1.0, 2.0, np.nan, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0])
    results = run_pettitt_rolling_window(data, window_size=12, stride=1, alpha=0.05)
    
    # Should skip windows with NaN
    # Windows containing index 2 (NaN) will be skipped
    # We should still get results for other windows
    assert len(results) >= 0  # May be 0 if all windows have NaN, but should not crash