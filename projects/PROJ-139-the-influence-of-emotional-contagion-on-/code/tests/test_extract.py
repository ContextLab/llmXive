import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import json
import logging

# Import the functions we are testing from the implementation
from code.data.extract import (
    load_downloaded_data,
    extract_seed_posts,
    flag_insufficient_seeds,
    log_exclusions,
    validate_metadata_completeness
)
from code.config.settings import get_config

# Fixtures
@pytest.fixture
def sample_data():
    """
    Creates a realistic sample dataframe mimicking the structure of downloaded Reddit data.
    Includes threads with sufficient seeds (>=3 top-level), insufficient seeds (<3),
    and missing metadata.
    """
    data = [
        # Thread 1: Sufficient seeds (4 top-level posts)
        {
            "thread_id": "t1", "post_id": "p1_0", "parent_id": "t1", "depth": 0,
            "timestamp": 1678886400, "author": "user_a", "text": "Seed 1",
            "subreddit": "AskScience", "site": "reddit"
        },
        {
            "thread_id": "t1", "post_id": "p1_1", "parent_id": "t1", "depth": 0,
            "timestamp": 1678886500, "author": "user_b", "text": "Seed 2",
            "subreddit": "AskScience", "site": "reddit"
        },
        {
            "thread_id": "t1", "post_id": "p1_2", "parent_id": "t1", "depth": 0,
            "timestamp": 1678886600, "author": "user_c", "text": "Seed 3",
            "subreddit": "AskScience", "site": "reddit"
        },
        {
            "thread_id": "t1", "post_id": "p1_3", "parent_id": "t1", "depth": 0,
            "timestamp": 1678886700, "author": "user_d", "text": "Seed 4",
            "subreddit": "AskScience", "site": "reddit"
        },
        # A reply to the first seed (depth 1)
        {
            "thread_id": "t1", "post_id": "p1_4", "parent_id": "p1_0", "depth": 1,
            "timestamp": 1678886800, "author": "user_e", "text": "Reply to seed 1",
            "subreddit": "AskScience", "site": "reddit"
        },

        # Thread 2: Insufficient seeds (2 top-level posts)
        {
            "thread_id": "t2", "post_id": "p2_0", "parent_id": "t2", "depth": 0,
            "timestamp": 1678890000, "author": "user_f", "text": "Seed 1",
            "subreddit": "AskScience", "site": "reddit"
        },
        {
            "thread_id": "t2", "post_id": "p2_1", "parent_id": "t2", "depth": 0,
            "timestamp": 1678890100, "author": "user_g", "text": "Seed 2",
            "subreddit": "AskScience", "site": "reddit"
        },

        # Thread 3: Missing metadata (None author)
        {
            "thread_id": "t3", "post_id": "p3_0", "parent_id": "t3", "depth": 0,
            "timestamp": 1678900000, "author": None, "text": "Seed 1",
            "subreddit": "AskScience", "site": "reddit"
        },
        {
            "thread_id": "t3", "post_id": "p3_1", "parent_id": "t3", "depth": 0,
            "timestamp": 1678900100, "author": "user_h", "text": "Seed 2",
            "subreddit": "AskScience", "site": "reddit"
        },
        {
            "thread_id": "t3", "post_id": "p3_2", "parent_id": "t3", "depth": 0,
            "timestamp": 1678900200, "author": "user_i", "text": "Seed 3",
            "subreddit": "AskScience", "site": "reddit"
        },

        # Thread 4: Missing timestamp
        {
            "thread_id": "t4", "post_id": "p4_0", "parent_id": "t4", "depth": 0,
            "timestamp": None, "author": "user_j", "text": "Seed 1",
            "subreddit": "AskScience", "site": "reddit"
        },
        {
            "thread_id": "t4", "post_id": "p4_1", "parent_id": "t4", "depth": 0,
            "timestamp": 1678910100, "author": "user_k", "text": "Seed 2",
            "subreddit": "AskScience", "site": "reddit"
        },
        {
            "thread_id": "t4", "post_id": "p4_2", "parent_id": "t4", "depth": 0,
            "timestamp": 1678910200, "author": "user_l", "text": "Seed 3",
            "subreddit": "AskScience", "site": "reddit"
        }
    ]
    return pd.DataFrame(data)

