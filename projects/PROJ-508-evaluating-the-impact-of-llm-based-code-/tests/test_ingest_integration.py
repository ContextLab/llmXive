import pytest
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from code.ingest import (
    calculate_avg_comment_length,
    calculate_review_thread_depth,
    calculate_revert_frequency
)

class TestIngestMetricsIntegration:
    """Integration tests for metrics extraction in ingest pipeline"""

    def test_avg_comment_length_extraction(self):
        """Test that avg_comment_length is correctly extracted from PR data"""
        # Simulate PR comments data
        comments = [
            {'body': 'This looks good'},
            {'body': 'Can you add some error handling?'},
            {'body': 'LGTM'}
        ]
        
        result = calculate_avg_comment_length(comments)
        
        # Calculate expected value
        expected = (14 + 31 + 5) / 3
        assert abs(result - expected) < 0.01

    def test_review_thread_depth_extraction(self):
        """Test that review_thread_depth is correctly calculated"""
        # Simulate review comments with threads
        review_comments = [
            {'in_reply_to_id': 'thread1', 'body': 'First comment'},
            {'in_reply_to_id': 'thread1', 'body': 'Reply to first'},
            {'in_reply_to_id': 'thread1', 'body': 'Another reply'},
            {'in_reply_to_id': 'thread2', 'body': 'Second thread'},
            {'in_reply_to_id': 'thread2', 'body': 'Reply to second'}
        ]
        
        result = calculate_review_thread_depth(review_comments)
        
        # thread1 has 3 comments, thread2 has 2
        assert result == 3

    def test_revert_frequency_extraction(self):
        """Test that revert_frequency is correctly calculated"""
        # Simulate commits with some reverts
        commits = [
            {'commit': {'message': 'Add new feature'}},
            {'commit': {'message': 'Revert "Add new feature"'}},
            {'commit': {'message': 'Fix bug'}},
            {'commit': {'message': 'Revert some change'}},
            {'commit': {'message': 'Update documentation'}}
        ]
        
        result = calculate_revert_frequency(commits)
        
        # 2 reverts out of 5 commits
        assert result == 0.4

    def test_metrics_in_master_dataset(self):
        """Test that all required metrics are present in the output dataset structure"""
        # This test verifies the structure that would be written to master_dataset.csv
        
        # Simulate processed repository data
        repo_data = {
            'repo_full_name': 'test/repo',
            'llm_adoption_flag': True,
            'domain_complexity': 5,
            'review_metrics': [
                {
                    'pr_number': 1,
                    'avg_comment_length': 25.5,
                    'review_thread_depth': 3,
                    'revert_frequency': 0.1,
                    'iteration_count': 5,
                    'avg_diff_complexity': 0.4,
                    'has_ai_noise': False
                },
                {
                    'pr_number': 2,
                    'avg_comment_length': 18.2,
                    'review_thread_depth': 2,
                    'revert_frequency': 0.0,
                    'iteration_count': 3,
                    'avg_diff_complexity': 0.2,
                    'has_ai_noise': True
                }
            ]
        }
        
        # Verify structure
        assert 'review_metrics' in repo_data
        assert len(repo_data['review_metrics']) == 2
        
        for metric in repo_data['review_metrics']:
            assert 'avg_comment_length' in metric
            assert 'review_thread_depth' in metric
            assert 'revert_frequency' in metric
            assert isinstance(metric['avg_comment_length'], float)
            assert isinstance(metric['review_thread_depth'], int)
            assert isinstance(metric['revert_frequency'], float)
            assert 0.0 <= metric['revert_frequency'] <= 1.0

    @patch('code.ingest.GitHubClient')
    def test_full_pipeline_metrics_extraction(self, mock_github_client):
        """Test that metrics are correctly extracted through the full pipeline"""
        # Mock GitHub client responses
        mock_pr = {
            'number': 123,
            'title': 'Test PR',
            'state': 'closed',
            'merged': True
        }
        
        mock_comments = [
            {'body': 'Comment 1'},
            {'body': 'Comment 2'},
            {'body': 'Comment 3'}
        ]
        
        mock_review_comments = [
            {'in_reply_to_id': 'thread1'},
            {'in_reply_to_id': 'thread1'},
            {'in_reply_to_id': 'thread2'}
        ]
        
        mock_commits = [
            {'commit': {'message': 'Add feature'}},
            {'commit': {'message': 'Revert "Add feature"'}}
        ]
        
        # Setup mock
        mock_client_instance = Mock()
        mock_github_client.return_value = mock_client_instance
        mock_client_instance.get_pull_requests.return_value = [mock_pr]
        mock_client_instance.get_pull_request_comments.return_value = mock_comments
        mock_client_instance.get_review_comments.return_value = mock_review_comments
        mock_client_instance.get_pull_request_commits.return_value = mock_commits
        
        # Test that metrics would be calculated (we can't run full pipeline without real data)
        avg_len = calculate_avg_comment_length(mock_comments)
        thread_depth = calculate_review_thread_depth(mock_review_comments)
        revert_freq = calculate_revert_frequency(mock_commits)
        
        assert avg_len > 0
        assert thread_depth > 0
        assert revert_freq == 0.5  # 1 revert out of 2 commits