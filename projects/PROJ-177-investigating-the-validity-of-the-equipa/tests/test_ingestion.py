import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion import calculate_tracking_failure_rate, IngestionError

@pytest.fixture
def sample_tracking_data():
    """Create sample particle tracking data with controlled missing frames."""
    n_windows = 5
    window_size = 100
    frames_per_window = [100, 80, 100, 70, 100]  # Window 1 and 3 have missing frames (20% and 30% loss)
    
    data = []
    current_time = datetime(2023, 1, 1, 0, 0, 0)
    
    for window_idx, frames in enumerate(frames_per_window):
        for i in range(frames):
            data.append({
                'particle_id': f'p{window_idx}',
                'timestamp': current_time + timedelta(seconds=i*0.01),
                'x': np.random.rand(),
                'y': np.random.rand(),
                'z': np.random.rand()
            })
        current_time += timedelta(seconds=window_size * 0.01 + 0.1)  # Add gap between windows
    
    return pd.DataFrame(data)

@pytest.fixture
def incomplete_tracking_data():
    """Create sample data with high missing frame rate (>20%)."""
    n_windows = 3
    window_size = 100
    frames_per_window = [100, 50, 100]  # Window 1 has 50% loss
    
    data = []
    current_time = datetime(2023, 1, 1, 0, 0, 0)
    
    for window_idx, frames in enumerate(frames_per_window):
        for i in range(frames):
            data.append({
                'particle_id': f'p{window_idx}',
                'timestamp': current_time + timedelta(seconds=i*0.01),
                'x': np.random.rand(),
                'y': np.random.rand(),
                'z': np.random.rand()
            })
        current_time += timedelta(seconds=window_size * 0.01 + 0.1)
    
    return pd.DataFrame(data)

def test_calculate_tracking_failure_rate_basic(sample_tracking_data):
    """Test basic functionality of tracking failure rate calculation."""
    flagged_df, summary = calculate_tracking_failure_rate(
        sample_tracking_data, 
        window_size=100,
        threshold=0.20
    )
    
    # Check that the dataframe has the 'excluded' column
    assert 'excluded' in flagged_df.columns
    assert 'window_id' in flagged_df.columns
    
    # Check summary statistics
    assert 'total_windows' in summary
    assert 'flagged_windows' in summary
    assert 'exclusion_threshold' in summary
    assert summary['exclusion_threshold'] == 0.20
    
    # Window 1 (20% loss) should NOT be flagged (threshold is > 20%)
    # Window 3 (30% loss) should be flagged
    assert summary['flagged_windows'] == 1
    assert 3 in summary['flagged_window_ids']

def test_calculate_tracking_failure_rate_high_threshold(incomplete_tracking_data):
    """Test with high threshold where no windows are flagged."""
    flagged_df, summary = calculate_tracking_failure_rate(
        incomplete_tracking_data, 
        window_size=100,
        threshold=0.60  # 60% threshold
    )
    
    assert summary['flagged_windows'] == 0
    assert len(summary['flagged_window_ids']) == 0

def test_calculate_tracking_failure_rate_low_threshold(incomplete_tracking_data):
    """Test with low threshold where multiple windows are flagged."""
    flagged_df, summary = calculate_tracking_failure_rate(
        incomplete_tracking_data, 
        window_size=100,
        threshold=0.10  # 10% threshold
    )
    
    # Window 1 has 50% loss, should be flagged
    assert summary['flagged_windows'] == 1
    assert 1 in summary['flagged_window_ids']

def test_calculate_tracking_failure_rate_missing_time_column():
    """Test error handling when time column is missing."""
    df = pd.DataFrame({
        'particle_id': ['p1', 'p2'],
        'x': [1.0, 2.0]
    })
    
    with pytest.raises(IngestionError) as exc_info:
        calculate_tracking_failure_rate(df, time_col='timestamp')
    
    assert "Time column 'timestamp' not found in DataFrame" in str(exc_info.value)

def test_calculate_tracking_failure_rate_output_structure(sample_tracking_data):
    """Test that the output structure matches expected format."""
    flagged_df, summary = calculate_tracking_failure_rate(
        sample_tracking_data, 
        window_size=100,
        threshold=0.20
    )
    
    # Verify summary keys
    required_keys = [
        'total_windows', 'flagged_windows', 'exclusion_threshold', 
        'window_size', 'avg_failure_rate', 'max_failure_rate', 'flagged_window_ids'
    ]
    for key in required_keys:
        assert key in summary, f"Missing key: {key}"
    
    # Verify data types
    assert isinstance(summary['total_windows'], int)
    assert isinstance(summary['flagged_windows'], int)
    assert isinstance(summary['exclusion_threshold'], float)
    assert isinstance(summary['flagged_window_ids'], list)

def test_calculate_tracking_failure_rate_window_assignment(sample_tracking_data):
    """Test that frames are correctly assigned to windows."""
    flagged_df, summary = calculate_tracking_failure_rate(
        sample_tracking_data, 
        window_size=100,
        threshold=0.20
    )
    
    # Check that window_id is assigned correctly
    window_ids = flagged_df['window_id'].unique()
    assert len(window_ids) == 5  # 5 windows in the sample data
    assert all(isinstance(wid, (int, np.integer)) for wid in window_ids)

def test_calculate_tracking_failure_rate_exclusion_flag(sample_tracking_data):
    """Test that the exclusion flag is correctly set based on failure rate."""
    flagged_df, summary = calculate_tracking_failure_rate(
        sample_tracking_data, 
        window_size=100,
        threshold=0.20
    )
    
    # Check that excluded column is boolean
    assert flagged_df['excluded'].dtype == bool
    
    # Check that flagged windows have excluded=True
    flagged_ids = summary['flagged_window_ids']
    if flagged_ids:
        for wid in flagged_ids:
            window_data = flagged_df[flagged_df['window_id'] == wid]
            assert all(window_data['excluded'] == True)
    
    # Check that non-flagged windows have excluded=False
    non_flagged_ids = [i for i in range(5) if i not in flagged_ids]
    for wid in non_flagged_ids:
        window_data = flagged_df[flagged_df['window_id'] == wid]
        if len(window_data) > 0:
            assert all(window_data['excluded'] == False)
