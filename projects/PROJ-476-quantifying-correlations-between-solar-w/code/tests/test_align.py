import pytest
import pandas as pd
import numpy as np
from datetime import timedelta
import warnings
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.data.align import align_to_hourly, interpolate_gaps

@pytest.fixture
def sample_ace_data():
    """Create sample ACE data with known gaps."""
    dates = pd.date_range(start='2020-01-01', end='2020-01-02', freq='30min')
    data = {
        'N_p': np.random.rand(len(dates)),
        'T_p': np.random.rand(len(dates)) * 100000,
        'He2+_ratio': np.random.rand(len(dates)) * 0.1
    }
    df = pd.DataFrame(data, index=dates)
    return df

@pytest.fixture
def sample_noaa_data():
    """Create sample NOAA data with known gaps."""
    dates = pd.date_range(start='2020-01-01', end='2020-01-02', freq='1h')
    data = {
        'Kp': np.random.randint(0, 10, len(dates)),
        'Dst': np.random.randint(-100, 50, len(dates))
    }
    df = pd.DataFrame(data, index=dates)
    return df

def test_align_interpolates_small_gaps_warns_large():
    """
    Test that gaps <= 6h are filled and gaps > 6h trigger a warning.
    """
    # Create a time series with a small gap (3 hours) and a large gap (8 hours)
    dates = pd.date_range(start='2020-01-01', end='2020-01-03', freq='1h')
    values = np.arange(len(dates), dtype=float)
    
    # Introduce a small gap (3 hours)
    values[10:13] = np.nan
    
    # Introduce a large gap (8 hours)
    values[20:28] = np.nan
    
    series = pd.Series(values, index=dates)
    
    # Test interpolation with max_gap=6h
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = interpolate_gaps(series, max_gap_hours=6)
        
        # Check that a warning was raised for the large gap
        assert len(w) >= 1, "Expected at least one warning for large gaps"
        assert any("Gap of 8h" in str(warning.message) for warning in w), \
            f"Expected warning about 8h gap, got: {[str(w.message) for w in w]}"
        
        # Check that the small gap was filled
        assert not result[10:13].isna().any(), "Small gap (3h) should be filled"
        
        # Check that the large gap remains (mostly) NaN
        # Note: interpolation might fill some edges, but the middle should be NaN
        assert result[20:28].isna().sum() > 0, "Large gap (8h) should remain NaN"
        
        # Verify that the small gap values are actually interpolated
        # They should be between the surrounding values
        assert result[11] > result[9], "Interpolated value should be increasing"
        assert result[11] < result[13] if not np.isnan(result[13]) else True, \
            "Interpolated value should be between surrounding values"

def test_align_resamples_to_hourly():
    """Test that align_to_hourly correctly resamples to hourly frequency."""
    # Create data with 30-minute intervals
    dates = pd.date_range(start='2020-01-01', end='2020-01-02', freq='30min')
    data = {
        'N_p': np.arange(len(dates), dtype=float)
    }
    df = pd.DataFrame(data, index=dates)
    
    # Resample to hourly
    hourly_series = align_to_hourly(df, 'N_p')
    
    # Check that the frequency is hourly
    assert hourly_series.index.freq == pd.Timedelta(hours=1), \
        f"Expected hourly frequency, got {hourly_series.index.freq}"
    
    # Check that the number of rows is approximately half (since we had 30-min data)
    expected_rows = len(dates) // 2
    assert abs(len(hourly_series) - expected_rows) <= 1, \
        f"Expected ~{expected_rows} rows, got {len(hourly_series)}"

def test_interpolate_gaps_basic():
    """Test basic interpolation functionality."""
    dates = pd.date_range(start='2020-01-01', end='2020-01-02', freq='1h')
    values = np.arange(len(dates), dtype=float)
    
    # Create a single gap
    values[10] = np.nan
    values[11] = np.nan
    
    series = pd.Series(values, index=dates)
    
    # Interpolate
    result = interpolate_gaps(series, max_gap_hours=6)
    
    # Check that the gap is filled
    assert not result[10:12].isna().any(), "Gap should be filled"
    
    # Check that the values are interpolated correctly
    # Linear interpolation between 9.0 and 12.0 should give 10.0 and 11.0
    assert result[10] == 10.0, f"Expected 10.0, got {result[10]}"
    assert result[11] == 11.0, f"Expected 11.0, got {result[11]}"

def test_align_handles_empty_dataframe():
    """Test that align_to_hourly handles empty dataframes gracefully."""
    empty_df = pd.DataFrame()
    
    # Should raise a clear error or return empty series
    with pytest.raises((KeyError, ValueError)):
        align_to_hourly(empty_df, 'N_p')
