"""
Unit tests for code/filter_analysis_subset.py.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the function under test
# We need to mock the load_aligned_events and write_aligned_events if we can't run full IO
# But for unit tests of the logic, we can pass a DataFrame directly.
from filter_analysis_subset import filter_non_recurrent_storms

def test_filter_non_recurrent_storms_basic():
    """Test that True values are removed, False and NaN are kept."""
    data = {
        'event_id': [1, 2, 3, 4, 5],
        'is_recurrent': [False, True, False, True, np.nan]
    }
    df = pd.DataFrame(data)
    
    result = filter_non_recurrent_storms(df)
    
    # Expected: rows 1, 3, 5 (indices 0, 2, 4)
    expected_ids = [1, 3, 5]
    assert list(result['event_id']) == expected_ids
    assert len(result) == 3

def test_filter_non_recurrent_storms_all_recurrent():
    """Test behavior when all events are recurrent."""
    data = {
        'event_id': [1, 2],
        'is_recurrent': [True, True]
    }
    df = pd.DataFrame(data)
    
    result = filter_non_recurrent_storms(df)
    
    assert len(result) == 0

def test_filter_non_recurrent_storms_none_recurrent():
    """Test behavior when no events are recurrent."""
    data = {
        'event_id': [1, 2, 3],
        'is_recurrent': [False, False, False]
    }
    df = pd.DataFrame(data)
    
    result = filter_non_recurrent_storms(df)
    
    assert len(result) == 3
    assert list(result['event_id']) == [1, 2, 3]

def test_filter_non_recurrent_storms_missing_column():
    """Test behavior when 'is_recurrent' column is missing."""
    data = {
        'event_id': [1, 2, 3],
        'other_col': ['a', 'b', 'c']
    }
    df = pd.DataFrame(data)
    
    # Should not raise, should return a copy of the original
    result = filter_non_recurrent_storms(df)
    
    assert len(result) == 3
    assert list(result['event_id']) == [1, 2, 3]

def test_filter_non_recurrent_storms_empty_df():
    """Test behavior on empty DataFrame."""
    df = pd.DataFrame(columns=['event_id', 'is_recurrent'])
    
    result = filter_non_recurrent_storms(df)
    
    assert len(result) == 0
