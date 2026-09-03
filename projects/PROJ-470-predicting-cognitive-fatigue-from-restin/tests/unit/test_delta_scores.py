import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis import calculate_delta_scores

def test_calculate_delta_scores_fatigue_only():
    """
    Test T019: Delta calculation for fatigue (Post - Pre).
    This test uses a mock dataset where complexity metrics are single-session
    (no pre/post complexity), so complexity_delta will be NaN, but fatigue_delta
    should be calculated correctly.
    """
    # Mock metrics data (single session)
    metrics_data = {
        'participant_id': ['P01', 'P01', 'P02', 'P02'],
        'channel': ['Fz', 'Cz', 'Fz', 'Cz'],
        'metric_type': ['LZC', 'LZC', 'LZC', 'LZC'],
        'value': [0.8, 0.75, 0.9, 0.85]
    }
    metrics_df = pd.DataFrame(metrics_data)
    
    # Mock fatigue data with pre/post ratings
    fatigue_data = {
        'participant_id': ['P01', 'P02'],
        'pre_fatigue_rating': [2.0, 3.0],
        'post_fatigue_rating': [5.0, 4.5]
    }
    fatigue_df = pd.DataFrame(fatigue_data)
    
    # Calculate deltas
    delta_df = calculate_delta_scores(metrics_df, fatigue_df)
    
    # Assert output exists
    assert not delta_df.empty, "Delta dataframe should not be empty"
    
    # Assert fatigue_delta is calculated correctly
    # P01: 5.0 - 2.0 = 3.0
    # P02: 4.5 - 3.0 = 1.5
    assert 'fatigue_delta' in delta_df.columns
    
    p01_delta = delta_df[delta_df['participant_id'] == 'P01']['fatigue_delta'].values[0]
    p02_delta = delta_df[delta_df['participant_id'] == 'P02']['fatigue_delta'].values[0]
    
    assert np.isclose(p01_delta, 3.0), f"P01 fatigue delta should be 3.0, got {p01_delta}"
    assert np.isclose(p02_delta, 1.5), f"P02 fatigue delta should be 1.5, got {p02_delta}"
    
    # Assert complexity_delta is NaN (since no session column)
    assert np.isnan(delta_df['complexity_delta'].values[0]), "Complexity delta should be NaN for single-session data"

def test_calculate_delta_scores_pre_post_complexity():
    """
    Test T019: Delta calculation when pre/post complexity data is available.
    """
    # Mock metrics data with session column
    metrics_data = {
        'participant_id': ['P01', 'P01', 'P02', 'P02'],
        'session': ['pre', 'post', 'pre', 'post'],
        'channel': ['Fz', 'Fz', 'Fz', 'Fz'],
        'metric_type': ['LZC', 'LZC', 'LZC', 'LZC'],
        'value': [0.8, 0.9, 0.7, 0.85]
    }
    metrics_df = pd.DataFrame(metrics_data)
    
    # Mock fatigue data
    fatigue_data = {
        'participant_id': ['P01', 'P02'],
        'pre_fatigue_rating': [2.0, 3.0],
        'post_fatigue_rating': [5.0, 4.5]
    }
    fatigue_df = pd.DataFrame(fatigue_data)
    
    # Calculate deltas
    delta_df = calculate_delta_scores(metrics_df, fatigue_df)
    
    # Assert output exists
    assert not delta_df.empty, "Delta dataframe should not be empty"
    
    # Assert fatigue_delta
    assert 'fatigue_delta' in delta_df.columns
    
    # Assert complexity_delta
    assert 'complexity_delta' in delta_df.columns
    
    # P01: complexity 0.9 - 0.8 = 0.1
    p01_complexity_delta = delta_df[delta_df['participant_id'] == 'P01']['complexity_delta'].values[0]
    assert np.isclose(p01_complexity_delta, 0.1), f"P01 complexity delta should be 0.1, got {p01_complexity_delta}"

def test_delta_scores_file_creation():
    """
    Test that delta_scores.csv is created in the correct location.
    """
    import tempfile
    import shutil
    
    # Create a temporary directory for testing
    test_dir = Path(tempfile.mkdtemp())
    analysis_dir = test_dir / "data" / "analysis"
    analysis_dir.mkdir(parents=True)
    
    try:
        # Mock data
        metrics_data = {
            'participant_id': ['P01'],
            'channel': ['Fz'],
            'metric_type': ['LZC'],
            'value': [0.8]
        }
        metrics_df = pd.DataFrame(metrics_data)
        
        fatigue_data = {
            'participant_id': ['P01'],
            'pre_fatigue_rating': [2.0],
            'post_fatigue_rating': [5.0]
        }
        fatigue_df = pd.DataFrame(fatigue_data)
        
        # Calculate and save
        delta_df = calculate_delta_scores(metrics_df, fatigue_df)
        delta_file = analysis_dir / "delta_scores.csv"
        delta_df.to_csv(delta_file, index=False)
        
        # Verify file exists
        assert delta_file.exists(), "delta_scores.csv should be created"
        
        # Verify content
        saved_df = pd.read_csv(delta_file)
        assert 'fatigue_delta' in saved_df.columns
        assert saved_df['fatigue_delta'].iloc[0] == 3.0
        
    finally:
        shutil.rmtree(test_dir)