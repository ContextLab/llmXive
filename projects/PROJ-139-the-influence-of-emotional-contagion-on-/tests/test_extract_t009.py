import pytest
import pandas as pd
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock the config to avoid dependency on full setup
from code.data.extract import extract_seed_posts, flag_insufficient_seeds, run_extraction

@pytest.fixture
def sample_valid_threads():
    """Create a mock valid_threads.csv content."""
    data = [
        {
            "thread_id": "t1",
            "subreddit": "AskScience",
            "origin_type": "pushshift",
            "posts": json.dumps([
                {"id": "c1", "parent_id": None, "text": "Seed 1"},
                {"id": "c2", "parent_id": "t1", "text": "Seed 2"},
                {"id": "c3", "parent_id": "t1", "text": "Seed 3"},
                {"id": "c4", "parent_id": "c1", "text": "Reply 1"}
            ])
        },
        {
            "thread_id": "t2",
            "subreddit": "AskScience",
            "origin_type": "huggingface",
            "posts": json.dumps([
                {"id": "c5", "parent_id": None, "text": "Seed 1"},
                {"id": "c6", "parent_id": "t2", "text": "Seed 2"},
                {"id": "c7", "parent_id": "t2", "text": "Seed 3"},
                {"id": "c8", "parent_id": "t2", "text": "Seed 4"}
            ])
        },
        {
            "thread_id": "t3",
            "subreddit": "AskScience",
            "origin_type": "pushshift",
            "posts": json.dumps([
                {"id": "c9", "parent_id": None, "text": "Seed 1"},
                {"id": "c10", "parent_id": "t3", "text": "Seed 2"}
            ]) # Only 2 seeds, should be flagged
        }
    ]
    return pd.DataFrame(data)

@pytest.fixture
def temp_processed_dir(tmp_path):
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    return processed_dir

@pytest.fixture
def temp_valid_file(sample_valid_threads, temp_processed_dir):
    file_path = temp_processed_dir / "valid_threads.csv"
    sample_valid_threads.to_csv(file_path, index=False)
    return file_path

def test_flag_insufficient_seeds_logic(sample_valid_threads):
    """Test that threads with <3 seeds are flagged correctly."""
    # Note: sample_valid_threads has 'posts' as string. 
    # In real run, it might be parsed. Let's assume the function handles string or list.
    # The implementation in extract.py does NOT parse string to list in flag_insufficient_seeds.
    # It assumes 'posts' is a list.
    # We need to parse it for the test to work with the current implementation.
    
    # Parse posts for test
    df = sample_valid_threads.copy()
    df['posts'] = df['posts'].apply(json.loads)
    
    result = flag_insufficient_seeds(df, min_seeds=3)
    
    assert result.loc[result['thread_id'] == 't1', 'seed_status'].values[0] == 'sufficient'
    assert result.loc[result['thread_id'] == 't2', 'seed_status'].values[0] == 'sufficient'
    assert result.loc[result['thread_id'] == 't3', 'seed_status'].values[0] == 'insufficient'

def test_extract_seed_posts_logic(sample_valid_threads):
    """Test that first 3 seeds are extracted correctly."""
    df = sample_valid_threads.copy()
    df['posts'] = df['posts'].apply(json.loads)
    
    # Filter for sufficient first to mimic the flow
    flagged = flag_insufficient_seeds(df, min_seeds=3)
    sufficient = flagged[flagged['seed_status'] == 'sufficient']
    
    result = extract_seed_posts(sufficient, n_seeds=3)
    
    assert len(result) == 2 # t1 and t2
    assert 'seed_id_1' in result.columns
    assert 'seed_id_2' in result.columns
    assert 'seed_id_3' in result.columns
    
    # Check t1 seeds
    t1_row = result[result['thread_id'] == 't1'].iloc[0]
    assert t1_row['seed_id_1'] == 'c1'
    assert t1_row['seed_id_2'] == 'c2'
    assert t1_row['seed_id_3'] == 'c3'

@patch('code.data.extract.get_config')
def test_run_extraction_integration(mock_get_config, sample_valid_threads, temp_processed_dir, temp_valid_file, tmp_path):
    """Test the full run_extraction pipeline."""
    # Setup mock config
    mock_config = MagicMock()
    mock_config.paths = MagicMock()
    mock_config.paths.processed_dir = temp_processed_dir
    mock_get_config.return_value = mock_config

    # Run extraction
    run_extraction()

    # Check output file
    output_path = temp_processed_dir / "threads_with_seeds.csv"
    assert output_path.exists()
    
    output_df = pd.read_csv(output_path)
    assert len(output_df) == 2 # t1 and t2
    assert 'thread_id' in output_df.columns
    assert 'seed_id_1' in output_df.columns

    # Check exclusion log
    exclusion_path = temp_processed_dir / "exclusions_seed.log"
    assert exclusion_path.exists()
    exclusion_df = pd.read_csv(exclusion_path)
    assert len(exclusion_df) == 1 # t3
    assert exclusion_df.iloc[0]['reason_code'] == 'SEED_INSUFFICIENT'