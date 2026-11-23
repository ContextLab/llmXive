import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from preprocess import (
    extract_fixations_ivt,
    map_stimulus_valence,
    filter_trials,
    calculate_ivt_threshold,
    validate_against_schema
)

def test_ivt_fixation_extraction():
    """Test that I-VT algorithm correctly extracts fixations with duration > 100ms."""
    # Create synthetic gaze data with a clear fixation
    # Sampling rate 1000Hz -> 1ms per frame
    # Fixation at (100, 100) for 200 frames (200ms)
    timestamps = np.arange(0, 300, 1)
    x = np.concatenate([np.random.normal(100, 5, 50), np.ones(200)*100, np.random.normal(200, 5, 50)])
    y = np.concatenate([np.random.normal(100, 5, 50), np.ones(200)*100, np.random.normal(200, 5, 50)])
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'x': x,
        'y': y
    })
    
    # Threshold: 30 deg/s. At 1000Hz, 55deg FOV, 1920px -> ~35px/s -> 0.035 px/ms
    # Let's use a very low threshold to catch the fixation, and high to catch saccades
    # Actually, let's just use a standard threshold
    threshold = 0.1 # px/ms equivalent for this test
    
    fixations = extract_fixations_ivt(df, threshold, min_duration_ms=100.0)
    
    assert len(fixations) > 0, "No fixations found"
    
    # Check if we found the 200ms fixation
    found_long_fixation = False
    for _, row in fixations.iterrows():
        if row['duration'] >= 100:
            found_long_fixation = True
            # Check mean position is around 100
            assert abs(row['mean_x'] - 100) < 10, f"Mean X {row['mean_x']} far from 100"
            assert abs(row['mean_y'] - 100) < 10, f"Mean Y {row['mean_y']} far from 100"
            break
    
    assert found_long_fixation, "Did not find the expected 200ms fixation"

def test_stimulus_valence_mapping():
    """Test that unmapped IDs raise KeyError or are handled."""
    df = pd.DataFrame({
        'stimulus_id': [1, 2, 3, 999],
        'other_col': ['a', 'b', 'c', 'd']
    })
    
    valence_map = {1: 1, 2: -1, 3: 0}
    
    # This should drop 999
    result = map_stimulus_valence(df, valence_map)
    
    assert len(result) == 3, "Unmapped ID should be dropped"
    assert 999 not in result['stimulus_id'].values, "Unmapped ID still present"
    assert 'valence' in result.columns, "Valence column missing"

def test_filter_trials():
    """Test trial filtering logic."""
    df = pd.DataFrame({
        'missing_frames_pct': [0.1, 0.6, 0.2],
        'blink_duration': [50.0, 20.0, 600.0]
    })
    
    filtered = filter_trials(df, max_missing_pct=0.5, max_blink_duration=500.0)
    
    assert len(filtered) == 1, "Should filter out 2 rows"
    assert filtered.iloc[0]['missing_frames_pct'] == 0.1
    assert filtered.iloc[0]['blink_duration'] == 50.0

def test_calculate_ivt_threshold():
    """Test I-VT threshold calculation."""
    geometry = {
        'screen_width_px': 1920,
        'viewing_distance_cm': 60,
        'sampling_rate_hz': 1000
    }
    threshold = calculate_ivt_threshold(geometry, deg_per_sec=30)
    assert threshold > 0, "Threshold must be positive"
    assert threshold < 100, "Threshold seems unreasonably high"

def test_validate_against_schema():
    """Test schema validation."""
    df = pd.DataFrame({
        'participant_id': ['1', '2'],
        'duration': [100.0, 200.0],
        'valence': [1, -1],
        'STAI': [30, 40],
        'start_time': [0, 100],
        'end_time': [100, 200],
        'mean_x': [10, 20],
        'mean_y': [10, 20]
    })
    
    schema = {
        'required': ['participant_id', 'duration', 'valence', 'STAI', 'start_time', 'end_time', 'mean_x', 'mean_y'],
        'properties': {}
    }
    
    assert validate_against_schema(df, schema) is True
    
    # Test missing column
    bad_df = df.drop(columns=['duration'])
    with pytest.raises(ValueError):
        validate_against_schema(bad_df, schema)