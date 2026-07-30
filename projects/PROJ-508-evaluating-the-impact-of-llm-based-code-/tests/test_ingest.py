import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest import extract_pr_metrics
from utils.metrics import calculate_avg_comment_length, calculate_review_thread_depth, calculate_revert_frequency

class TestExtractPRMetrics:
    def test_avg_comment_length_calculation(self):
        """Test that average comment length is calculated correctly."""
        pr_data = {
            'review_threads': [
                {'body': 'Short'},
                {'body': 'This is a much longer comment body for testing purposes.'}
            ],
            'commits': []
        }
        metrics = extract_pr_metrics(pr_data)
        
        expected_avg = (5 + 52) / 2
        assert abs(metrics['avg_comment_length'] - expected_avg) < 0.001
        assert metrics['review_thread_depth'] == 2

    def test_review_thread_depth_count(self):
        """Test that review thread depth counts comments correctly."""
        pr_data = {
            'review_threads': [
                {'body': 'Comment 1'},
                {'body': 'Comment 2'},
                {'body': 'Comment 3'}
            ],
            'commits': []
        }
        metrics = extract_pr_metrics(pr_data)
        assert metrics['review_thread_depth'] == 3

    def test_revert_frequency_detection(self):
        """Test that revert frequency detects 'revert' in commit messages."""
        pr_data = {
            'review_threads': [],
            'commits': [
                {'commit': {'message': 'Fix bug'}},
                {'commit': {'message': 'Revert previous changes'}},
                {'commit': {'message': 'Revert commit abc123'}},
                {'commit': {'message': 'Refactor code'}}
            ]
        }
        metrics = extract_pr_metrics(pr_data)
        assert metrics['revert_frequency'] == 2.0

    def test_empty_pr_data(self):
        """Test handling of empty PR data."""
        pr_data = {
            'review_threads': [],
            'commits': []
        }
        metrics = extract_pr_metrics(pr_data)
        assert metrics['avg_comment_length'] == 0.0
        assert metrics['review_thread_depth'] == 0
        assert metrics['revert_frequency'] == 0.0

    def test_case_insensitive_revert(self):
        """Test that revert detection is case-insensitive."""
        pr_data = {
            'review_threads': [],
            'commits': [
                {'commit': {'message': 'REVERT all changes'}},
                {'commit': {'message': 'Revert single line'}},
                {'commit': {'message': 'revert this'}}
            ]
        }
        metrics = extract_pr_metrics(pr_data)
        assert metrics['revert_frequency'] == 3.0
