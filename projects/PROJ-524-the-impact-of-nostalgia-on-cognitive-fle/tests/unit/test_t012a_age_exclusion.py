"""
Unit tests for T012a: Age Exclusion Logic
"""
import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# We need to mock the config to point to temporary directories
# Since we are testing the logic, we will import the functions directly
# and mock the file system interactions.

# Add code directory to path if running standalone
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from task_t012a_age_exclusion import filter_by_age, save_exclusion_count

@pytest.fixture
def sample_data():
    return pd.DataFrame({
        'participant_id': [1, 2, 3, 4, 5, 6],
        'age': [60, 65, 70, 75, 80, None],
        'stimulus_type': ['control', 'nostalgia', 'control', 'nostalgia', 'control', 'nostalgia'],
        'perseverative_errors': [10, 5, 8, 4, 9, 6],
        'categories_completed': [4, 6, 5, 7, 4, 5]
    })

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

def test_filter_by_age_valid(sample_data):
    """Test filtering keeps only age >= 65"""
    filtered, excluded = filter_by_age(sample_data, min_age=65)
    
    assert len(filtered) == 4 # IDs 2, 3, 4, 5 (ID 6 is None, ID 1 is 60)
    assert excluded == 2 # ID 1 (60) and ID 6 (None)
    assert all(filtered['age'] >= 65)
    assert 'age' not in filtered[filtered['age'] < 65].index

def test_filter_by_age_missing_values(sample_data):
    """Test that missing age values are excluded"""
    filtered, excluded = filter_by_age(sample_data, min_age=65)
    
    # Check that no NaN ages are in the result
    assert not filtered['age'].isna().any()
    # Count of excluded should include the NaN
    assert excluded >= 1 

def test_filter_by_age_all_below_threshold():
    """Test behavior when all ages are below threshold"""
    df = pd.DataFrame({
        'participant_id': [1, 2],
        'age': [20, 30]
    })
    filtered, excluded = filter_by_age(df, min_age=65)
    
    assert len(filtered) == 0
    assert excluded == 2

def test_filter_by_age_all_valid():
    """Test behavior when all ages are valid"""
    df = pd.DataFrame({
        'participant_id': [1, 2],
        'age': [70, 80]
    })
    filtered, excluded = filter_by_age(df, min_age=65)
    
    assert len(filtered) == 2
    assert excluded == 0

def test_save_exclusion_count(temp_dir):
    """Test saving exclusion counts to JSON"""
    paths = {'processed': temp_dir}
    count = 15
    
    # Create parent if needed (though temp_dir exists)
    output_path = paths['processed'] / 'exclusion_counts.json'
    
    save_exclusion_count(count, paths)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert 'ERR_MISSING_AGE_FIELD' in data
    assert data['ERR_MISSING_AGE_FIELD'] == 15

def test_save_exclusion_count_updates_existing(temp_dir):
    """Test that saving updates existing JSON without losing other keys"""
    paths = {'processed': temp_dir}
    output_path = paths['processed'] / 'exclusion_counts.json'
    
    # Pre-populate file
    with open(output_path, 'w') as f:
        json.dump({'ERR_OTHER': 10}, f)
    
    save_exclusion_count(20, paths)
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data['ERR_OTHER'] == 10
    assert data['ERR_MISSING_AGE_FIELD'] == 20
