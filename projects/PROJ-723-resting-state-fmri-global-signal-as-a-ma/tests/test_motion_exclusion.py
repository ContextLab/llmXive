import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingestion import apply_motion_exclusion, run_motion_exclusion_pipeline

def test_motion_exclusion_basic():
    """Test basic motion exclusion logic."""
    data = {
        'Subject_ID': ['S1', 'S2', 'S3', 'S4'],
        'Mean_FD': [0.2, 0.6, 0.4, 0.8]
    }
    df = pd.DataFrame(data)
    
    filtered_df, exclusion_log = apply_motion_exclusion(df, threshold=0.5)
    
    assert len(filtered_df) == 2
    assert set(filtered_df['Subject_ID'].tolist()) == {'S1', 'S3'}
    assert len(exclusion_log) == 2
    assert set([e['subject_id'] for e in exclusion_log]) == {'S2', 'S4'}

def test_motion_exclusion_no_exclusions():
    """Test case where no subjects are excluded."""
    data = {
        'Subject_ID': ['S1', 'S2'],
        'Mean_FD': [0.1, 0.2]
    }
    df = pd.DataFrame(data)
    
    filtered_df, exclusion_log = apply_motion_exclusion(df, threshold=0.5)
    
    assert len(filtered_df) == 2
    assert len(exclusion_log) == 0

def test_motion_exclusion_all_excluded():
    """Test case where all subjects are excluded."""
    data = {
        'Subject_ID': ['S1', 'S2'],
        'Mean_FD': [0.6, 0.7]
    }
    df = pd.DataFrame(data)
    
    filtered_df, exclusion_log = apply_motion_exclusion(df, threshold=0.5)
    
    assert len(filtered_df) == 0
    assert len(exclusion_log) == 2

def test_motion_exclusion_missing_column():
    """Test error handling for missing columns."""
    data = {
        'Subject_ID': ['S1'],
        'Other': [0.1]
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(ValueError):
        apply_motion_exclusion(df, threshold=0.5)
    
    data2 = {
        'Mean_FD': [0.1],
        'Other': ['S1']
    }
    df2 = pd.DataFrame(data2)
    
    with pytest.raises(ValueError):
        apply_motion_exclusion(df2, threshold=0.5)

def test_motion_exclusion_pipeline_wrapper():
    """Test the pipeline wrapper function."""
    data = {
        'Subject_ID': ['S1', 'S2', 'S3'],
        'Mean_FD': [0.1, 0.6, 0.3]
    }
    df = pd.DataFrame(data)
    
    filtered_df, exclusion_log = run_motion_exclusion_pipeline(df, threshold=0.5)
    
    assert len(filtered_df) == 2
    assert len(exclusion_log) == 1
    assert exclusion_log[0]['subject_id'] == 'S2'