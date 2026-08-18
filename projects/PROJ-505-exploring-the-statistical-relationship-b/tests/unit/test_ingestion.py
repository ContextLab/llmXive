import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path if running standalone
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.ingestion.align import resample_to_hourly_median, validate_temporal_alignment
from code.utils.logging import AlignmentError

@pytest.fixture
def sample_data_with_gaps():
    """
    Create a sample DataFrame with irregular timestamps and multiple values per hour
    to test the 1-hour resampling and median aggregation logic.
    """
    # Start time
    base_time = datetime(2023, 1, 1, 0, 0, 0)
    
    # Generate irregular timestamps (some hours have multiple entries, some have gaps)
    timestamps = [
        base_time,
        base_time + timedelta(minutes=10),
        base_time + timedelta(minutes=20),
        base_time + timedelta(hours=1, minutes=5),
        base_time + timedelta(hours=1, minutes=30),
        base_time + timedelta(hours=1, minutes=45),
        base_time + timedelta(hours=3, minutes=0),  # Gap: missing hour 2
        base_time + timedelta(hours=3, minutes=15),
        base_time + timedelta(hours=3, minutes=45),
        base_time + timedelta(hours=4, minutes=10),
    ]
    
    # Create data with known values for verification
    data = {
        'timestamp': timestamps,
        'Dst': [10.0, 12.0, 14.0, 20.0, 22.0, 24.0, 30.0, 32.0, 34.0, 40.0],
        'Kp': [3.0, 3.3, 3.6, 4.0, 4.3, 4.6, 5.0, 5.3, 5.6, 6.0],
        'He_H': [0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13],
        'O_Fe': [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9],
        'C_O': [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95],
    }
    
    df = pd.DataFrame(data)
    return df

@pytest.fixture
def sample_data_monotonic():
    """
    Create a sample DataFrame with strictly monotonically increasing timestamps.
    """
    base_time = datetime(2023, 1, 1, 0, 0, 0)
    timestamps = [base_time + timedelta(hours=i) for i in range(10)]
    
    data = {
        'timestamp': timestamps,
        'Dst': [10.0 + i for i in range(10)],
        'Kp': [3.0 + i * 0.3 for i in range(10)],
    }
    return pd.DataFrame(data)

def test_resample_to_hourly_median_aggregation(sample_data_with_gaps):
    """
    Verify that resample_to_hourly_median correctly:
    1. Groups data into 1-hour bins
    2. Calculates the median for each numeric column
    3. Handles hours with multiple entries
    """
    result = resample_to_hourly_median(sample_data_with_gaps, 'timestamp')
    
    # Check that the result has hourly frequency
    assert len(result) > 0
    
    # Verify the timestamps are at the hour boundary
    for ts in result['timestamp']:
        assert ts.minute == 0
        assert ts.second == 0
    
    # Verify median calculation for hour 0 (entries at 0:00, 0:10, 0:20)
    # Dst: [10, 12, 14] -> median = 12
    # Kp: [3.0, 3.3, 3.6] -> median = 3.3
    hour_0_row = result[result['timestamp'] == pd.Timestamp('2023-01-01 00:00:00')]
    assert len(hour_0_row) == 1
    assert np.isclose(hour_0_row['Dst'].iloc[0], 12.0, atol=1e-5)
    assert np.isclose(hour_0_row['Kp'].iloc[0], 3.3, atol=1e-5)
    
    # Verify median calculation for hour 1 (entries at 1:05, 1:30, 1:45)
    # Dst: [20, 22, 24] -> median = 22
    # Kp: [4.0, 4.3, 4.6] -> median = 4.3
    hour_1_row = result[result['timestamp'] == pd.Timestamp('2023-01-01 01:00:00')]
    assert len(hour_1_row) == 1
    assert np.isclose(hour_1_row['Dst'].iloc[0], 22.0, atol=1e-5)
    assert np.isclose(hour_1_row['Kp'].iloc[0], 4.3, atol=1e-5)

def test_resample_to_hourly_median_handles_gaps(sample_data_with_gaps):
    """
    Verify that resample_to_hourly_median correctly handles missing hours
    by not creating rows for them (unless fillna is explicitly requested, 
    which is not the case in the default behavior).
    """
    result = resample_to_hourly_median(sample_data_with_gaps, 'timestamp')
    
    # Check that hour 2 (missing in source) is NOT in the result
    hour_2_present = any(ts.hour == 2 for ts in result['timestamp'])
    assert not hour_2_present, "Missing hours should not be created by default"
    
    # Verify that hour 3 exists (it has data)
    hour_3_row = result[result['timestamp'] == pd.Timestamp('2023-01-01 03:00:00')]
    assert len(hour_3_row) == 1

