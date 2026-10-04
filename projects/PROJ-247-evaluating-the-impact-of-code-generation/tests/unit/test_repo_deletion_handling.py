"""
Unit tests for repo deletion handling in 02_metric_edge_case_handler.py
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import csv
import tempfile
import os
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, 'code')

from code_02_metric_edge_case_handler import handle_repo_deletion, save_exclusions_log, LOG_PATH, REPO_DELETION_LOG
from utils.github_client import RepositoryNotFoundError

class TestRepoDeletionHandling(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_github_client = Mock()
        self.temp_dir = tempfile.mkdtemp()
        self.test_log_path = Path(self.temp_dir) / "test_repo_deletion.log"
        
        # Sample metrics data
        self.metrics_data = [
            {'block_id': '1', 'repo_name': 'valid/repo1', 'latency_days': '10'},
            {'block_id': '2', 'repo_name': 'deleted/repo2', 'latency_days': '5'},
            {'block_id': '3', 'repo_name': 'valid/repo3', 'latency_days': '20'},
            {'block_id': '4', 'repo_name': 'private/repo4', 'latency_days': '15'},
        ]
    
    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.test_log_path):
            os.remove(self.test_log_path)
    
    @patch('code_02_metric_edge_case_handler.GitHubClient')
    def test_handle_repo_deletion_removes_deleted_repos(self, mock_client_class):
        """Test that deleted repos are removed from metrics."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Setup mock responses
        def get_repo_info_side_effect(repo_name):
            if repo_name in ['valid/repo1', 'valid/repo3']:
                return {'name': repo_name, 'status': 'active'}
            elif repo_name in ['deleted/repo2', 'private/repo4']:
                raise RepositoryNotFoundError(f"Repo {repo_name} not found")
            return None
        
        mock_client.get_repo_info.side_effect = get_repo_info_side_effect
        
        # Run function
        result = handle_repo_deletion(self.metrics_data, mock_client)
        
        # Assertions
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['block_id'], '1')
        self.assertEqual(result[1]['block_id'], '3')
        
        # Verify log file was created
        self.assertTrue(self.test_log_path.exists())
        
        # Verify log content
        with open(self.test_log_path, 'r') as f:
            log_content = f.read()
            self.assertIn('deleted/repo2', log_content)
            self.assertIn('private/repo4', log_content)
            self.assertIn('Repository not found', log_content)
    
    def test_handle_repo_deletion_keeps_valid_repos(self):
        """Test that valid repos are kept in metrics."""
        mock_client = Mock()
        
        def get_repo_info_side_effect(repo_name):
            return {'name': repo_name, 'status': 'active'}
        
        mock_client.get_repo_info.side_effect = get_repo_info_side_effect
        
        result = handle_repo_deletion(self.metrics_data, mock_client)
        
        self.assertEqual(len(result), 4)
        # All original block_ids should be present
        block_ids = [r['block_id'] for r in result]
        self.assertEqual(set(block_ids), {'1', '2', '3', '4'})
    
    def test_handle_repo_deletion_handles_missing_repo_name(self):
        """Test handling of metrics with missing repo_name."""
        metrics_with_missing = self.metrics_data + [
            {'block_id': '5', 'repo_name': None, 'latency_days': '30'},
            {'block_id': '6', 'repo_name': '', 'latency_days': '25'},
        ]
        
        mock_client = Mock()
        
        def get_repo_info_side_effect(repo_name):
            return {'name': repo_name, 'status': 'active'}
        
        mock_client.get_repo_info.side_effect = get_repo_info_side_effect
        
        result = handle_repo_deletion(metrics_with_missing, mock_client)
        
        # Metrics with missing repo_name should be kept
        self.assertEqual(len(result), 6)
        block_ids = [r['block_id'] for r in result]
        self.assertIn('5', block_ids)
        self.assertIn('6', block_ids)
    
    def test_save_exclusions_log_creates_file(self):
        """Test that exclusions log is created with correct format."""
        entries = [
            {'repo_name': 'test/repo1', 'reason': 'Not found', 'timestamp': '2023-01-01 12:00:00'},
            {'repo_name': 'test/repo2', 'reason': 'Private', 'timestamp': '2023-01-01 12:01:00'},
        ]
        
        save_exclusions_log(self.test_log_path, entries)
        
        self.assertTrue(self.test_log_path.exists())
        
        with open(self.test_log_path, 'r') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 2)
            self.assertIn('test/repo1', lines[0])
            self.assertIn('Not found', lines[0])
            self.assertIn('test/repo2', lines[1])
            self.assertIn('Private', lines[1])

if __name__ == '__main__':
    unittest.main()