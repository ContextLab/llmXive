"""
Unit tests for T012a: Age Exclusion Filter
"""
import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))
from task_t012a_age_exclusion import filter_by_age, save_exclusion_count, load_raw_dataset

def test_filter_by_age_valid():
    """Test filtering with valid age data."""
    data = {
        'participant_id': ['P1', 'P2', 'P3', 'P4'],
        'age': [60, 65, 70, 80],
        'stimulus_type': ['nostalgia', 'control', 'nostalgia', 'control']
    }
    df = pd.DataFrame(data)
    
    filtered_df, count = filter_by_age(df, min_age=65)
    
    assert len(filtered_df) == 3
    assert count == 1
    assert all(filtered_df['age'] >= 65)
    assert 'P1' not in filtered_df['participant_id'].values

def test_filter_by_age_all_excluded():
    """Test filtering when all records are excluded."""
    data = {
        'participant_id': ['P1', 'P2'],
        'age': [20, 30],
        'stimulus_type': ['nostalgia', 'control']
    }
    df = pd.DataFrame(data)
    
    filtered_df, count = filter_by_age(df, min_age=65)
    
    assert len(filtered_df) == 0
    assert count == 2

def test_filter_by_age_all_included():
    """Test filtering when all records are included."""
    data = {
        'participant_id': ['P1', 'P2', 'P3'],
        'age': [65, 70, 80],
        'stimulus_type': ['nostalgia', 'control', 'nostalgia']
    }
    df = pd.DataFrame(data)
    
    filtered_df, count = filter_by_age(df, min_age=65)
    
    assert len(filtered_df) == 3
    assert count == 0

def test_filter_by_age_missing_column():
    """Test filtering when 'age' column is missing."""
    data = {
        'participant_id': ['P1', 'P2'],
        'stimulus_type': ['nostalgia', 'control']
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(ValueError, match="ERR_MISSING_AGE_FIELD"):
        filter_by_age(df, min_age=65)

def test_save_exclusion_count_creates_file():
    """Test that save_exclusion_count creates a new file if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "exclusion_counts.json")
        
        save_exclusion_count("TEST_KEY", 5, output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert data["TEST_KEY"] == 5

def test_save_exclusion_count_updates_existing():
    """Test that save_exclusion_count updates an existing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "exclusion_counts.json")
        
        # Create initial file
        with open(output_path, 'w') as f:
            json.dump({"EXISTING_KEY": 10}, f)
        
        save_exclusion_count("NEW_KEY", 5, output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert data["EXISTING_KEY"] == 10
        assert data["NEW_KEY"] == 5