"""
Unit tests for data cleaning and resampling.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from code.data.clean import clean_and_resample, handle_gaps

def test_clean_removes_nan():
    """Test that clean_and_resample removes rows with NaN values."""
    # Create test data with NaN
    dates = pd.date_range(start='2023-01-01', periods=10, freq='5min')
    df_sw = pd.DataFrame({
        'timestamp': dates,
        'Vsw': [400.0, 401.0, np.nan, 403.0, 404.0, 405.0, 406.0, 407.0, 408.0, 409.0],
        'Bz': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    })
    df_ey = pd.DataFrame({
        'timestamp': dates,
        'Ey': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    })

    df_sw_clean, df_ey_clean = clean_and_resample(df_sw, df_ey)

    # Check that the row with NaN in Vsw is removed
    assert len(df_sw_clean) < 10
    assert not df_sw_clean['Vsw'].isna().any()
    assert not df_ey_clean['Ey'].isna().any()

def test_clean_resamples_to_5min():
    """Test that clean_and_resample resamples to 5-minute intervals."""
    # Create data with irregular intervals (e.g., 1 min)
    dates = pd.date_range(start='2023-01-01', periods=20, freq='1min')
    df_sw = pd.DataFrame({
        'timestamp': dates,
        'Vsw': np.arange(20, dtype=float) + 400.0,
        'Bz': np.arange(20, dtype=float)
    })
    df_ey = pd.DataFrame({
        'timestamp': dates,
        'Ey': np.arange(20, dtype=float) * 0.1
    })

    df_sw_clean, df_ey_clean = clean_and_resample(df_sw, df_ey)

    # Check frequency
    assert df_sw_clean.index.freq == pd.Timedelta(minutes=5) or df_sw_clean.index.freqstr == '5T'
    assert len(df_sw_clean) < 20  # Should be resampled

def test_clean_handles_large_gaps():
    """Test that handle_gaps detects and truncates large gaps."""
    # Create data with a large gap
    dates = pd.date_range(start='2023-01-01', periods=10, freq='5min')
    # Insert a gap of 60 minutes
    dates = list(dates) + [dates[-1] + pd.Timedelta(minutes=60)] + list(dates[-9:])
    dates = pd.DatetimeIndex(dates)
    
    df = pd.DataFrame({
        'Vsw': np.arange(len(dates), dtype=float) + 400.0
    }, index=dates)

    df_result = handle_gaps(df, max_gap_minutes=30)

    # Should be truncated before the gap
    assert len(df_result) < len(df)
    # The last index should be before the 60-minute gap
    last_idx = df_result.index[-1]
    # The gap started at the 10th element (index 9 in original list)
    # So we should have kept up to the 9th element (index 8 in original list? No, index 9 is the last one before gap)
    # Let's just verify it's not the full length
    assert len(df_result) == 10  # Should keep the first 10 points

def test_clean_handles_empty_input():
    """Test that clean_and_resample handles empty DataFrames."""
    df_sw = pd.DataFrame(columns=['timestamp', 'Vsw', 'Bz'])
    df_ey = pd.DataFrame(columns=['timestamp', 'Ey'])

    # Should not raise an error
    df_sw_clean, df_ey_clean = clean_and_resample(df_sw, df_ey)
    assert df_sw_clean.empty
    assert df_ey_clean.empty