def test_resample_to_hourly_median_single_entry_per_hour():
    """
    Verify that when there is exactly one entry per hour, the median equals the value.
    """
    base_time = datetime(2023, 1, 1, 0, 0, 0)
    timestamps = [base_time + timedelta(hours=i) for i in range(5)]
    
    data = {
        'timestamp': timestamps,
        'Dst': [10.0, 20.0, 30.0, 40.0, 50.0],
        'Kp': [3.0, 4.0, 5.0, 6.0, 7.0],
    }
    df = pd.DataFrame(data)
    
    result = resample_to_hourly_median(df, 'timestamp')
    
    # Verify values are preserved
    assert len(result) == 5
    assert np.isclose(result['Dst'].iloc[0], 10.0)
    assert np.isclose(result['Dst'].iloc[1], 20.0)
    assert np.isclose(result['Kp'].iloc[2], 5.0)

def test_validate_temporal_alignment_monotonic(sample_data_monotonic):
    """
    Verify that validate_temporal_alignment passes for monotonically increasing timestamps.
    """
    # This should not raise an error
    try:
        validate_temporal_alignment(sample_data_monotonic, 'timestamp')
    except AlignmentError as e:
        pytest.fail(f"validate_temporal_alignment raised unexpected error: {e}")

def test_validate_temporal_alignment_non_monotonic():
    """
    Verify that validate_temporal_alignment raises AlignmentError for non-monotonic timestamps.
    """
    base_time = datetime(2023, 1, 1, 0, 0, 0)
    # Create non-monotonic timestamps
    timestamps = [
        base_time,
        base_time + timedelta(hours=1),
        base_time + timedelta(hours=0, minutes=30),  # Backwards!
        base_time + timedelta(hours=2),
    ]
    
    data = {
        'timestamp': timestamps,
        'Dst': [10.0, 20.0, 15.0, 30.0],
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(AlignmentError, match="Timestamps are not monotonically increasing"):
        validate_temporal_alignment(df, 'timestamp')

def test_validate_temporal_alignment_duplicate_timestamps():
    """
    Verify that validate_temporal_alignment handles duplicate timestamps gracefully.
    (Duplicates are allowed if they represent multiple measurements at the same time)
    """
    base_time = datetime(2023, 1, 1, 0, 0, 0)
    timestamps = [base_time, base_time, base_time + timedelta(hours=1)]
    
    data = {
        'timestamp': timestamps,
        'Dst': [10.0, 11.0, 20.0],
    }
    df = pd.DataFrame(data)
    
    # Duplicates are allowed, so this should pass
    try:
        validate_temporal_alignment(df, 'timestamp')
    except AlignmentError as e:
        pytest.fail(f"validate_temporal_alignment raised unexpected error for duplicates: {e}")

def test_resample_to_hourly_median_with_nan():
    """
    Verify that resample_to_hourly_median correctly handles NaN values in the data.
    """
    base_time = datetime(2023, 1, 1, 0, 0, 0)
    timestamps = [
        base_time,
        base_time + timedelta(minutes=10),
        base_time + timedelta(hours=1),
        base_time + timedelta(hours=1, minutes=30),
    ]
    
    data = {
        'timestamp': timestamps,
        'Dst': [10.0, np.nan, 20.0, 25.0],
        'Kp': [3.0, 3.5, np.nan, 4.5],
    }
    df = pd.DataFrame(data)
    
    result = resample_to_hourly_median(df, 'timestamp')
    
    # Hour 0: [10.0, NaN] -> median should be 10.0 (ignoring NaN)
    hour_0_row = result[result['timestamp'] == pd.Timestamp('2023-01-01 00:00:00')]
    assert np.isclose(hour_0_row['Dst'].iloc[0], 10.0)
    
    # Hour 1: [NaN, 25.0] -> median should be 25.0 (ignoring NaN)
    hour_1_row = result[result['timestamp'] == pd.Timestamp('2023-01-01 01:00:00')]
    assert np.isclose(hour_1_row['Dst'].iloc[0], 25.0)
    assert np.isclose(hour_1_row['Kp'].iloc[0], 4.5)