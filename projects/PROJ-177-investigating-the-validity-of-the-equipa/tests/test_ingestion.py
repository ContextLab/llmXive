import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingestion import (
    ingest_driving_logs,
    handle_missing_frames,
    calculate_tracking_failure_rate,
    compute_velocity_angular_velocity,
    handle_non_stationary_segments,
    detect_non_stationary_segments,
    DataIngestionError
)

@pytest.fixture
def temp_input_dir():
    """Create a temporary directory with sample log files."""
    temp_dir = tempfile.mkdtemp()
    input_path = Path(temp_dir)
    
    # Create sample CSV log
    data = {
        'timestamp': [1.0, 2.0, 3.0, 4.0, 5.0],
        'signal': [10.0, 12.0, 11.0, 13.0, 14.0],
        'x': [0.1, 0.2, 0.3, 0.4, 0.5],
        'y': [0.1, 0.2, 0.3, 0.4, 0.5],
        'z': [0.1, 0.2, 0.3, 0.4, 0.5],
        'theta': [0.0, 0.1, 0.2, 0.3, 0.4]
    }
    df = pd.DataFrame(data)
    csv_path = input_path / "test_log.csv"
    df.to_csv(csv_path, index=False)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing."""
    data = {
        'timestamp': [1.0, 2.0, 3.0, 4.0, 5.0],
        'signal': [10.0, 12.0, 11.0, 13.0, 14.0],
        'x': [0.1, 0.2, 0.3, 0.4, 0.5],
        'y': [0.1, 0.2, 0.3, 0.4, 0.5],
        'z': [0.1, 0.2, 0.3, 0.4, 0.5],
        'theta': [0.0, 0.1, 0.2, 0.3, 0.4]
    }
    return pd.DataFrame(data)

def test_ingest_driving_logs(temp_input_dir):
    """Test ingestion of driving logs."""
    output_path = "data/derived/test_driving_signals.csv"
    try:
        df = ingest_driving_logs(input_dir=temp_input_dir, output_path=output_path)
        assert df is not None
        assert 'timestamp' in df.columns
        assert 'signal' in df.columns
        assert Path(output_path).exists()
    finally:
        if Path(output_path).exists():
            Path(output_path).unlink()

def test_handle_missing_frames(sample_dataframe):
    """Test handling of missing frames with explicit linear interpolation logic."""
    # Introduce a gap by setting a timestamp far away to simulate a missing frame window
    # and setting the values to NaN to represent the missing data state
    df = sample_dataframe.copy()
    
    # Simulate a missing frame at index 2 (timestamp jumps from 2.0 to 10.0)
    # We set the position values to NaN to represent the missing data that needs interpolation
    df.loc[2, 'timestamp'] = 10.0
    df.loc[2, 'x'] = np.nan
    df.loc[2, 'y'] = np.nan
    df.loc[2, 'z'] = np.nan
    df.loc[2, 'theta'] = np.nan
    
    # Also set the next frame to have a gap flag if needed, but primarily test the interpolation
    result = handle_missing_frames(df)
    
    # Assert the gap_flag column exists
    assert 'gap_flag' in result.columns
    
    # Assert the specific row with the gap is flagged
    # The logic in handle_missing_frames flags rows where the time delta is large
    # or where data was missing and interpolated
    assert result.loc[2, 'gap_flag'] == True
    
    # CRITICAL: Verify linear interpolation actually occurred
    # The value at index 2 should be interpolated between index 1 (0.2) and index 3 (0.4)
    # Expected value for linear interpolation: (0.2 + 0.4) / 2 = 0.3
    assert not np.isnan(result.loc[2, 'x']), "Interpolation failed: x is still NaN"
    assert np.isclose(result.loc[2, 'x'], 0.3, atol=1e-6), f"Linear interpolation failed: expected 0.3, got {result.loc[2, 'x']}"
    
    # Verify other columns too
    assert not np.isnan(result.loc[2, 'y'])
    assert not np.isnan(result.loc[2, 'z'])
    assert not np.isnan(result.loc[2, 'theta'])

def test_calculate_tracking_failure_rate(sample_dataframe):
    """Test tracking failure rate calculation."""
    df = sample_dataframe.copy()
    df['gap_flag'] = [False, False, True, False, False]
    
    rate = calculate_tracking_failure_rate(df)
    # 1 gap out of 5 rows = 0.2
    assert rate == 0.2

def test_compute_velocity_angular_velocity(sample_dataframe):
    """Test velocity and angular velocity computation."""
    result = compute_velocity_angular_velocity(sample_dataframe)
    # The function should compute velocity (v) or components (vx, vy) and angular velocity (omega)
    assert 'v' in result.columns or ('vx' in result.columns and 'vy' in result.columns)
    assert 'omega' in result.columns

def test_detect_non_stationary_segments(sample_dataframe):
    """Test detection of non-stationary segments."""
    # Create a signal with a clear chirp
    data = sample_dataframe.copy()
    data['signal'] = [10, 20, 30, 40, 50] # Linearly increasing (chirp-like)
    
    result = detect_non_stationary_segments(data, signal_col='signal')
    assert 'is_non_stationary' in result.columns

def test_handle_non_stationary_segments_exclude(sample_dataframe, temp_input_dir):
    """Test handling non-stationary signals with exclude strategy."""
    # Create a dataset with non-stationary signal
    data = sample_dataframe.copy()
    data['signal'] = [10, 20, 30, 40, 50]
    data['timestamp'] = [1, 2, 3, 4, 5]
    
    output_path = "artifacts/test_chirp_result.csv"
    try:
        result_df = handle_non_stationary_segments(
            data,
            strategy='exclude',
            signal_col='signal',
            output_path=output_path
        )
        assert Path(output_path).exists()
        # Check that non-stationary rows are excluded or marked
        assert 'is_non_stationary' in result_df.columns
    finally:
        if Path(output_path).exists():
            Path(output_path).unlink()

def test_handle_non_stationary_segments_bin(sample_dataframe, temp_input_dir):
    """Test handling non-stationary signals with bin strategy."""
    data = sample_dataframe.copy()
    data['signal'] = [10, 20, 30, 40, 50]
    data['timestamp'] = [1, 2, 3, 4, 5]
    data['frequency'] = [10.5, 11.2, 12.1, 13.0, 14.5]
    
    output_path = "artifacts/test_chirp_result_bin.csv"
    try:
        result_df = handle_non_stationary_segments(
            data,
            strategy='bin',
            signal_col='signal',
            output_path=output_path
        )
        assert Path(output_path).exists()
        assert 'frequency_bin' in result_df.columns
    finally:
        if Path(output_path).exists():
            Path(output_path).unlink()

def test_handle_non_stationary_segments_invalid_strategy(sample_dataframe):
    """Test error handling for invalid strategy."""
    with pytest.raises(ValueError):
        handle_non_stationary_segments(
            sample_dataframe,
            strategy='invalid',
            signal_col='signal'
        )

def test_interpolation_edge_cases():
    """Test interpolation when missing data is at the start or end."""
    df = pd.DataFrame({
        'timestamp': [1.0, 2.0, 3.0, 4.0, 5.0],
        'x': [0.1, np.nan, np.nan, 0.4, 0.5],
        'y': [0.1, 0.2, 0.3, 0.4, 0.5]
    })
    
    # Add a gap flag for the missing rows
    df['gap_flag'] = [False, True, True, False, False]
    
    result = handle_missing_frames(df)
    
    # Interpolation should work for the middle values (between 0.1 and 0.4)
    # Index 1: (0.1 + 0.4)/2 = 0.25 (roughly, depending on exact interpolation logic)
    # Index 2: (0.1 + 0.4)/2 = 0.25
    # Note: Pandas interpolate defaults to linear
    assert not np.isnan(result.loc[1, 'x'])
    assert not np.isnan(result.loc[2, 'x'])

def test_no_interpolation_needed():
    """Test that data without gaps passes through correctly."""
    df = pd.DataFrame({
        'timestamp': [1.0, 2.0, 3.0],
        'x': [0.1, 0.2, 0.3],
        'y': [0.1, 0.2, 0.3]
    })
    df['gap_flag'] = [False, False, False]
    
    result = handle_missing_frames(df)
    
    # Values should be identical
    assert result.loc[0, 'x'] == 0.1
    assert result.loc[1, 'x'] == 0.2
    assert result.loc[2, 'x'] == 0.3
    assert 'gap_flag' in result.columns