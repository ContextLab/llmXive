import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Mock the utils and config if needed, or assume they are installed
# For this test, we assume ingestion.py is importable and contains the function
from ingestion import apply_motion_exclusion

def test_apply_motion_exclusion_basic():
    """Test that subjects with Mean_FD > 0.5 are excluded."""
    data = {
        'Subject_ID': ['sub-01', 'sub-02', 'sub-03', 'sub-04'],
        'Mean_FD': [0.2, 0.6, 0.4, 0.8],
        'Other_Col': [1, 2, 3, 4]
    }
    df = pd.DataFrame(data)
    
    logger = logging.getLogger("test")
    filtered_df, log_info = apply_motion_exclusion(df, threshold=0.5, logger=logger)
    
    assert len(filtered_df) == 2
    assert set(filtered_df['Subject_ID']) == {'sub-01', 'sub-03'}
    assert log_info['excluded_count'] == 2
    assert set(log_info['excluded_ids']) == {'sub-02', 'sub-04'}

def test_apply_motion_exclusion_all_pass():
    """Test that no subjects are excluded if all are below threshold."""
    data = {
        'Subject_ID': ['sub-01', 'sub-02'],
        'Mean_FD': [0.1, 0.4],
        'Other_Col': [1, 2]
    }
    df = pd.DataFrame(data)
    
    logger = logging.getLogger("test")
    filtered_df, log_info = apply_motion_exclusion(df, threshold=0.5, logger=logger)
    
    assert len(filtered_df) == 2
    assert log_info['excluded_count'] == 0
    assert log_info['excluded_ids'] == []

def test_apply_motion_exclusion_all_fail():
    """Test that all subjects are excluded if all are above threshold."""
    data = {
        'Subject_ID': ['sub-01', 'sub-02'],
        'Mean_FD': [0.6, 0.9],
        'Other_Col': [1, 2]
    }
    df = pd.DataFrame(data)
    
    logger = logging.getLogger("test")
    filtered_df, log_info = apply_motion_exclusion(df, threshold=0.5, logger=logger)
    
    assert len(filtered_df) == 0
    assert log_info['excluded_count'] == 2
    assert set(log_info['excluded_ids']) == {'sub-01', 'sub-02'}

def test_apply_motion_exclusion_missing_column():
    """Test that ValueError is raised if Mean_FD is missing."""
    data = {
        'Subject_ID': ['sub-01'],
        'Other_Col': [1]
    }
    df = pd.DataFrame(data)
    
    logger = logging.getLogger("test")
    with pytest.raises(ValueError, match="Mean_FD"):
        apply_motion_exclusion(df, threshold=0.5, logger=logger)

def test_apply_motion_exclusion_missing_id_column():
    """Test that ValueError is raised if Subject_ID is missing."""
    data = {
        'Mean_FD': [0.6],
        'Other_Col': [1]
    }
    df = pd.DataFrame(data)
    
    logger = logging.getLogger("test")
    with pytest.raises(ValueError, match="Subject_ID"):
        apply_motion_exclusion(df, threshold=0.5, logger=logger)
