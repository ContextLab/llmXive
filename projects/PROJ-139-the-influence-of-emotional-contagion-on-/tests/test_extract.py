import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import json

from code.data.extract import (
    flag_insufficient_seeds,
    log_exclusions,
    validate_metadata_completeness,
    extract_seed_posts,
    EXCLUSION_REASON_SEED_INSUFFICIENT,
    MIN_SEED_POSTS
)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    data = [
        {'thread_id': 't1', 'parent_id': None, 'created_utc': 1000, 'author': 'user1', 'id': 'c1'},
        {'thread_id': 't1', 'parent_id': 'c1', 'created_utc': 1001, 'author': 'user2', 'id': 'c2'},
        {'thread_id': 't1', 'parent_id': None, 'created_utc': 1002, 'author': 'user3', 'id': 'c3'},
        {'thread_id': 't1', 'parent_id': None, 'created_utc': 1003, 'author': 'user4', 'id': 'c4'},
        {'thread_id': 't1', 'parent_id': None, 'created_utc': 1004, 'author': 'user5', 'id': 'c5'},
        {'thread_id': 't2', 'parent_id': None, 'created_utc': 2000, 'author': 'user6', 'id': 'c6'},
        {'thread_id': 't2', 'parent_id': 'c6', 'created_utc': 2001, 'author': 'user7', 'id': 'c7'},
        {'thread_id': 't3', 'parent_id': None, 'created_utc': 3000, 'author': 'user8', 'id': 'c8'},
        {'thread_id': 't3', 'parent_id': None, 'created_utc': 3001, 'author': 'user9', 'id': 'c9'},
    ]
    return pd.DataFrame(data)

@pytest.fixture
def temp_raw_dir(tmp_path):
    """Create a temporary directory for raw data."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir

def test_extract_seed_posts(sample_data):
    """Test that seed posts are correctly extracted."""
    # Thread t1 has 4 top-level posts, should get 3
    # Thread t2 has 1 top-level post, should get 1
    # Thread t3 has 2 top-level posts, should get 2
    
    result = extract_seed_posts(sample_data, n_seed_posts=3)
    
    # Check that we got the correct number of seed posts
    assert len(result) == 6  # 3 from t1, 1 from t2, 2 from t3
    
    # Check that only top-level posts are included
    assert all(result['parent_id'].isna())
    
    # Check thread t1 has exactly 3 seed posts
    t1_seeds = result[result['thread_id'] == 't1']
    assert len(t1_seeds) == 3
    
    # Check thread t2 has exactly 1 seed post
    t2_seeds = result[result['thread_id'] == 't2']
    assert len(t2_seeds) == 1

def test_flag_insufficient_seeds(sample_data):
    """Test that threads with insufficient seed posts are flagged."""
    exclusions = flag_insufficient_seeds(sample_data, min_seeds=3)
    
    # Thread t2 has 1 top-level post (< 3)
    # Thread t3 has 2 top-level posts (< 3)
    # Thread t1 has 4 top-level posts (>= 3)
    
    assert len(exclusions) == 2
    
    exclusion_thread_ids = [e['thread_id'] for e in exclusions]
    assert 't2' in exclusion_thread_ids
    assert 't3' in exclusion_thread_ids
    
    # Check reason code
    for exclusion in exclusions:
        assert exclusion['reason_code'] == EXCLUSION_REASON_SEED_INSUFFICIENT
        assert exclusion['min_required'] == 3

def test_flag_insufficient_seeds_empty_dataframe():
    """Test flagging with empty dataframe."""
    df = pd.DataFrame(columns=['thread_id', 'parent_id', 'created_utc', 'author', 'id'])
    exclusions = flag_insufficient_seeds(df, min_seeds=3)
    assert len(exclusions) == 0

def test_log_exclusions(tmp_path):
    """Test that exclusions are logged correctly."""
    exclusions = [
        {'thread_id': 't1', 'reason_code': EXCLUSION_REASON_SEED_INSUFFICIENT, 'details': 'Test', 'top_level_count': 1, 'min_required': 3},
        {'thread_id': 't2', 'reason_code': EXCLUSION_REASON_SEED_INSUFFICIENT, 'details': 'Test', 'top_level_count': 2, 'min_required': 3}
    ]
    
    output_path = tmp_path / "exclusions.log"
    log_exclusions(exclusions, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        content = f.read()
    
    assert 'SEED_INSUFFICIENT' in content
    assert 't1' in content
    assert 't2' in content
    assert 'Test' in content

def test_log_exclusions_empty(tmp_path):
    """Test logging with no exclusions."""
    output_path = tmp_path / "exclusions.log"
    log_exclusions([], output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        content = f.read()
    assert "No exclusions" in content

def test_metadata_completeness(sample_data):
    """Test metadata completeness validation."""
    # All records have complete metadata
    completeness = validate_metadata_completeness(sample_data)
    assert completeness == 1.0

def test_metadata_completeness_missing_values(sample_data):
    """Test metadata completeness with missing values."""
    # Add a record with missing author
    incomplete_data = sample_data.copy()
    incomplete_data.loc[0, 'author'] = None
    
    completeness = validate_metadata_completeness(incomplete_data)
    assert completeness < 1.0
    assert completeness == 8/9  # 8 out of 9 records complete

def test_extract_empty_dataframe():
    """Test extraction with empty dataframe."""
    df = pd.DataFrame(columns=['thread_id', 'parent_id', 'created_utc', 'author', 'id'])
    result = extract_seed_posts(df)
    assert result.empty

def test_run_extraction_integration(sample_data, tmp_path):
    """Integration test for the extraction pipeline."""
    # Create a temporary raw data file
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_file = raw_dir / "test_data.jsonl"
    
    with open(raw_file, 'w') as f:
        for _, row in sample_data.iterrows():
            f.write(json.dumps(row.to_dict()) + '\n')
    
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    config = {
        'paths': {
            'raw_data': str(raw_file),
            'processed': str(processed_dir)
        }
    }
    
    from code.data.extract import run_extraction
    results = run_extraction(config)
    
    assert results['status'] == 'success'
    assert results['threads_flagged'] == 2  # t2 and t3
    assert results['threads_with_seed_posts'] == 3  # t1, t2, t3 all have at least 1 seed post
    assert results['total_threads'] == 3
    
    # Check that exclusions log was created
    exclusions_log = processed_dir / "exclusions.log"
    assert exclusions_log.exists()
    
    # Check that seed posts were saved
    seed_posts_file = processed_dir / "seed_posts.csv"
    assert seed_posts_file.exists()