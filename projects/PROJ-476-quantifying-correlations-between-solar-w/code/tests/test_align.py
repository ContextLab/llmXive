"""
Unit tests for the alignment module.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
import warnings
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.data.align import align_to_grid, merge_datasets, validate_and_normalize, interpolate_gaps
from code.config import ACE_VARS, NOAA_VARS

def test_align_interpolates_small_gaps_warns_large():
    """
    Test that alignment correctly handles gaps:
    - Gaps <= 6 hours should be filled (interpolated)
    - Gaps > 6 hours should trigger a warning (in real implementation)
    
    This test verifies the resampling logic creates a continuous 1-hour grid
    and that interpolation logic behaves as expected for small gaps while
    warning for large gaps.
    """
    # Create test data with a small gap (3 hours: missing 3, 4, 5)
    # and a large gap (10 hours: missing 9 through 18)
    timestamps = [
        datetime(2020, 1, 1, 0, 0),
        datetime(2020, 1, 1, 1, 0),
        datetime(2020, 1, 1, 2, 0),
        # Gap: missing 3, 4, 5 (3 hour gap) -> Should interpolate
        datetime(2020, 1, 1, 6, 0),
        datetime(2020, 1, 1, 7, 0),
        datetime(2020, 1, 1, 8, 0),
        # Large gap: missing 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 (10 hour gap) -> Should warn
        datetime(2020, 1, 1, 19, 0),
    ]
    
    # Values chosen so linear interpolation is predictable
    # 0->1->2 (linear), then jump to 6->7->8 (linear), then jump to 19
    # Interpolated values for 3,4,5 should be 4.0, 5.0, 6.0
    values = [1.0, 2.0, 3.0, 6.0, 7.0, 8.0, 19.0]
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'N_p': values
    })
    
    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Align to 1-hour grid
        aligned = align_to_grid(df)
        aligned = aligned.reset_index()
        
        # Check that we have continuous 1-hour intervals
        # From 0:00 to 19:00 should be 20 records (including gaps filled)
        expected_count = 20
        assert len(aligned) == expected_count, f"Expected {expected_count} records, got {len(aligned)}"
        
        # Check that timestamps are exactly 1 hour apart
        for i in range(1, len(aligned)):
            diff = aligned.iloc[i]['timestamp'] - aligned.iloc[i-1]['timestamp']
            assert diff == pd.Timedelta(hours=1), f"Gap of {diff} detected at index {i}"
    
    # Verify interpolation for the small gap (3 hours)
    # Indices 3, 4, 5 correspond to timestamps 3:00, 4:00, 5:00
    # Expected interpolated values: 4.0, 5.0, 6.0
    small_gap_indices = [3, 4, 5]
    expected_small_gap_values = [4.0, 5.0, 6.0]
    
    for idx, expected_val in zip(small_gap_indices, expected_small_gap_values):
        actual_val = aligned.iloc[idx]['N_p']
        assert np.isclose(actual_val, expected_val), \
            f"Interpolation failed at index {idx}: expected {expected_val}, got {actual_val}"
    
    # Verify that a warning was raised for the large gap (> 6 hours)
    # The large gap is 10 hours (missing 9 through 18)
    warning_messages = [str(warning.message) for warning in w]
    large_gap_warnings = [msg for msg in warning_messages if "large gap" in msg.lower() or "10 hour" in msg]
    
    assert len(large_gap_warnings) > 0, \
        f"Expected a warning for large gap (> 6h), but no warning was raised. Warnings captured: {warning_messages}"
    
    # Verify the warning mentions the gap size or duration
    assert any("10" in msg or "large" in msg.lower() for msg in large_gap_warnings), \
        f"Warning message should indicate the large gap size. Messages: {large_gap_warnings}"

def test_align_handles_empty_dataframe():
    """Test that align_to_grid handles empty dataframes gracefully."""
    df = pd.DataFrame(columns=['timestamp', 'N_p'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    with pytest.raises(Exception):
        # Resampling empty dataframe should raise or handle appropriately
        aligned = align_to_grid(df)
        # If it doesn't raise, it should be empty
        assert len(aligned) == 0

def test_merge_datasets():
    """Test merging of ACE and NOAA datasets."""
    ace_df = pd.DataFrame({
        'timestamp': [datetime(2020, 1, 1, 0, 0), datetime(2020, 1, 1, 1, 0)],
        'N_p': [5.0, 6.0],
        'T_p': [10.0, 11.0]
    })
    
    noaa_df = pd.DataFrame({
        'timestamp': [datetime(2020, 1, 1, 0, 0), datetime(2020, 1, 1, 1, 0)],
        'Kp': [3.0, 4.0],
        'Dst': [-20.0, -25.0]
    })
    
    merged = merge_datasets(ace_df, noaa_df)
    
    assert len(merged) == 2
    assert 'N_p' in merged.columns
    assert 'Kp' in merged.columns
    assert merged.iloc[0]['N_p'] == 5.0
    assert merged.iloc[0]['Kp'] == 3.0

def test_validate_and_normalize():
    """Test validation and normalization of merged data."""
    merged_df = pd.DataFrame({
        'timestamp': [datetime(2020, 1, 1, 0, 0)],
        'N_p': [5.0],
        'T_p': [10.0],
        'He2+_ratio': [0.1],
        'Kp': [3.0],
        'Dst': [-20.0]
    })
    
    # This should pass validation
    result = validate_and_normalize(merged_df)
    
    # Check that columns are normalized to lowercase
    assert all(col.islower() for col in result.columns if col != 'timestamp')
    assert 'n_p' in result.columns
    assert 'k_p' in result.columns

if __name__ == "__main__":
    pytest.main([__file__, "-v"])