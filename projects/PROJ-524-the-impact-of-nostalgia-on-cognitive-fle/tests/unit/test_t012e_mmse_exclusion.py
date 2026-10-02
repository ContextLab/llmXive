import os
import json
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
from task_t012e_mmse_exclusion import (
    load_score_filtered_dataset,
    load_mmse_flag,
    filter_mmse,
    save_cleaned_dataset,
    save_no_mmse_dataset,
    update_exclusion_counts,
    save_exclusion_counts,
    main
)
from config import get_config

@pytest.fixture
def mock_config(tmp_path):
    """Create a temporary config structure for testing."""
    processed_dir = tmp_path / 'data' / 'processed'
    processed_dir.mkdir(parents=True)
    
    # Mock config return
    mock_cfg = {
        'paths': {
            'processed': processed_dir
        }
    }
    
    with patch('task_t012e_mmse_exclusion.get_config', return_value=mock_cfg):
        yield processed_dir

@pytest.fixture
def sample_score_filtered_df():
    """Create a sample dataframe matching T012b output."""
    data = {
        'participant_id': ['P1', 'P2', 'P3', 'P4', 'P5'],
        'stimulus_type': ['nostalgia', 'control', 'nostalgia', 'control', 'nostalgia'],
        'perseverative_errors': [10, 12, 8, 15, 9],
        'categories_completed': [5, 4, 6, 3, 5],
        'age': [65, 70, 68, 72, 66],
        'MMSE': [28, 22, 29, 24, 20]
    }
    return pd.DataFrame(data)

def test_load_mmse_flag_true(mock_config, sample_score_filtered_df):
    """Test loading MMSE flag when True."""
    # Setup
    flag_path = mock_config / 'mmse_flag.json'
    with open(flag_path, 'w') as f:
        json.dump({'has_mmse': True}, f)
    
    # Test
    result = load_mmse_flag()
    assert result is True

def test_load_mmse_flag_false(mock_config):
    """Test loading MMSE flag when False."""
    # Setup
    flag_path = mock_config / 'mmse_flag.json'
    with open(flag_path, 'w') as f:
        json.dump({'has_mmse': False}, f)
    
    # Test
    result = load_mmse_flag()
    assert result is False

def test_filter_mmse(sample_score_filtered_df):
    """Test MMSE filtering logic."""
    # Expected: P1 (28), P3 (29), P4 (24) should remain. P2 (22), P5 (20) excluded.
    filtered_df, excluded_count = filter_mmse(sample_score_filtered_df, threshold=24)
    
    assert len(filtered_df) == 3
    assert excluded_count == 2
    assert all(filtered_df['MMSE'] >= 24)

def test_filter_mmse_no_column(sample_score_filtered_df):
    """Test filtering when MMSE column is missing."""
    df_no_mmse = sample_score_filtered_df.drop(columns=['MMSE'])
    filtered_df, excluded_count = filter_mmse(df_no_mmse, threshold=24)
    
    # Should return original dataframe unchanged
    assert len(filtered_df) == len(df_no_mmse)
    assert excluded_count == 0

def test_update_exclusion_counts():
    """Test updating exclusion counts dictionary."""
    counts = {'ERR_MISSING_AGE': 5}
    updated = update_exclusion_counts(counts, 'ERR_MISSING_SCORE', 3)
    
    assert updated['ERR_MISSING_AGE'] == 5
    assert updated['ERR_MISSING_SCORE'] == 3

def test_main_with_mmse_present(mock_config, sample_score_filtered_df, tmp_path):
    """Test main execution when MMSE is present."""
    # Setup files
    score_path = mock_config / 'cleaned_score_filtered.csv'
    sample_score_filtered_df.to_csv(score_path, index=False)
    
    flag_path = mock_config / 'mmse_flag.json'
    with open(flag_path, 'w') as f:
        json.dump({'has_mmse': True}, f)
    
    # Run main
    with patch('task_t012e_mmse_exclusion.get_mmse_threshold', return_value=24):
        result = main()
    
    assert result == 0
    
    # Verify outputs
    primary_path = mock_config / 'cleaned_dataset.csv'
    robustness_path = mock_config / 'cleaned_dataset_no_mmse.csv'
    exclusion_path = mock_config / 'exclusion_counts.json'
    
    assert primary_path.exists()
    assert robustness_path.exists()
    assert exclusion_path.exists()
    
    # Check primary has MMSE filter applied
    primary_df = pd.read_csv(primary_path)
    assert all(primary_df['MMSE'] >= 24)
    assert len(primary_df) < len(sample_score_filtered_df)
    
    # Check robustness is unfiltered (by MMSE)
    robustness_df = pd.read_csv(robustness_path)
    assert len(robustness_df) == len(sample_score_filtered_df)

def test_main_with_mmse_absent(mock_config, sample_score_filtered_df, tmp_path):
    """Test main execution when MMSE is absent."""
    # Setup files
    score_path = mock_config / 'cleaned_score_filtered.csv'
    sample_score_filtered_df.to_csv(score_path, index=False)
    
    flag_path = mock_config / 'mmse_flag.json'
    with open(flag_path, 'w') as f:
        json.dump({'has_mmse': False}, f)
    
    # Run main
    result = main()
    
    assert result == 0
    
    # Verify outputs
    primary_path = mock_config / 'cleaned_dataset.csv'
    robustness_path = mock_config / 'cleaned_dataset_no_mmse.csv'
    
    assert primary_path.exists()
    assert robustness_path.exists()
    
    # Both should be identical to score filtered
    primary_df = pd.read_csv(primary_path)
    robustness_df = pd.read_csv(robustness_path)
    
    assert len(primary_df) == len(sample_score_filtered_df)
    assert len(robustness_df) == len(sample_score_filtered_df)
    pd.testing.assert_frame_equal(primary_df, robustness_df)

def test_main_missing_flag_file(mock_config, sample_score_filtered_df):
    """Test main execution when MMSE flag file is missing."""
    # Setup score file only
    score_path = mock_config / 'cleaned_score_filtered.csv'
    sample_score_filtered_df.to_csv(score_path, index=False)
    
    # Flag file missing
    
    with pytest.raises(FileNotFoundError):
        main()

def test_main_missing_score_file(mock_config):
    """Test main execution when score filtered file is missing."""
    # Setup flag file
    flag_path = mock_config / 'mmse_flag.json'
    with open(flag_path, 'w') as f:
        json.dump({'has_mmse': True}, f)
    
    # Score file missing
    with pytest.raises(FileNotFoundError):
        main()
