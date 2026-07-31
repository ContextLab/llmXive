"""
Tests for ambiguous ground truth handling in validation.py
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
from code.data.validation import classify_thread, validate_and_classify, check_valid_thread_threshold

class TestAmbiguousGroundTruth:
    """Test handling of threads with multiple accepted answers."""
    
    def test_single_accepted_answer_valid(self):
        """Test that a single accepted answer is classified as valid."""
        thread = {
            'platform': 'stackexchange',
            'accepted_answer_id': '12345',
            'thread_id': 'test_1'
        }
        status, reason = classify_thread(thread)
        assert status == 'valid'
        assert reason == 'accepted_answer_exists'
    
    def test_multiple_accepted_answers_ambiguous(self):
        """Test that multiple accepted answers are classified as ambiguous."""
        thread = {
            'platform': 'stackexchange',
            'accepted_answer_id': ['12345', '67890'],
            'thread_id': 'test_2'
        }
        status, reason = classify_thread(thread)
        assert status == 'ambiguous'
        assert reason == 'multiple_accepted_answers'
    
    def test_empty_accepted_answer_list_invalid(self):
        """Test that empty accepted answer list is invalid."""
        thread = {
            'platform': 'stackexchange',
            'accepted_answer_id': [],
            'thread_id': 'test_3'
        }
        status, reason = classify_thread(thread)
        assert status == 'invalid'
        assert reason == 'no_accepted_answer'
    
    def test_reddit_thread_valid_no_gt(self):
        """Test that Reddit threads are classified as valid_no_gt."""
        thread = {
            'platform': 'reddit',
            'thread_id': 'test_4',
            'upvotes': 100,
            'downvotes': 10
        }
        status, reason = classify_thread(thread)
        assert status == 'valid_no_gt'
        assert reason == 'reddit_no_external_gt'
    
    def test_validate_and_classify_detects_ambiguous(self, tmp_path):
        """Test that validate_and_classify correctly identifies and logs ambiguous threads."""
        # Create test data
        data = {
            'thread_id': ['t1', 't2', 't3', 't4'],
            'platform': ['stackexchange', 'stackexchange', 'stackexchange', 'reddit'],
            'accepted_answer_id': [
                '123', 
                ['456', '789'],  # Ambiguous
                None, 
                None
            ],
            'upvotes': [None, None, None, 50],
            'downvotes': [None, None, None, 10]
        }
        df = pd.DataFrame(data)
        
        # Run validation
        result_df = validate_and_classify(df)
        
        # Check classifications
        assert result_df.loc[result_df['thread_id'] == 't1', 'classification'].values[0] == 'valid'
        assert result_df.loc[result_df['thread_id'] == 't2', 'classification'].values[0] == 'ambiguous'
        assert result_df.loc[result_df['thread_id'] == 't3', 'classification'].values[0] == 'invalid'
        assert result_df.loc[result_df['thread_id'] == 't4', 'classification'].values[0] == 'valid_no_gt'
        
        # Check that ambiguous log was created
        log_path = Path('data/processed/ambiguous_ground_truth.log')
        if log_path.exists():
            with open(log_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) >= 1
                ambiguous_entry = json.loads(lines[0])
                assert ambiguous_entry['thread_id'] == 't2'
                assert ambiguous_entry['reason'] == 'multiple_accepted_answers'
    
    def test_no_ambiguous_threads_no_log(self, tmp_path):
        """Test that no ambiguous log is created when there are no ambiguous threads."""
        # Create test data with no ambiguous threads
        data = {
            'thread_id': ['t1', 't2'],
            'platform': ['stackexchange', 'reddit'],
            'accepted_answer_id': ['123', None],
            'upvotes': [None, 50],
            'downvotes': [None, 10]
        }
        df = pd.DataFrame(data)
        
        # Remove existing log if present
        log_path = Path('data/processed/ambiguous_ground_truth.log')
        if log_path.exists():
            log_path.unlink()
        
        # Run validation
        result_df = validate_and_classify(df)
        
        # Check that no log was created
        assert not log_path.exists()
    
    def test_check_valid_thread_threshold_with_ambiguous(self):
        """Test threshold calculation includes ambiguous threads in total count."""
        data = {
            'thread_id': ['t1', 't2', 't3', 't4', 't5'],
            'classification': ['valid', 'valid', 'ambiguous', 'valid_no_gt', 'invalid']
        }
        df = pd.DataFrame(data)
        
        stats = check_valid_thread_threshold(df, threshold=0.4)
        
        # 2 valid out of 5 total = 40%
        assert stats['total_dataset_count'] == 5
        assert stats['valid_dataset_count'] == 2
        assert stats['valid_thread_percentage'] == 40.0
        assert stats['status'] == 'pass'  # 40% >= 40% threshold
    
    def test_ambiguous_threads_excluded_from_valid_count(self):
        """Test that ambiguous threads are not counted as valid."""
        data = {
            'thread_id': ['t1', 't2', 't3'],
            'classification': ['valid', 'ambiguous', 'valid_no_gt']
        }
        df = pd.DataFrame(data)
        
        stats = check_valid_thread_threshold(df, threshold=0.6)
        
        # 1 valid out of 3 total = 33.33%
        assert stats['total_dataset_count'] == 3
        assert stats['valid_dataset_count'] == 1
        assert abs(stats['valid_thread_percentage'] - 33.333333) < 0.01
        assert stats['status'] == 'fail'  # 33.33% < 60% threshold

if __name__ == '__main__':
    pytest.main([__file__, '-v'])