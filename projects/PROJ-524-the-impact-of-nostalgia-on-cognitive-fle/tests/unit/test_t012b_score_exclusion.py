import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from task_t012b_score_exclusion import (
    load_age_filtered_dataset,
    filter_by_score,
    save_filtered_dataset,
    update_exclusion_counts
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_age_filtered_df():
    """Create a sample DataFrame simulating age-filtered data."""
    data = {
        'participant_id': [1, 2, 3, 4, 5, 6],
        'age': [65, 70, 75, 80, 85, 90],
        'stimulus_type': ['nostalgia', 'control', 'nostalgia', 'control', 'nostalgia', 'control'],
        'perseverative_errors': [5, 8, None, 10, 3, None],
        'categories_completed': [4, 3, 5, None, 6, 4],
        'MMSE': [28, 27, 29, 25, 30, 26]
    }
    return pd.DataFrame(data)

def test_load_age_filtered_dataset(temp_dir, sample_age_filtered_df):
    """Test loading a CSV file."""
    csv_path = Path(temp_dir) / 'test_input.csv'
    sample_age_filtered_df.to_csv(csv_path, index=False)
    
    loaded_df = load_age_filtered_dataset(str(csv_path))
    
    assert len(loaded_df) == len(sample_age_filtered_df)
    assert list(loaded_df.columns) == list(sample_age_filtered_df.columns)

def test_load_age_filtered_dataset_missing_file(temp_dir):
    """Test loading a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_age_filtered_dataset(str(Path(temp_dir) / 'nonexistent.csv'))

def test_filter_by_score_all_valid(sample_age_filtered_df):
    """Test filtering when all records have valid scores."""
    # Create a DataFrame with all valid scores
    data = sample_age_filtered_df.copy()
    data['perseverative_errors'] = [5, 8, 6, 10, 3, 4]
    data['categories_completed'] = [4, 3, 5, 7, 6, 4]
    
    filtered_df, excluded_count = filter_by_score(data)
    
    assert len(filtered_df) == len(data)
    assert excluded_count == 0

def test_filter_by_score_some_invalid(sample_age_filtered_df):
    """Test filtering when some records have missing scores."""
    filtered_df, excluded_count = filter_by_score(sample_age_filtered_df)
    
    # Expected: 4 valid records (indices 0, 1, 4, 5)
    # Excluded: 2 records (indices 2, 3)
    assert len(filtered_df) == 4
    assert excluded_count == 2
    
    # Verify no NaN values in score columns
    assert filtered_df['perseverative_errors'].notna().all()
    assert filtered_df['categories_completed'].notna().all()

def test_filter_by_score_missing_columns(sample_age_filtered_df):
    """Test filtering when required columns are missing."""
    # Remove a required column
    df = sample_age_filtered_df.drop(columns=['perseverative_errors'])
    
    with pytest.raises(ValueError, match="Missing required columns"):
        filter_by_score(df)

def test_save_filtered_dataset(temp_dir, sample_age_filtered_df):
    """Test saving a filtered dataset to CSV."""
    filtered_df, _ = filter_by_score(sample_age_filtered_df)
    output_path = Path(temp_dir) / 'output.csv'
    
    save_filtered_dataset(filtered_df, str(output_path))
    
    assert output_path.exists()
    saved_df = pd.read_csv(output_path)
    assert len(saved_df) == len(filtered_df)

def test_update_exclusion_counts_new_file(temp_dir):
    """Test updating exclusion counts when file doesn't exist."""
    counts_file = Path(temp_dir) / 'counts.json'
    
    update_exclusion_counts('ERR_TEST', 10, str(counts_file))
    
    assert counts_file.exists()
    with open(counts_file, 'r') as f:
        counts = json.load(f)
    
    assert counts['ERR_TEST'] == 10

def test_update_exclusion_counts_existing_file(temp_dir):
    """Test updating exclusion counts when file already exists."""
    counts_file = Path(temp_dir) / 'counts.json'
    
    # Create initial counts file
    initial_counts = {'ERR_EXISTING': 5}
    with open(counts_file, 'w') as f:
        json.dump(initial_counts, f)
    
    update_exclusion_counts('ERR_NEW', 10, str(counts_file))
    
    with open(counts_file, 'r') as f:
        counts = json.load(f)
    
    assert counts['ERR_EXISTING'] == 5
    assert counts['ERR_NEW'] == 10

def test_end_to_end_score_exclusion(temp_dir, sample_age_filtered_df):
    """Test the complete flow of score exclusion."""
    input_path = Path(temp_dir) / 'input.csv'
    output_path = Path(temp_dir) / 'output.csv'
    counts_path = Path(temp_dir) / 'counts.json'
    
    # Save input
    sample_age_filtered_df.to_csv(input_path, index=False)
    
    # Load
    df = load_age_filtered_dataset(str(input_path))
    
    # Filter
    filtered_df, excluded_count = filter_by_score(df)
    
    # Save
    save_filtered_dataset(filtered_df, str(output_path))
    
    # Update counts
    update_exclusion_counts('ERR_MISSING_SCORE', excluded_count, str(counts_path))
    
    # Verify output
    assert output_path.exists()
    assert counts_path.exists()
    
    with open(counts_path, 'r') as f:
        counts = json.load(f)
    
    assert counts['ERR_MISSING_SCORE'] == 2
    assert len(pd.read_csv(output_path)) == 4