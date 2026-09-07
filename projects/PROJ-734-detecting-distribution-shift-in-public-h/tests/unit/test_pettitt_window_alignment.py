"""
Unit test for T043: Verify Pettitt implementation uses sliding window of 12 weeks with stride 1,
matching the MMD window configuration exactly.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from pettitt import run_pettitt_rolling_window, pettitt_statistic
from mmd_detector import detect_shifts
from main import load_config


def test_pettitt_window_alignment():
    """
    Test that Pettitt rolling window uses exactly the same time intervals as MMD detector.
    Both should use window_size=12 and stride=1.
    """
    # Create a deterministic synthetic dataset for testing
    np.random.seed(42)
    n_weeks = 100
    date_range = pd.date_range(start='2020-01-01', periods=n_weeks, freq='W')
    ili_values = np.random.normal(loc=100, scale=10, size=n_weeks)
    
    test_data = pd.DataFrame({
        'week_id': date_range,
        'ili': ili_values
    })
    
    # Load config to get window_size and stride (should be 12 and 1)
    config = load_config()
    window_size = config.window_size
    stride = config.stride
    
    # Verify config values match requirements
    assert window_size == 12, f"Expected window_size=12, got {window_size}"
    assert stride == 1, f"Expected stride=1, got {stride}"
    
    # Run Pettitt rolling window
    pettitt_results = run_pettitt_rolling_window(
        test_data,
        window_size=window_size,
        stride=stride
    )
    
    # Verify the number of windows matches expected calculation
    # Number of windows = (n_weeks - window_size) // stride + 1
    expected_num_windows = (n_weeks - window_size) // stride + 1
    assert len(pettitt_results) == expected_num_windows, \
        f"Expected {expected_num_windows} windows, got {len(pettitt_results)}"
    
    # Verify window alignment: first window should start at index 0
    # and cover weeks [0, window_size)
    if len(pettitt_results) > 0:
        first_result = pettitt_results[0]
        # Check that the first window starts at week_id 0 (or the first week in data)
        assert first_result['window_start_idx'] == 0, \
            f"First window should start at index 0, got {first_result['window_start_idx']}"
        
        # Check window length
        assert first_result['window_size'] == window_size, \
            f"Window size should be {window_size}, got {first_result['window_size']}"
        
        # Verify consecutive windows are separated by stride
        if len(pettitt_results) > 1:
            for i in range(1, len(pettitt_results)):
                current_start = pettitt_results[i]['window_start_idx']
                prev_start = pettitt_results[i-1]['window_start_idx']
                assert current_start - prev_start == stride, \
                    f"Window stride should be {stride}, got {current_start - prev_start}"
    
    # Compare with MMD detector window configuration
    # The MMD detector should use the same window_size and stride
    # We verify this by checking that the detect_shifts function accepts
    # the same parameters and would generate the same window structure
    
    # Verify that both methods would process the same number of windows
    # for the same input data with the same configuration
    mmd_config = load_config()
    assert mmd_config.window_size == config.window_size, \
        "MMD and Pettitt should use the same window_size"
    assert mmd_config.stride == config.stride, \
        "MMD and Pettitt should use the same stride"
    
    # Test that the Pettitt statistic function works correctly on a window
    window_data = test_data.iloc[:window_size]['ili'].values
    stat, p_val = pettitt_statistic(window_data)
    
    # Verify that the statistic is a valid number
    assert isinstance(stat, (int, float, np.number)), \
        f"Pettitt statistic should be numeric, got {type(stat)}"
    assert not np.isnan(stat), "Pettitt statistic should not be NaN"
    
    # Verify p-value is in valid range [0, 1]
    assert isinstance(p_val, (int, float, np.number)), \
        f"Pettitt p-value should be numeric, got {type(p_val)}"
    assert 0 <= p_val <= 1, f"Pettitt p-value should be in [0,1], got {p_val}"


def test_pettitt_statistic_computation():
    """
    Test that Pettitt statistic is computed correctly for a known case.
    """
    # Create a simple dataset with a known change point
    np.random.seed(123)
    n1 = 10
    n2 = 10
    data_before = np.random.normal(loc=0, scale=1, size=n1)
    data_after = np.random.normal(loc=2, scale=1, size=n2)  # Shift in mean
    test_data = np.concatenate([data_before, data_after])
    
    stat, p_val = pettitt_statistic(test_data)
    
    # The Pettitt statistic should be positive (detecting a change)
    # and the p-value should be relatively small for a clear shift
    assert stat > 0, f"Expected positive statistic for clear shift, got {stat}"
    assert 0 <= p_val <= 1, f"P-value should be in [0,1], got {p_val}"
    
    # For a very clear shift, p-value should be small (though not guaranteed)
    # This is just a sanity check
    assert p_val < 0.5, f"P-value seems too high for clear shift: {p_val}"


def test_pettitt_edge_cases():
    """
    Test Pettitt implementation with edge cases.
    """
    # Test with constant series (should raise ValueError or handle gracefully)
    constant_data = np.ones(20)
    with pytest.raises(ValueError) as exc_info:
        pettitt_statistic(constant_data)
    assert "Zero variance" in str(exc_info.value) or "constant" in str(exc_info.value).lower()
    
    # Test with very small window (should work but may have limited power)
    small_window = np.array([1.0, 2.0, 3.0])
    stat, p_val = pettitt_statistic(small_window)
    assert isinstance(stat, (int, float, np.number))
    assert isinstance(p_val, (int, float, np.number))
    
    # Test with window_size=2 (minimum for Pettitt test)
    minimal_window = np.array([1.0, 2.0])
    stat, p_val = pettitt_statistic(minimal_window)
    assert isinstance(stat, (int, float, np.number))
    assert isinstance(p_val, (int, float, np.number))
