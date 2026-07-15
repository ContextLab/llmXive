import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Ensure project root is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.data.clean import clean_and_resample

def test_clean_removes_nan():
    """Test that clean_and_resample removes NaN values."""
    # Create DataFrame with NaN values
    timestamps = pd.date_range(start='2023-01-01', periods=10, freq='5min')
    df1 = pd.DataFrame({
        'timestamp': timestamps,
        'Vsw': [400, 410, np.nan, 420, 430, np.nan, 440, 450, 460, 470]
    })
    
    df2 = pd.DataFrame({
        'timestamp': timestamps,
        'Ey': [1.0, 1.1, 1.2, np.nan, 1.4, 1.5, 1.6, 1.7, np.nan, 1.9]
    })
    
    # Clean and resample
    cleaned_df1, cleaned_df2 = clean_and_resample(df1, df2)
    
    # Verify no NaN values remain
    assert not cleaned_df1['Vsw'].isna().any()
    assert not cleaned_df2['Ey'].isna().any()
    
    # Verify rows were removed
    assert len(cleaned_df1) < len(df1)
    assert len(cleaned_df2) < len(df2)

def test_clean_resamples_to_5min():
    """Test that clean_and_resample resamples to 5-minute intervals."""
    # Create DataFrame with irregular timestamps
    timestamps = [
        datetime(2023, 1, 1, 0, 0),
        datetime(2023, 1, 1, 0, 7),  # 7 minutes
        datetime(2023, 1, 1, 0, 12), # 12 minutes
        datetime(2023, 1, 1, 0, 18), # 18 minutes
        datetime(2023, 1, 1, 0, 23), # 23 minutes
    ]
    
    df1 = pd.DataFrame({
        'timestamp': timestamps,
        'Vsw': [400, 410, 420, 430, 440]
    })
    
    df2 = pd.DataFrame({
        'timestamp': timestamps,
        'Ey': [1.0, 1.1, 1.2, 1.3, 1.4]
    })
    
    # Clean and resample
    cleaned_df1, cleaned_df2 = clean_and_resample(df1, df2)
    
    # Verify timestamps are at 5-minute intervals
    time_diffs = cleaned_df1['timestamp'].diff().dropna()
    expected_diff = pd.Timedelta(minutes=5)
    
    for diff in time_diffs:
        assert diff == expected_diff, f"Expected {expected_diff}, got {diff}"

def test_clean_handles_empty_input():
    """Test that clean_and_resample handles empty DataFrames."""
    df1_empty = pd.DataFrame(columns=['timestamp', 'Vsw'])
    df2_empty = pd.DataFrame(columns=['timestamp', 'Ey'])
    
    # Should not raise an exception
    cleaned_df1, cleaned_df2 = clean_and_resample(df1_empty, df2_empty)
    
    # Should return empty DataFrames
    assert len(cleaned_df1) == 0
    assert len(cleaned_df2) == 0

def test_clean_all_nan():
    """Test that clean_and_resample handles all-NaN columns."""
    timestamps = pd.date_range(start='2023-01-01', periods=5, freq='5min')
    df1 = pd.DataFrame({
        'timestamp': timestamps,
        'Vsw': [np.nan, np.nan, np.nan, np.nan, np.nan]
    })
    
    df2 = pd.DataFrame({
        'timestamp': timestamps,
        'Ey': [1.0, 1.1, 1.2, 1.3, 1.4]
    })
    
    # Should handle all-NaN column gracefully
    cleaned_df1, cleaned_df2 = clean_and_resample(df1, df2)
    
    # df1 should be empty after removing all-NaN
    assert len(cleaned_df1) == 0
    # df2 should also be empty since no common timestamps remain
    assert len(cleaned_df2) == 0

def test_clean_single_value():
    """Test that clean_and_resample handles single-value DataFrames."""
    timestamps = [datetime(2023, 1, 1, 0, 0)]
    df1 = pd.DataFrame({
        'timestamp': timestamps,
        'Vsw': [400]
    })
    
    df2 = pd.DataFrame({
        'timestamp': timestamps,
        'Ey': [1.0]
    })
    
    # Should not raise an exception
    cleaned_df1, cleaned_df2 = clean_and_resample(df1, df2)
    
    # Should return single-row DataFrames
    assert len(cleaned_df1) == 1
    assert len(cleaned_df2) == 1
    assert cleaned_df1['Vsw'].iloc[0] == 400
    assert cleaned_df2['Ey'].iloc[0] == 1.0