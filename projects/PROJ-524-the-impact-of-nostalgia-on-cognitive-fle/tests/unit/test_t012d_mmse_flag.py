import os
import json
import pytest
import pandas as pd
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from task_t012d_mmse_flag import load_score_filtered_dataset, validate_mmse_presence, save_mmse_flag, main

# Test Fixtures
@pytest.fixture
def temp_processed_dir(tmp_path):
    """Creates a temporary processed directory structure."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    return processed_dir

@pytest.fixture
def score_filtered_file(temp_processed_dir):
    """Creates a mock cleaned_score_filtered.csv file."""
    file_path = temp_processed_dir / "cleaned_score_filtered.csv"
    data = {
        'participant_id': [1, 2, 3, 4],
        'stimulus_type': ['nostalgia', 'control', 'nostalgia', 'control'],
        'perseverative_errors': [5, 3, 6, 2],
        'categories_completed': [4, 5, 3, 6],
        'age': [68, 72, 65, 80],
        'MMSE': [28, 29, None, 26] # One null, rest valid
    }
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    return file_path

@pytest.fixture
def score_filtered_no_mmse_col(temp_processed_dir):
    """Creates a mock file without the MMSE column."""
    file_path = temp_processed_dir / "cleaned_score_filtered.csv"
    data = {
        'participant_id': [1, 2],
        'stimulus_type': ['nostalgia', 'control'],
        'perseverative_errors': [5, 3],
        'categories_completed': [4, 5],
        'age': [68, 72]
    }
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    return file_path

@pytest.fixture
def score_filtered_all_null_mmse(temp_processed_dir):
    """Creates a mock file with MMSE column but all nulls."""
    file_path = temp_processed_dir / "cleaned_score_filtered.csv"
    data = {
        'participant_id': [1, 2],
        'stimulus_type': ['nostalgia', 'control'],
        'perseverative_errors': [5, 3],
        'categories_completed': [4, 5],
        'age': [68, 72],
        'MMSE': [None, None]
    }
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    return file_path

def test_validate_mmse_presence_present_and_valid(score_filtered_file, temp_processed_dir):
    """Test that validation returns True when MMSE column exists and has values."""
    # Temporarily patch the path constant to use temp dir
    import task_t012d_mmse_flag as module
    original_path = module.SCORE_FILTERED_PATH
    module.SCORE_FILTERED_PATH = score_filtered_file
    
    try:
        df = load_score_filtered_dataset()
        result = validate_mmse_presence(df)
        assert result is True
    finally:
        module.SCORE_FILTERED_PATH = original_path

def test_validate_mmse_presence_missing_column(score_filtered_no_mmse_col, temp_processed_dir):
    """Test that validation returns False when MMSE column is missing."""
    import task_t012d_mmse_flag as module
    original_path = module.SCORE_FILTERED_PATH
    module.SCORE_FILTERED_PATH = score_filtered_no_mmse_col
    
    try:
        df = load_score_filtered_dataset()
        result = validate_mmse_presence(df)
        assert result is False
    finally:
        module.SCORE_FILTERED_PATH = original_path

def test_validate_mmse_presence_all_null(score_filtered_all_null_mmse, temp_processed_dir):
    """Test that validation returns False when MMSE column exists but is all null."""
    import task_t012d_mmse_flag as module
    original_path = module.SCORE_FILTERED_PATH
    module.SCORE_FILTERED_PATH = score_filtered_all_null_mmse
    
    try:
        df = load_score_filtered_dataset()
        result = validate_mmse_presence(df)
        assert result is False
    finally:
        module.SCORE_FILTERED_PATH = original_path

def test_save_mmse_flag_creates_file(temp_processed_dir):
    """Test that save_mmse_flag writes a valid JSON file."""
    import task_t012d_mmse_flag as module
    flag_path = temp_processed_dir / "mmse_flag.json"
    module.MMSE_FLAG_PATH = flag_path
    
    try:
        save_mmse_flag(True)
        
        assert flag_path.exists()
        with open(flag_path, 'r') as f:
            data = json.load(f)
        
        assert data['has_mmse'] is True
        assert 'timestamp' in data
    finally:
        module.MMSE_FLAG_PATH = Path("data/processed/mmse_flag.json")

def test_main_integration_success(temp_processed_dir, score_filtered_file, monkeypatch):
    """Integration test: Run main() and verify output file is created."""
    import task_t012d_mmse_flag as module
    
    # Patch paths to use temp directory
    module.SCORE_FILTERED_PATH = score_filtered_file
    flag_output = temp_processed_dir / "mmse_flag.json"
    module.MMSE_FLAG_PATH = flag_output
    
    # Run main
    result = module.main()
    
    assert result == 0
    assert flag_output.exists()
    
    with open(flag_output, 'r') as f:
        data = json.load(f)
    
    assert data['has_mmse'] is True