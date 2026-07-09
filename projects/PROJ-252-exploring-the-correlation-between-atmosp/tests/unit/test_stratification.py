import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis import stratify_control_windows

def test_stratify_control_windows_basic():
    """Test that stratify_control_windows correctly assigns strata based on month/day."""
    # Create a mock dataset
    data = {
        'timestamp': [
            '2018-01-15', '2018-02-20', '2019-01-15', '2019-02-20', 
            '2020-01-15', '2020-02-20'
        ],
        'is_event': [1, 1, 0, 0, 0, 0],  # First two are events, rest are controls
        'pressure_anomaly': [0.5, -0.3, 0.1, -0.1, 0.2, -0.2]
    }
    df = pd.DataFrame(data)
    
    result = stratify_control_windows(df)
    
    # Check that stratum column exists
    assert 'stratum' in result.columns
    assert 'data_verification_status' in result.columns
    
    # Check that event rows have stratum starting with 'event_'
    event_rows = result[result['is_event'] == 1]
    assert all(event_rows['stratum'].str.startswith('event_'))
    
    # Check that control rows have stratum starting with 'control_'
    control_rows = result[result['is_event'] == 0]
    assert all(control_rows['stratum'].str.startswith('control_'))
    
    # Check that data_verification_status is 'unverified'
    assert all(result['data_verification_status'] == 'unverified')

def test_stratify_control_windows_date_matching():
    """Test that controls are matched by month/day."""
    data = {
        'timestamp': [
            '2018-03-10', '2019-03-10', '2020-03-10', '2021-03-11'
        ],
        'is_event': [1, 0, 0, 0],
        'pressure_anomaly': [0.5, 0.1, 0.2, 0.3]
    }
    df = pd.DataFrame(data)
    
    result = stratify_control_windows(df)
    
    # The control on 2019-03-10 and 2020-03-10 should have the same month_day
    # and thus be in the same stratum group conceptually
    march_10_controls = result[result['timestamp'].str.contains('03-10')]
    assert len(march_10_controls) == 3  # 1 event + 2 controls
    
    # Check stratum format
    assert 'stratum' in result.columns

def test_stratify_control_windows_empty_dataset():
    """Test behavior with an empty dataset."""
    df = pd.DataFrame(columns=['timestamp', 'is_event', 'pressure_anomaly'])
    result = stratify_control_windows(df)
    
    assert 'stratum' in result.columns
    assert 'data_verification_status' in result.columns