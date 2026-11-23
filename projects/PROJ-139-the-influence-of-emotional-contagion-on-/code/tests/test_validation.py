import os
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path
from code.data.validation import (
    compute_external_validation_score,
    classify_thread,
    validate_and_classify,
    run_validation_pipeline
)

def test_compute_external_validation_score_stackexchange_valid():
    """Test StackExchange thread with accepted answer."""
    thread = {
        'platform': 'StackExchange',
        'accepted_answer_id': 12345
    }
    assert compute_external_validation_score(thread) == 1.0

def test_compute_external_validation_score_stackexchange_invalid():
    """Test StackExchange thread without accepted answer."""
    thread = {
        'platform': 'StackExchange',
        'accepted_answer_id': None
    }
    assert compute_external_validation_score(thread) == 0.0

def test_compute_external_validation_score_reddit_valid():
    """Test Reddit thread with upvotes > downvotes."""
    thread = {
        'platform': 'Reddit',
        'upvotes': 100,
        'downvotes': 50
    }
    assert compute_external_validation_score(thread) == 1.0

def test_compute_external_validation_score_reddit_invalid():
    """Test Reddit thread with upvotes < downvotes."""
    thread = {
        'platform': 'Reddit',
        'upvotes': 50,
        'downvotes': 100
    }
    assert compute_external_validation_score(thread) == 0.0

def test_compute_external_validation_score_reddit_inconclusive():
    """Test Reddit thread with equal upvotes and downvotes."""
    thread = {
        'platform': 'Reddit',
        'upvotes': 50,
        'downvotes': 50
    }
    assert compute_external_validation_score(thread) is None

def test_compute_external_validation_score_reddit_missing_upvotes():
    """Test Reddit thread with missing upvotes (should return None and be logged)."""
    thread = {
        'platform': 'Reddit',
        'upvotes': None,
        'downvotes': 50
    }
    assert compute_external_validation_score(thread) is None

def test_compute_external_validation_score_reddit_missing_downvotes():
    """Test Reddit thread with missing downvotes (should return None and be logged)."""
    thread = {
        'platform': 'Reddit',
        'upvotes': 100,
        'downvotes': None
    }
    assert compute_external_validation_score(thread) is None

def test_compute_external_validation_score_reddit_missing_both():
    """Test Reddit thread with both missing (should return None and be logged)."""
    thread = {
        'platform': 'Reddit',
        'upvotes': None,
        'downvotes': None
    }
    assert compute_external_validation_score(thread) is None

def test_classify_thread_stackexchange_valid():
    """Test classification of valid StackExchange thread."""
    thread = {
        'platform': 'StackExchange',
        'accepted_answer_id': 123
    }
    assert classify_thread(thread) == 'valid'

def test_classify_thread_stackexchange_invalid():
    """Test classification of invalid StackExchange thread."""
    thread = {
        'platform': 'StackExchange',
        'accepted_answer_id': None
    }
    assert classify_thread(thread) == 'invalid'

def test_classify_thread_reddit():
    """Test classification of Reddit thread."""
    thread = {
        'platform': 'Reddit'
    }
    assert classify_thread(thread) == 'valid_no_gt'

def test_run_validation_pipeline_missing_votes_logging():
    """Test that missing vote data is correctly logged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'input.csv')
        output_valid = os.path.join(tmpdir, 'valid.csv')
        output_all = os.path.join(tmpdir, 'all.csv')
        output_stats = os.path.join(tmpdir, 'stats.json')
        output_compliance = os.path.join(tmpdir, 'compliance.json')
        output_missing_log = os.path.join(tmpdir, 'missing_votes.log')
        
        # Create input data with missing votes
        data = [
            {
                'thread_id': 't1',
                'platform': 'Reddit',
                'upvotes': 10,
                'downvotes': 5,
                'accepted_answer_id': None
            },
            {
                'thread_id': 't2',
                'platform': 'Reddit',
                'upvotes': None,
                'downvotes': 5,
                'accepted_answer_id': None
            },
            {
                'thread_id': 't3',
                'platform': 'StackExchange',
                'upvotes': None,
                'downvotes': None,
                'accepted_answer_id': 123
            }
        ]
        df_input = pd.DataFrame(data)
        df_input.to_csv(input_path, index=False)
        
        run_validation_pipeline(
            input_path=input_path,
            output_valid_path=output_valid,
            output_all_classified_path=output_all,
            output_gt_stats_path=output_stats,
            output_compliance_path=output_compliance,
            output_missing_votes_log=output_missing_log
        )
        
        # Verify missing votes log exists and contains t2
        assert os.path.exists(output_missing_log)
        with open(output_missing_log, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 1
        logged_data = json.loads(lines[0])
        assert logged_data['thread_id'] == 't2'
        assert 'Missing upvotes or downvotes' in logged_data['reason']
        
        # Verify valid threads CSV contains t1 and t3 (t3 is StackExchange valid)
        df_valid = pd.read_csv(output_valid)
        assert len(df_valid) == 2
        assert 't1' in df_valid['thread_id'].values
        assert 't3' in df_valid['thread_id'].values
        
        # Verify external_validation_score for t2 is None in all.csv
        df_all = pd.read_csv(output_all)
        row_t2 = df_all[df_all['thread_id'] == 't2'].iloc[0]
        assert pd.isna(row_t2['external_validation_score'])