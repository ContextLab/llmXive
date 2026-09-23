"""
Unit tests for T012a: Age Exclusion logic.
"""
import pytest
import pandas as pd
import json
import os
import tempfile
from pathlib import Path
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from task_t012a_age_exclusion import filter_by_age, save_exclusion_count, load_raw_dataset

def test_filter_by_age_basic():
    """Test basic age filtering."""
    data = {
        'participant_id': [1, 2, 3, 4],
        'age': [60, 65, 70, 80],
        'score': [10, 20, 30, 40]
    }
    df = pd.DataFrame(data)
    
    filtered_df, excluded_count = filter_by_age(df, min_age=65)
    
    assert len(filtered_df) == 3
    assert excluded_count == 1
    assert all(filtered_df['age'] >= 65)
    assert list(filtered_df['participant_id']) == [2, 3, 4]

def test_filter_by_age_all_excluded():
    """Test case where all records are excluded."""
    data = {
        'participant_id': [1, 2],
        'age': [20, 30],
        'score': [10, 20]
    }
    df = pd.DataFrame(data)
    
    filtered_df, excluded_count = filter_by_age(df, min_age=65)
    
    assert len(filtered_df) == 0
    assert excluded_count == 2

def test_filter_by_age_no_excluded():
    """Test case where no records are excluded."""
    data = {
        'participant_id': [1, 2],
        'age': [70, 80],
        'score': [10, 20]
    }
    df = pd.DataFrame(data)
    
    filtered_df, excluded_count = filter_by_age(df, min_age=65)
    
    assert len(filtered_df) == 2
    assert excluded_count == 0

def test_filter_by_age_missing_column():
    """Test error handling when 'age' column is missing."""
    data = {
        'participant_id': [1, 2],
        'years': [70, 80]
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(KeyError, match="Column 'age' not found"):
        filter_by_age(df, min_age=65)

def test_save_exclusion_count_update():
    """Test updating existing exclusion counts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "exclusion_counts.json"
        
        # Create initial file
        initial_data = {"ERR_OTHER": 5}
        with open(path, 'w') as f:
            json.dump(initial_data, f)
        
        # Update
        save_exclusion_count(10, path)
        
        # Verify
        with open(path, 'r') as f:
            result = json.load(f)
        
        assert result["ERR_OTHER"] == 5
        assert result["ERR_MISSING_AGE_FIELD"] == 10