@pytest.fixture
def temp_raw_dir():
    """Creates a temporary directory to simulate data/raw for loading tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_extract_seed_posts(sample_data):
    """
    Asserts that extract_seed_posts correctly identifies and returns the first N=3
    top-level posts for threads with sufficient seeds.
    """
    # Run extraction
    result = extract_seed_posts(sample_data, n_seeds=3)

    # Check that t1 is present and has exactly 3 seeds
    t1_seeds = result[result['thread_id'] == 't1']
    assert len(t1_seeds) == 3, f"Expected 3 seeds for t1, got {len(t1_seeds)}"
    
    # Verify they are top-level (depth 0)
    assert all(t1_seeds['depth'] == 0), "All extracted seeds must be depth 0"
    
    # Verify they are the first 3 by timestamp (or just the first 3 in order if timestamps equal)
    # In our sample, p1_0, p1_1, p1_2 are the first three
    expected_ids = {'p1_0', 'p1_1', 'p1_2'}
    actual_ids = set(t1_seeds['post_id'].tolist())
    assert actual_ids == expected_ids, f"Expected IDs {expected_ids}, got {actual_ids}"

    # Check that t2 is NOT present (insufficient seeds)
    t2_rows = result[result['thread_id'] == 't2']
    assert len(t2_rows) == 0, "Thread t2 should be excluded due to insufficient seeds"

def test_flag_insufficient_seeds(sample_data):
    """
    Asserts that flag_insufficient_seeds correctly identifies threads with <3 top-level posts
    and returns the expected exclusion list with the correct reason code.
    """
    # Run flagging logic
    exclusions = flag_insufficient_seeds(sample_data, min_seeds=3)

    # We expect t2 to be excluded.
    # t3 and t4 have 3 seeds but might fail metadata validation later, 
    # but flag_insufficient_seeds only checks count.
    # t1 has 4 seeds (pass).
    # t2 has 2 seeds (fail).
    
    assert len(exclusions) == 1, f"Expected 1 exclusion for seed count, got {len(exclusions)}"
    
    excluded_thread = exclusions[0]
    assert excluded_thread['thread_id'] == 't2', "Thread t2 should be excluded"
    assert excluded_thread['reason_code'] == 'SEED_INSUFFICIENT', \
        f"Expected reason SEED_INSUFFICIENT, got {excluded_thread['reason_code']}"
    assert excluded_thread['count'] == 2, f"Expected count 2, got {excluded_thread['count']}"

def test_metadata_completeness(sample_data):
    """
    Asserts that validate_metadata_completeness correctly calculates completeness
    and flags threads that fall below the threshold (e.g., 95%).
    """
    # We have 4 threads: t1, t2, t3, t4
    # t1: 5 rows, all complete -> 100%
    # t2: 2 rows, all complete -> 100%
    # t3: 3 rows, 1 missing author -> 66.6% (FAIL)
    # t4: 3 rows, 1 missing timestamp -> 66.6% (FAIL)
    
    threshold = 0.95
    result = validate_metadata_completeness(sample_data, threshold=threshold)
    
    # The function should return a dataframe or list of threads that PASS or FAIL?
    # Based on typical implementation, let's assume it returns a dict/list of status.
    # We need to verify the logic:
    # It should identify t3 and t4 as failing.
    
    # Let's assume the function returns a DataFrame with a 'completeness' column
    # and we filter for those < threshold.
    
    if isinstance(result, pd.DataFrame):
        # Filter for failed threads
        failed = result[result['completeness'] < threshold]
        failed_ids = set(failed['thread_id'].tolist())
        assert 't3' in failed_ids, "Thread t3 should be flagged for incomplete metadata"
        assert 't4' in failed_ids, "Thread t4 should be flagged for incomplete metadata"
        assert 't1' not in failed_ids, "Thread t1 should pass metadata check"
        assert 't2' not in failed_ids, "Thread t2 should pass metadata check"
    else:
        # If it returns a list of failed threads
        failed_ids = set(r['thread_id'] for r in result)
        assert 't3' in failed_ids
        assert 't4' in failed_ids

def test_extract_empty_dataframe():
    """
    Asserts that extract_seed_posts handles an empty DataFrame gracefully.
    """
    empty_df = pd.DataFrame(columns=['thread_id', 'post_id', 'parent_id', 'depth', 'timestamp', 'author', 'text'])
    result = extract_seed_posts(empty_df, n_seeds=3)
    assert result.empty, "Result should be empty for empty input"

def test_run_extraction_integration(sample_data, temp_raw_dir):
    """
    Integration test: Simulates the full extraction flow including logging exclusions.
    """
    # 1. Save sample data to a temp file to mimic load_downloaded_data
    temp_file = temp_raw_dir / "sample_threads.json"
    sample_data.to_json(temp_file, orient='records')
    
    # 2. Load data (using the real loader)
    loaded_data = load_downloaded_data(temp_file)
    
    # 3. Run extraction pipeline (mocking the main flow)
    # We manually call the functions to ensure they work together
    exclusions = flag_insufficient_seeds(loaded_data, min_seeds=3)
    
    # 4. Verify exclusions are logged correctly
    # Create a temp log path
    log_path = temp_raw_dir / "exclusions.log"
    log_exclusions(exclusions, log_path)
    
    assert log_path.exists(), "Exclusions log file should be created"
    
    with open(log_path, 'r') as f:
        content = f.read()
    
    assert "t2" in content, "Log should contain thread t2"
    assert "SEED_INSUFFICIENT" in content, "Log should contain reason code"
    
    # 5. Verify extracted seeds
    seeds = extract_seed_posts(loaded_data, n_seeds=3)
    assert not seeds.empty, "Seeds should be extracted"
    assert 't1' in seeds['thread_id'].values, "t1 should be in extracted seeds"
    assert 't2' not in seeds['thread_id'].values, "t2 should not be in extracted seeds"