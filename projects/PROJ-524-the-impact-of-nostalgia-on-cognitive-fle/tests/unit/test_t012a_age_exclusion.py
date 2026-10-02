"""
Unit tests for T012a: Age Exclusion
"""
import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import os
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from task_t012a_age_exclusion import (
    load_raw_dataset,
    filter_by_age,
    save_filtered_dataset,
    save_exclusion_count
)

@pytest.fixture
def sample_raw_data():
    """Create sample raw data for testing."""
    data = {
        'participant_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
        'age': [60, 65, 70, 75, 80],
        'stimulus_type': ['nostalgia', 'control', 'nostalgia', 'control', 'nostalgia'],
        'perseverative_errors': [10, 5, 8, 3, 6],
        'categories_completed': [3, 5, 4, 6, 4]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_filter_by_age_includes_valid_ages(sample_raw_data):
    """Test that filter_by_age correctly includes participants aged 65 and above."""
    filtered_df, excluded_count = filter_by_age(sample_raw_data, min_age=65)
    
    # Should include P002 (65), P003 (70), P004 (75), P005 (80)
    assert len(filtered_df) == 4
    assert excluded_count == 1
    
    # Verify all ages in filtered data are >= 65
    assert all(filtered_df['age'] >= 65)
    
    # Verify P001 (age 60) is excluded
    assert 'P001' not in filtered_df['participant_id'].values

def test_filter_by_age_all_excluded(temp_dir, sample_raw_data):
    """Test filter when all participants are below age threshold."""
    young_data = sample_raw_data.copy()
    young_data['age'] = [50, 55, 60, 62, 64]
    
    filtered_df, excluded_count = filter_by_age(young_data, min_age=65)
    
    assert len(filtered_df) == 0
    assert excluded_count == 5

def test_filter_by_age_no_exclusions(temp_dir, sample_raw_data):
    """Test filter when all participants meet age threshold."""
    old_data = sample_raw_data.copy()
    old_data['age'] = [65, 70, 75, 80, 85]
    
    filtered_df, excluded_count = filter_by_age(old_data, min_age=65)
    
    assert len(filtered_df) == 5
    assert excluded_count == 0

def test_save_filtered_dataset(temp_dir, sample_raw_data):
    """Test that filtered data is saved correctly."""
    filtered_df, _ = filter_by_age(sample_raw_data)
    output_path = temp_dir / "test_output.csv"
    
    save_filtered_dataset(filtered_df, output_path)
    
    assert output_path.exists()
    
    # Verify saved data matches filtered data
    saved_df = pd.read_csv(output_path)
    assert len(saved_df) == len(filtered_df)
    assert list(saved_df.columns) == list(filtered_df.columns)

def test_save_exclusion_count_creates_file(temp_dir):
    """Test that exclusion count is saved correctly."""
    counts_path = temp_dir / "exclusion_counts.json"
    
    save_exclusion_count(5, counts_path)
    
    assert counts_path.exists()
    
    with open(counts_path, 'r') as f:
        counts = json.load(f)
    
    assert counts["ERR_MISSING_AGE_FIELD"] == 5
    assert "ERR_MISSING_SCORE" in counts
    assert "ERR_MMSE_IMPAIRED" in counts

def test_save_exclusion_count_updates_existing(temp_dir):
    """Test that exclusion count updates existing file correctly."""
    counts_path = temp_dir / "exclusion_counts.json"
    
    # Create initial file
    initial_counts = {
        "ERR_MISSING_AGE_FIELD": 2,
        "ERR_MISSING_SCORE": 3,
        "ERR_MMSE_IMPAIRED": 1
    }
    with open(counts_path, 'w') as f:
        json.dump(initial_counts, f)
    
    # Update with new count
    save_exclusion_count(10, counts_path)
    
    with open(counts_path, 'r') as f:
        counts = json.load(f)
    
    assert counts["ERR_MISSING_AGE_FIELD"] == 10
    assert counts["ERR_MISSING_SCORE"] == 3  # Unchanged
    assert counts["ERR_MMSE_IMPAIRED"] == 1  # Unchanged