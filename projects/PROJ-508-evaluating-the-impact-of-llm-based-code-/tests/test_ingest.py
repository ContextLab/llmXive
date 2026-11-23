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

    def test_copilot_frequency_calculation(self):
        """Test that commit message 'Copilot' frequency is calculated correctly.
        
        This test specifically validates the frequency calculation logic required
        by T019: count occurrences of 'Copilot' in commit messages and calculate
        the percentage relative to total commits.
        """
        pr_data = {
            'review_threads': [],
            'commits': [
                {'commit': {'message': 'Fix bug'}},
                {'commit': {'message': 'Add feature with Copilot assistance'}},
                {'commit': {'message': 'Refactor code'}},
                {'commit': {'message': 'Update docs'}},
                {'commit': {'message': 'Copilot suggested this fix'}}
            ]
        }
        # Total commits: 5
        # Commits with 'Copilot': 2 (indices 1 and 4)
        # Expected frequency: 2/5 = 0.4
        metrics = extract_pr_metrics(pr_data)
        assert 'copilot_frequency' in metrics
        assert abs(metrics['copilot_frequency'] - 0.4) < 0.001

    def test_copilot_frequency_zero(self):
        """Test that Copilot frequency is 0 when no Copilot mentions exist."""
        pr_data = {
            'review_threads': [],
            'commits': [
                {'commit': {'message': 'Fix bug'}},
                {'commit': {'message': 'Add feature'}},
                {'commit': {'message': 'Refactor code'}}
            ]
        }
        metrics = extract_pr_metrics(pr_data)
        assert 'copilot_frequency' in metrics
        assert metrics['copilot_frequency'] == 0.0

    def test_copilot_frequency_one(self):
        """Test that Copilot frequency is 1.0 when all commits mention Copilot."""
        pr_data = {
            'review_threads': [],
            'commits': [
                {'commit': {'message': 'Copilot fix bug'}},
                {'commit': {'message': 'Copilot add feature'}},
                {'commit': {'message': 'Copilot refactor'}}
            ]
        }
        metrics = extract_pr_metrics(pr_data)
        assert 'copilot_frequency' in metrics
        assert metrics['copilot_frequency'] == 1.0

    def test_copilot_case_insensitive(self):
        """Test that Copilot detection is case-insensitive."""
        pr_data = {
            'review_threads': [],
            'commits': [
                {'commit': {'message': 'COPILOT fix bug'}},
                {'commit': {'message': 'copilot add feature'}},
                {'commit': {'message': 'Copilot refactor'}}
            ]
        }
        metrics = extract_pr_metrics(pr_data)
        assert 'copilot_frequency' in metrics
        assert metrics['copilot_frequency'] == 1.0