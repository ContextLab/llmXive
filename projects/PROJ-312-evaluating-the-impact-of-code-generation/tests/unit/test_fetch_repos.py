import pytest
from unittest.mock import patch, MagicMock
import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from fetch_repos import fetch_repos_from_github

@patch('fetch_repos.api_request_with_backoff')
@patch('fetch_repos.log_api_headers')
def test_fetch_repos_success(mock_log, mock_request):
    """Test successful fetching of repositories"""
    # Mock response data
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {"full_name": "test/repo1", "stargazers_count": 50000},
            {"full_name": "test/repo2", "stargazers_count": 45000}
        ]
    }
    mock_request.return_value = mock_response
    
    # Set token for test
    with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
        repos = fetch_repos_from_github("Python", min_stars=10000, limit=5)
    
    assert len(repos) == 2
    assert repos[0]["name"] == "test/repo1"
    assert repos[0]["stars"] == 50000
    assert repos[1]["name"] == "test/repo2"
    assert repos[1]["stars"] == 45000

@patch('fetch_repos.api_request_with_backoff')
@patch('fetch_repos.log_api_headers')
def test_fetch_repos_empty_response(mock_log, mock_request):
    """Test handling of empty API response"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": []}
    mock_request.return_value = mock_response
    
    with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
        repos = fetch_repos_from_github("Python", min_stars=10000, limit=5)
    
    assert len(repos) == 0

@patch('fetch_repos.api_request_with_backoff')
@patch('fetch_repos.log_api_headers')
def test_fetch_repos_limit(mock_log, mock_request):
    """Test that limit parameter works correctly"""
    # Create enough items to exceed limit
    items = [
        {"full_name": f"test/repo{i}", "stargazers_count": 50000 - i}
        for i in range(10)
    ]
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": items}
    mock_request.return_value = mock_response
    
    with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
        repos = fetch_repos_from_github("Python", min_stars=10000, limit=3)
    
    assert len(repos) == 3

def test_missing_token():
    """Test that missing GITHUB_TOKEN raises error"""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError, match="GITHUB_TOKEN environment variable is not set"):
            fetch_repos_from_github("Python")
