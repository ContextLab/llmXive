"""
Unit tests for T025: Merge and Save logic.
"""
import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Mock config for testing
MOCK_CONFIG = {
    'paths': {
        'data_processed': 'data/processed',
        'data_interim': 'data/interim',
        'data_results': 'data/results'
    }
}

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_features_missing_file(temp_dir):
    """Test that load_features raises FileNotFoundError if file is missing."""
    from merge_save import load_features
    
    config = {'paths': {'data_processed': str(temp_dir / 'nonexistent')}}
    
    with pytest.raises(FileNotFoundError, match="Required file missing"):
        load_features(config)

def test_load_features_missing_columns(temp_dir):
    """Test that load_features raises ValueError if columns are missing."""
    from merge_save import load_features
    
    # Create a temp file with wrong columns
    csv_path = temp_dir / 'features.csv'
    df_wrong = pd.DataFrame({'wrong_col': [1, 2, 3]})
    df_wrong.to_csv(csv_path, index=False)
    
    config = {'paths': {'data_processed': str(temp_dir)}}
    
    with pytest.raises(ValueError, match="Features file missing required columns"):
        load_features(config)

def test_load_features_success(temp_dir):
    """Test successful loading of features."""
    from merge_save import load_features
    
    csv_path = temp_dir / 'features.csv'
    df_correct = pd.DataFrame({
        'prompt_id': ['p1', 'p2'],
        'raw_text': ['text1', 'text2'],
        'feature_a': [0.1, 0.2]
    })
    df_correct.to_csv(csv_path, index=False)
    
    config = {'paths': {'data_processed': str(temp_dir)}}
    result = load_features(config)
    
    assert result.shape == (2, 3)
    assert 'prompt_id' in result.columns
    assert 'raw_text' in result.columns

def test_load_responses_missing_file(temp_dir):
    """Test that load_responses raises FileNotFoundError if file is missing."""
    from merge_save import load_responses
    
    config = {'paths': {'data_interim': str(temp_dir / 'nonexistent')}}
    
    with pytest.raises(FileNotFoundError, match="Required file missing"):
        load_responses(config)

def test_load_responses_missing_columns(temp_dir):
    """Test that load_responses raises ValueError if columns are missing."""
    from merge_save import load_responses
    
    csv_path = temp_dir / 'labeling_results.csv'
    df_wrong = pd.DataFrame({'wrong_col': [1, 2, 3]})
    df_wrong.to_csv(csv_path, index=False)
    
    config = {'paths': {'data_interim': str(temp_dir)}}
    
    with pytest.raises(ValueError, match="Labeling results missing required columns"):
        load_responses(config)

def test_merge_datasets_inner_join(temp_dir):
    """Test that merge_datasets performs an inner join."""
    from merge_save import merge_datasets
    
    df_features = pd.DataFrame({
        'prompt_id': ['p1', 'p2', 'p3'],
        'raw_text': ['t1', 't2', 't3']
    })
    
    df_responses = pd.DataFrame({
        'prompt_id': ['p2', 'p3', 'p4'],
        'response_text': ['r2', 'r3', 'r4'],
        'adherence_label': [0, 1, 0],
        'safety_refusal': [False, False, True]
    })
    
    merged = merge_datasets(df_features, df_responses)
    
    # Inner join should only keep p2 and p3
    assert len(merged) == 2
    assert set(merged['prompt_id']) == {'p2', 'p3'}
    assert 'response_text' in merged.columns
    assert 'adherence_label' in merged.columns

def test_merge_datasets_empty_result(temp_dir):
    """Test that merge_datasets raises ValueError if result is empty."""
    from merge_save import merge_datasets
    
    df_features = pd.DataFrame({
        'prompt_id': ['p1'],
        'raw_text': ['t1']
    })
    
    df_responses = pd.DataFrame({
        'prompt_id': ['p2'],
        'response_text': ['r2'],
        'adherence_label': [0],
        'safety_refusal': [False]
    })
    
    with pytest.raises(ValueError, match="Merged dataset is empty"):
        merge_datasets(df_features, df_responses)

def test_save_merged_dataset(temp_dir):
    """Test that save_merged_dataset writes the file correctly."""
    from merge_save import save_merged_dataset
    
    df = pd.DataFrame({
        'prompt_id': ['p1'],
        'raw_text': ['t1'],
        'response_text': ['r1'],
        'adherence_label': [0],
        'safety_refusal': [False]
    })
    
    output_path = temp_dir / 'labeled_responses.csv'
    config = {'paths': {'data_interim': str(temp_dir)}}
    
    save_merged_dataset(df, config)
    
    assert output_path.exists()
    loaded = pd.read_csv(output_path)
    assert len(loaded) == 1
    assert loaded['prompt_id'].iloc[0] == 'p1'