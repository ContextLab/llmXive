"""
Unit tests for filter_descriptors module (T015).
"""
import pandas as pd
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from filter_descriptors import load_descriptors, count_missing_values, filter_entries, save_filtered_data

def test_count_missing_values():
    """Test counting missing values per row."""
    data = {
        'formula': ['CsPbI3', 'MAPbI3', 'FAPbI3'],
        'T_d': [400, 350, 380],
        'feat1': [1.0, 2.0, None],
        'feat2': [None, None, 3.0],
        'feat3': [1.0, 2.0, 3.0]
    }
    df = pd.DataFrame(data)
    
    missing_counts = count_missing_values(df)
    
    # Expected: Row 0 has 1 missing (feat2), Row 1 has 2 missing (feat1, feat2), Row 2 has 1 missing (feat1)
    # Note: 'T_d' and 'formula' are excluded from count
    assert missing_counts.iloc[0] == 1
    assert missing_counts.iloc[1] == 2
    assert missing_counts.iloc[2] == 1

def test_filter_entries_exclude_two_missing():
    """Test that entries with >= 2 missing values are excluded."""
    data = {
        'formula': ['CsPbI3', 'MAPbI3', 'FAPbI3'],
        'T_d': [400, 350, 380],
        'feat1': [1.0, 2.0, None],
        'feat2': [None, None, 3.0],
        'feat3': [1.0, 2.0, 3.0]
    }
    df = pd.DataFrame(data)
    
    filtered_df, excluded_count = filter_entries(df, max_missing=1)
    
    # Row 1 (MAPbI3) has 2 missing values, should be excluded
    assert excluded_count == 1
    assert len(filtered_df) == 2
    assert 'MAPbI3' not in filtered_df['formula'].values
    
    # Verify remaining rows
    assert 'CsPbI3' in filtered_df['formula'].values
    assert 'FAPbI3' in filtered_df['formula'].values

def test_filter_entries_all_valid():
    """Test filtering when no entries are excluded."""
    data = {
        'formula': ['CsPbI3', 'MAPbI3'],
        'T_d': [400, 350],
        'feat1': [1.0, 2.0],
        'feat2': [3.0, 4.0],
        'feat3': [5.0, 6.0]
    }
    df = pd.DataFrame(data)
    
    filtered_df, excluded_count = filter_entries(df, max_missing=1)
    
    assert excluded_count == 0
    assert len(filtered_df) == 2

def test_filter_entries_all_excluded():
    """Test filtering when all entries have too many missing values."""
    data = {
        'formula': ['CsPbI3', 'MAPbI3'],
        'T_d': [400, 350],
        'feat1': [None, None],
        'feat2': [None, None],
        'feat3': [None, None]
    }
    df = pd.DataFrame(data)
    
    filtered_df, excluded_count = filter_entries(df, max_missing=1)
    
    assert excluded_count == 2
    assert len(filtered_df) == 0
    assert filtered_df.empty