import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from task_t012a_age_exclusion import filter_by_age, load_raw_dataset, save_filtered_dataset, save_exclusion_count
from config import get_config

def test_filter_by_age_keeps_valid():
    """Test that filter_by_age keeps records >= 65 and excludes < 65"""
    data = {
        'participant_id': [1, 2, 3, 4],
        'age': [64, 65, 70, 80],
        'stimulus_type': ['A', 'B', 'A', 'B']
    }
    df = pd.DataFrame(data)
    
    filtered_df, excluded_count = filter_by_age(df, min_age=65)
    
    assert len(filtered_df) == 3
    assert excluded_count == 1
    assert all(filtered_df['age'] >= 65)
    assert 64 not in filtered_df['age'].values

def test_filter_by_age_missing_column():
    """Test that filter_by_age raises error if 'age' column is missing"""
    data = {
        'participant_id': [1, 2],
        'stimulus_type': ['A', 'B']
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(ValueError, match="Column 'age' not found"):
        filter_by_age(df)

def test_filter_by_age_all_excluded():
    """Test behavior when all records are below age threshold"""
    data = {
        'participant_id': [1, 2],
        'age': [20, 30]
    }
    df = pd.DataFrame(data)
    
    filtered_df, excluded_count = filter_by_age(df)
    
    assert len(filtered_df) == 0
    assert excluded_count == 2

def test_save_exclusion_count_updates_existing():
    """Test that save_exclusion_count correctly updates existing JSON"""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / 'exclusion_counts.json'
        
        # Create initial file
        initial_data = {'ERR_OTHER': 5}
        with open(path, 'w') as f:
            json.dump(initial_data, f)
        
        # Update with new count
        new_counts = {'ERR_MISSING_AGE_FIELD': 10}
        save_exclusion_count(new_counts, str(path))
        
        # Verify content
        with open(path, 'r') as f:
            result = json.load(f)
        
        assert result['ERR_OTHER'] == 5
        assert result['ERR_MISSING_AGE_FIELD'] == 10