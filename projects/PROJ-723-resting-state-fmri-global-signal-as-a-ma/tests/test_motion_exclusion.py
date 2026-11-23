"""
Tests for T014: Motion Exclusion Logic.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion import apply_motion_exclusion

def test_motion_exclusion_basic():
    """Test that subjects with Mean_FD > 0.5 are excluded."""
    data = {
        'Subject_ID': ['S1', 'S2', 'S3', 'S4'],
        'Mean_FD': [0.2, 0.4, 0.6, 0.8],
        'Other_Column': [1, 2, 3, 4]
    }
    df = pd.DataFrame(data)
    
    filtered_df, excluded_ids = apply_motion_exclusion(df, threshold=0.5)
    
    # S1, S2 should remain; S3, S4 should be excluded
    assert len(filtered_df) == 2
    assert list(filtered_df['Subject_ID']) == ['S1', 'S2']
    assert set(excluded_ids) == {'S3', 'S4'}

def test_motion_exclusion_all_pass():
    """Test when all subjects pass the threshold."""
    data = {
        'Subject_ID': ['S1', 'S2'],
        'Mean_FD': [0.1, 0.4],
        'Other_Column': [1, 2]
    }
    df = pd.DataFrame(data)
    
    filtered_df, excluded_ids = apply_motion_exclusion(df, threshold=0.5)
    
    assert len(filtered_df) == 2
    assert len(excluded_ids) == 0

def test_motion_exclusion_all_fail():
    """Test when all subjects fail the threshold."""
    data = {
        'Subject_ID': ['S1', 'S2'],
        'Mean_FD': [0.6, 0.8],
        'Other_Column': [1, 2]
    }
    df = pd.DataFrame(data)
    
    filtered_df, excluded_ids = apply_motion_exclusion(df, threshold=0.5)
    
    assert len(filtered_df) == 0
    assert set(excluded_ids) == {'S1', 'S2'}

def test_motion_exclusion_boundary():
    """Test exact boundary condition (0.5)."""
    # 0.5 is NOT > 0.5, so it should pass
    data = {
        'Subject_ID': ['S1', 'S2'],
        'Mean_FD': [0.5, 0.5001],
        'Other_Column': [1, 2]
    }
    df = pd.DataFrame(data)
    
    filtered_df, excluded_ids = apply_motion_exclusion(df, threshold=0.5)
    
    # S1 (0.5) passes, S2 (0.5001) fails
    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]['Subject_ID'] == 'S1'
    assert excluded_ids == ['S2']

def test_missing_columns():
    """Test that missing columns raise an error."""
    data = {'Subject_ID': ['S1'], 'Mean_FD': [0.1]}
    df = pd.DataFrame(data)
    
    # Test missing Mean_FD
    df_missing_fd = df.drop(columns=['Mean_FD'])
    with pytest.raises(ValueError):
        apply_motion_exclusion(df_missing_fd)
    
    # Test missing Subject_ID
    df_missing_id = df.drop(columns=['Subject_ID'])
    with pytest.raises(ValueError):
        apply_motion_exclusion(df_missing_id)
