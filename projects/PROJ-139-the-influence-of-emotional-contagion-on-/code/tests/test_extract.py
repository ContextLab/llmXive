"""
Unit tests for code/data/extract.py (T012).

Tests the extraction logic for seed posts, insufficient seed flagging,
and metadata completeness validation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import logging

from code.data.extract import (
    extract_seed_posts, 
    load_downloaded_data, 
    run_extraction,
    validate_metadata_completeness
)


@pytest.fixture
def sample_data():
    """
    Creates a synthetic DataFrame mimicking Reddit comment data structure.
    Includes top-level comments and nested comments.
    """
    data = {
        'id': [
            't3_thread1', 't1_comment1', 't1_comment2', 't1_comment3', 't1_comment4', # Thread 1
            't3_thread2', 't1_comment5', 't1_comment6',                             # Thread 2
            't3_thread3', 't1_comment7'                                             # Thread 3 (only 1 comment)
        ],
        'parent_id': [
            None, 't3_thread1', 't3_thread1', 't3_thread1', 't1_comment2', # Thread 1
            None, 't3_thread2', 't3_thread2',                              # Thread 2
            None, 't3_thread3'                                             # Thread 3
        ],
        'created_utc': [
            100, 101, 102, 103, 104, # Thread 1 (sorted)
            200, 201, 202,           # Thread 2 (sorted)
            300, 301                 # Thread 3 (sorted)
        ],
        'author': ['user0', 'user1', 'user2', 'user3', 'user4', 'user0', 'user5', 'user6', 'user0', 'user7'],
        'selftext': ['root', 'reply1', 'reply2', 'reply3', 'reply_nested', 'root2', 'reply5', 'reply6', 'root3', 'reply7'],
        'subreddit': ['test', 'test', 'test', 'test', 'test', 'test', 'test', 'test', 'test', 'test']
    }
    return pd.DataFrame(data)


@pytest.fixture
def temp_raw_dir(sample_data, tmp_path):
    """
    Creates a temporary directory with a JSONL file containing sample data.
    """
    file_path = tmp_path / "sample_data.jsonl"
    sample_data.to_json(file_path, orient='records', lines=True)
    return tmp_path


def test_extract_seed_posts(sample_data):
    """
    test_extract_seed_posts: Asserts a small set of posts extracted.
    
    Verifies that the first N=3 top-level comments are extracted per thread.
    Expected:
      - Thread 1: comment1, comment2, comment3 (3 seeds)
      - Thread 2: comment5, comment6 (2 seeds)
      - Thread 3: comment7 (1 seed)
      - Total: 6 seeds
    """
    result = extract_seed_posts(sample_data, n_seeds=3)
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 6
    
    # Check Thread 1 seeds
    thread1_seeds = result[
        (result['id'].str.startswith('t1_')) & 
        (result['parent_id'] == 't3_thread1')
    ]
    assert len(thread1_seeds) == 3
    assert set(thread1_seeds['id'].tolist()) == {'t1_comment1', 't1_comment2', 't1_comment3'}
    
    # Check Thread 2 seeds
    thread2_seeds = result[
        (result['id'].str.startswith('t1_')) & 
        (result['parent_id'] == 't3_thread2')
    ]
    assert len(thread2_seeds) == 2
    assert set(thread2_seeds['id'].tolist()) == {'t1_comment5', 't1_comment6'}


def test_flag_insufficient_seeds(sample_data):
    """
    test_flag_insufficient_seeds: Asserts exclusion logic behavior.
    
    Verifies that threads with <3 top-level posts are handled gracefully.
    While T010 handles the logging of exclusions, this test ensures the
    extraction function returns the available seeds without crashing,
    which is a prerequisite for the exclusion logic to identify them.
    """
    result = extract_seed_posts(sample_data, n_seeds=3)
    
    # Thread 3 has only 1 seed. It should be included in the result.
    thread3_ids = result[result['parent_id'] == 't3_thread3']['id'].tolist()
    assert 't1_comment7' in thread3_ids
    assert len(thread3_ids) == 1
    
    # Verify that we didn't drop the thread entirely, just limited the seeds
    # This allows downstream logic (T010) to flag it as SEED_INSUFFICIENT if needed


def test_metadata_completeness(sample_data):
    """
    test_metadata_completeness: Asserts a high-confidence threshold.
    
    Verifies that extracted posts retain required metadata columns and
    that critical fields (id, parent_id, created_utc, author) are not null.
    """
    result = extract_seed_posts(sample_data, n_seeds=3)
    
    required_columns = ['id', 'parent_id', 'created_utc', 'author', 'selftext']
    
    for col in required_columns:
        assert col in result.columns, f"Missing column: {col}"
    
    # Check for nulls in critical fields
    critical_fields = ['id', 'parent_id', 'created_utc', 'author']
    for field in critical_fields:
        null_count = result[field].isnull().sum()
        assert null_count == 0, f"Column {field} has {null_count} null values, expected 0"
    
    # Assert completeness threshold (100% for this clean sample)
    total_cells = len(result) * len(critical_fields)
    non_null_cells = total_cells - sum(result[f].isnull().sum() for f in critical_fields)
    completeness_ratio = non_null_cells / total_cells
    assert completeness_ratio >= 0.95, f"Metadata completeness {completeness_ratio} is below 0.95 threshold"


def test_extract_empty_dataframe():
    """
    Asserts that an empty DataFrame returns an empty result.
    """
    empty_df = pd.DataFrame(columns=['id', 'parent_id', 'created_utc', 'author', 'selftext'])
    result = extract_seed_posts(empty_df, n_seeds=3)
    assert result.empty


def test_run_extraction_integration(temp_raw_dir, tmp_path):
    """
    Integration test for run_extraction function.
    Verifies that the function reads from a directory, processes, and writes output.
    """
    output_file = run_extraction(raw_dir=temp_raw_dir, output_dir=tmp_path)
    
    assert os.path.exists(output_file)
    assert "seed_posts.csv" in output_file
    
    df_out = pd.read_csv(output_file)
    assert not df_out.empty
    assert 'id' in df_out.columns
    assert 'created_utc' in df_out.columns