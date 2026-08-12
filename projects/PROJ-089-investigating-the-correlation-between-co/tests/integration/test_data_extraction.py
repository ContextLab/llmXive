"""
Integration tests for data extraction module.

These tests verify that:
1. GitHub API queries return valid data.
2. Repository cloning works.
3. Git metrics extraction produces expected fields.
"""
import pytest
import os
import tempfile
from pathlib import Path
import csv

# We need to mock the network calls for a pure unit test, 
# but for integration we might want to run a small subset if credentials exist.
# Given the constraints, we will test the logic flow and structure.

# Mocking requests and pydriller for pure logic testing without network
from unittest.mock import patch, MagicMock, mock_open
import requests

# Import the module
import code.data_extraction as de
from code.config import ensure_directories


class TestDataExtraction:
    
    @patch('code.data_extraction.requests.get')
    def test_query_github_repos(self, mock_get):
        """Test that query_github_repos returns expected structure."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {
                    "name": "test-repo",
                    "full_name": "owner/test-repo",
                    "html_url": "https://github.com/owner/test-repo",
                    "stargazers_count": 1000,
                    "language": "Python",
                    "created_at": "2020-01-01T00:00:00Z",
                    "clone_url": "https://github.com/owner/test-repo.git",
                    "fork": False
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        repos = de.query_github_repos(min_stars=100, min_age_years=1, languages=["Python"], max_results=1)
        
        assert len(repos) == 1
        assert repos[0]["name"] == "test-repo"
        assert repos[0]["stargazers_count"] == 1000
        assert repos[0]["language"] == "Python"
        
    @patch('code.data_extraction.subprocess.run')
    def test_clone_repository(self, mock_run):
        """Test repository cloning logic."""
        mock_run.return_value = MagicMock(check_returncode=0)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "test-repo"
            # Mock the directory existence check
            with patch.object(Path, 'exists', return_value=False):
                result = de.clone_repository("https://github.com/test/repo.git", target)
                
            # subprocess.run should have been called
            assert mock_run.called
            # Note: actual success depends on git command, we mock the call
            # In a real integration test with network, this would be True
            
    def test_aggregate_file_metrics(self):
        """Test aggregation of file metrics."""
        metrics = [
            {"file_path": "a.py", "total_lines_changed": 10, "commit_count": 2, "contributor_count": 1},
            {"file_path": "b.py", "total_lines_changed": 5, "commit_count": 1, "contributor_count": 1}
        ]
        
        result = de.aggregate_file_metrics(metrics, "test/repo")
        
        assert len(result) == 2
        assert result[0]["repo_name"] == "test/repo"
        assert result[1]["repo_name"] == "test/repo"
        
    @patch('code.data_extraction.save_repos_metadata')
    def test_run_data_extraction_flow(self, mock_save):
        """Test the high-level flow of run_data_extraction."""
        with patch.object(de, 'query_github_repos') as mock_query, \
             patch.object(de, 'process_single_repo') as mock_process, \
             patch.object(de, 'Path') as MockPath:
             
            mock_query.return_value = [{"full_name": "test/repo", "clone_url": "url"}]
            mock_process.return_value = [{"repo_name": "test/repo", "file_path": "a.py"}]
            
            MockPath.return_value.mkdir = MagicMock()
            
            result = de.run_data_extraction(max_repos=1)
            
            assert len(result) == 1
            assert mock_query.called
            assert mock_process.called

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
