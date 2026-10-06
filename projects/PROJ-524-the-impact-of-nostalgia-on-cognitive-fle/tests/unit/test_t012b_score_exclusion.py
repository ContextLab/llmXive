"""
Unit tests for Task T012b: Score Exclusion
"""
import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Import the module functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from task_t012b_score_exclusion import (
    filter_by_score,
    update_exclusion_counts
)

def test_filter_by_score_all_valid():
    """Test filtering when all records have valid scores."""
    data = {
        'participant_id': [1, 2, 3],
        'age': [65, 70, 75],
        'stimulus_type': ['nostalgia', 'control', 'nostalgia'],
        'perseverative_errors': [5.0, 3.0, 4.0],
        'categories_completed': [4.0, 5.0, 3.0]
    }
    df = pd.DataFrame(data)
    
    filtered_df, excluded_count = filter_by_score(df)
    
    assert len(filtered_df) == 3
    assert excluded_count == 0
    assert 'perseverative_errors' in filtered_df.columns
    assert 'categories_completed' in filtered_df.columns

def test_filter_by_score_some_invalid():
    """Test filtering when some records have missing scores."""
    data = {
        'participant_id': [1, 2, 3, 4],
        'age': [65, 70, 75, 80],
        'stimulus_type': ['nostalgia', 'control', 'nostalgia', 'control'],
        'perseverative_errors': [5.0, None, 4.0, 2.0],
        'categories_completed': [4.0, 5.0, None, 3.0]
    }
    df = pd.DataFrame(data)
    
    filtered_df, excluded_count = filter_by_score(df)
    
    # Only row 0 and 3 are valid (both columns non-null)
    assert len(filtered_df) == 2
    assert excluded_count == 2
    assert list(filtered_df['participant_id']) == [1, 4]

def test_filter_by_score_all_invalid():
    """Test filtering when all records have missing scores."""
    data = {
        'participant_id': [1, 2],
        'age': [65, 70],
        'stimulus_type': ['nostalgia', 'control'],
        'perseverative_errors': [None, None],
        'categories_completed': [None, None]
    }
    df = pd.DataFrame(data)
    
    filtered_df, excluded_count = filter_by_score(df)
    
    assert len(filtered_df) == 0
    assert excluded_count == 2

def test_update_exclusion_counts_new_file(tmp_path):
    """Test updating exclusion counts when the file does not exist."""
    counts_file = tmp_path / "exclusion_counts.json"
    update_exclusion_counts(5, counts_file)
    
    assert counts_file.exists()
    with open(counts_file, 'r') as f:
        counts = json.load(f)
    
    assert counts["ERR_MISSING_SCORE"] == 5

def test_update_exclusion_counts_existing_file(tmp_path):
    """Test updating exclusion counts when the file already exists."""
    counts_file = tmp_path / "exclusion_counts.json"
    
    # Create initial file
    initial_counts = {"ERR_MISSING_AGE_FIELD": 10}
    with open(counts_file, 'w') as f:
        json.dump(initial_counts, f)
    
    update_exclusion_counts(5, counts_file)
    
    with open(counts_file, 'r') as f:
        counts = json.load(f)
    
    assert counts["ERR_MISSING_AGE_FIELD"] == 10
    assert counts["ERR_MISSING_SCORE"] == 5