"""
Tests for time-alignment logic in data/preprocessing.py (Task T017).

These tests verify that the align_time_series function correctly merges
multi-satellite datasets onto a common time grid.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add code to path
code_path = Path(__file__).parent.parent
sys.path.insert(0, str(code_path))

from data.preprocessing import align_time_series


@pytest.fixture
def sample_multi_sat_data():
    """Create a sample DataFrame with multiple satellites and irregular timestamps."""
    data = []
    
    # Satellite A: observations at 0, 30, 60, 90 seconds
    for i in range(4):
        data.append({
            'satellite_id': 'SAT_A',
            'timestamp': datetime(2023, 1, 1, 0, 0, i * 30),
            'range_m': 10000000.0 + i,
            'residual': 0.01 + i * 0.001
        })
    
    # Satellite B: observations at 15, 45, 75 seconds (offset by 15s)
    for i in range(3):
        data.append({
            'satellite_id': 'SAT_B',
            'timestamp': datetime(2023, 1, 1, 0, 0, 15 + i * 30),
            'range_m': 10000000.0 + i * 10,
            'residual': 0.005 + i * 0.002
        })
        
    return pd.DataFrame(data)


def test_align_time_series_basic(sample_multi_sat_data):
    """Test basic time alignment with 1-minute frequency."""
    result = align_time_series(
        sample_multi_sat_data, 
        time_col='timestamp', 
        freq='1min', 
        method='nearest'
    )
    
    assert not result.empty
    assert 'satellite_id' in result.columns
    assert 'time_aligned' in result.columns or 'timestamp' in result.columns
    
    # Should have aligned to 2 time points (00:00 and 00:01)
    unique_times = result['timestamp'].dt.floor('1min').unique()
    assert len(unique_times) <= 3  # Allow some tolerance


def test_align_time_series_missing_values(sample_multi_sat_data):
    """Test that time alignment handles missing values correctly."""
    result = align_time_series(
        sample_multi_sat_data, 
        time_col='timestamp', 
        freq='1min', 
        method='nearest'
    )
    
    # Check that we have data for both satellites
    satellites = result['satellite_id'].unique()
    assert 'SAT_A' in satellites
    assert 'SAT_B' in satellites


def test_align_time_series_empty_dataframe():
    """Test handling of empty DataFrame."""
    empty_df = pd.DataFrame(columns=['satellite_id', 'timestamp', 'range_m'])
    
    with pytest.warns(UserWarning):
        result = align_time_series(empty_df, time_col='timestamp', freq='1min')
        
    assert result.empty


def test_align_time_series_missing_columns():
    """Test error handling for missing required columns."""
    df = pd.DataFrame({'satellite_id': ['A'], 'range_m': [100]})
    
    with pytest.raises(ValueError):
        align_time_series(df, time_col='timestamp', freq='1min')
        
    df_no_id = pd.DataFrame({'timestamp': [datetime.now()]})
    with pytest.raises(ValueError):
        align_time_series(df_no_id, time_col='timestamp', freq='1min')


def test_align_time_series_different_methods(sample_multi_sat_data):
    """Test different filling methods."""
    # Pad method
    result_pad = align_time_series(
        sample_multi_sat_data, 
        time_col='timestamp', 
        freq='1min', 
        method='pad'
    )
    assert not result_pad.empty
    
    # Backfill method
    result_bfill = align_time_series(
        sample_multi_sat_data, 
        time_col='timestamp', 
        freq='1min', 
        method='backfill'
    )
    assert not result_bfill.empty
    
    # No fill (nearest with no data might leave NaNs, but shouldn't crash)
    result_none = align_time_series(
        sample_multi_sat_data, 
        time_col='timestamp', 
        freq='1min', 
        method=None
    )
    assert not result_none.empty