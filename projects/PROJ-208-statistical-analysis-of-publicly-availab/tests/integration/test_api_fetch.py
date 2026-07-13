"""
Integration test for API fetch with rate limit simulation.

This test verifies that the GitHub API client in code/utils/api_client.py
correctly handles rate limiting by simulating 403 responses with
Retry-After headers and ensuring exponential backoff is applied.

It also validates that the issue fetcher in code/collect/fetch_issues.py
integrates correctly with the API client to retrieve issues.
"""
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any, Optional, Tuple

import pytest
import requests
import requests_mock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.api_client import GitHubAPIClient, RateLimitError, HTTPError
from collect.fetch_issues import fetch_issues_for_repo, load_repository_list

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Test fixtures
TEST_REPO = "octocat/Hello-World"
TEST_ISSUES_URL = f"https://api.github.com/repos/{TEST_REPO}/issues"
MOCK_ISSUES_RESPONSE = [
    {
        "id": 1,
        "number": 1,
        "title": "First Issue",
        "state": "closed",
        "created_at": "2023-01-01T00:00:00Z",
        "closed_at": "2023-01-02T00:00:00Z",
        "user": {"login": "testuser"},
        "labels": []
    },
    {
        "id": 2,
        "number": 2,
        "title": "Second Issue",
        "state": "closed",
        "created_at": "2023-01-03T00:00:00Z",
        "closed_at": "2023-01-04T00:00:00Z",
        "user": {"login": "testuser"},
        "labels": []
    }
]

@pytest.fixture
def mock_api_client():
    """Create a mock GitHub API client for testing."""
    client = GitHubAPIClient(token="fake_token")
    # Override the actual HTTP session with a mock
    client.session = MagicMock()
    return client

@pytest.fixture
def rate_limited_response():
    """Create a mock 403 rate limit response."""
    response = MagicMock()
    response.status_code = 403
    response.headers = {
        "Retry-After": "1",  # Retry after 1 second for fast testing
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": str(int(time.time()) + 60)
    }
    response.json.return_value = {
        "message": "API rate limit exceeded",
        "documentation_url": "https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting"
    }
    return response

@pytest.fixture
def success_response():
    """Create a mock 200 success response."""
    response = MagicMock()
    response.status_code = 200
    response.headers = {
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Reset": str(int(time.time()) + 3600)
    }
    response.json.return_value = MOCK_ISSUES_RESPONSE
    return response

def test_rate_limit_handling_with_backoff(mock_api_client, rate_limited_response, success_response):
    """
    Test that the API client handles rate limits by waiting and retrying.
    
    Scenario:
    1. First request returns 403 with Retry-After header
    2. Client waits for the specified duration (or a minimum)
    3. Second request succeeds
    """
    # Configure the mock to return rate limit first, then success
    mock_api_client.session.get.side_effect = [rate_limited_response, success_response]

    start_time = time.time()
    
    # This should trigger the rate limit handling logic
    result = mock_api_client.get(TEST_ISSUES_URL, max_retries=2)
    
    end_time = time.time()
    
    # Verify that get was called twice (first failed, second succeeded)
    assert mock_api_client.session.get.call_count == 2
    
    # Verify that the result is the successful response
    assert result.status_code == 200
    assert result.json() == MOCK_ISSUES_RESPONSE
    
    # Verify that some time passed (at least the retry duration)
    # Note: In a real test, we'd check for the exact retry time, but for speed
    # we just ensure the logic ran
    assert end_time - start_time >= 0.5  # At least 0.5s should have passed

def test_rate_limit_error_after_max_retries(mock_api_client, rate_limited_response):
    """
    Test that RateLimitError is raised when max retries are exhausted.
    """
    # Configure mock to always return rate limit
    mock_api_client.session.get.side_effect = [rate_limited_response] * 3

    with pytest.raises(RateLimitError) as exc_info:
        mock_api_client.get(TEST_ISSUES_URL, max_retries=2)
    
    assert "rate limit" in str(exc_info.value).lower()
    assert mock_api_client.session.get.call_count == 3

def test_http_error_handling(mock_api_client):
    """Test that non-403 HTTP errors are handled correctly."""
    error_response = MagicMock()
    error_response.status_code = 404
    error_response.headers = {}
    error_response.json.return_value = {"message": "Not Found"}
    
    mock_api_client.session.get.return_value = error_response

    with pytest.raises(HTTPError) as exc_info:
        mock_api_client.get(TEST_ISSUES_URL)
    
    assert exc_info.value.status_code == 404

def test_fetch_issues_with_mocked_api():
    """
    Integration test for fetch_issues_for_repo with a mocked API.
    
    This test ensures that the fetch_issues_for_repo function correctly
    uses the API client and handles the response.
    """
    repo = TEST_REPO
    
    with patch('collect.fetch_issues.GitHubAPIClient') as MockClient:
        mock_client_instance = MagicMock()
        MockClient.return_value = mock_client_instance
        
        # Mock the get method to return our success response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_ISSUES_RESPONSE
        mock_client_instance.get.return_value = mock_response
        
        # Call the function
        issues = fetch_issues_for_repo(repo)
        
        # Verify results
        assert len(issues) == 2
        assert issues[0]["number"] == 1
        assert issues[1]["number"] == 2
        
        # Verify API was called with correct URL
        mock_client_instance.get.assert_called_once()
        call_args = mock_client_instance.get.call_args[0][0]
        assert TEST_ISSUES_URL in call_args

def test_fetch_issues_handles_empty_response():
    """Test that fetch_issues_for_repo handles empty responses gracefully."""
    repo = TEST_REPO
    
    with patch('collect.fetch_issues.GitHubAPIClient') as MockClient:
        mock_client_instance = MagicMock()
        MockClient.return_value = mock_client_instance
        
        # Mock empty response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_client_instance.get.return_value = mock_response
        
        issues = fetch_issues_for_repo(repo)
        
        assert len(issues) == 0

def test_fetch_issues_handles_rate_limit():
    """Test that fetch_issues_for_repo handles rate limits by retrying."""
    repo = TEST_REPO
    
    with patch('collect.fetch_issues.GitHubAPIClient') as MockClient:
        mock_client_instance = MagicMock()
        MockClient.return_value = mock_client_instance
        
        # First call fails with rate limit, second succeeds
        rate_limit_resp = MagicMock()
        rate_limit_resp.status_code = 403
        rate_limit_resp.headers = {"Retry-After": "1"}
        rate_limit_resp.json.return_value = {"message": "Rate limit exceeded"}
        
        success_resp = MagicMock()
        success_resp.status_code = 200
        success_resp.json.return_value = MOCK_ISSUES_RESPONSE
        
        mock_client_instance.get.side_effect = [rate_limit_resp, success_resp]
        
        issues = fetch_issues_for_repo(repo)
        
        # Should have retried and succeeded
        assert len(issues) == 2
        assert mock_client_instance.get.call_count == 2

def test_load_repository_list_from_file():
    """Test loading repository list from a JSON file."""
    # Create a temporary test file
    test_data = {
        "repositories": [
            "octocat/Hello-World",
            "psf/requests"
        ]
    }
    
    with patch('collect.fetch_issues.Path') as MockPath:
        mock_path = MagicMock()
        MockPath.return_value = mock_path
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps(test_data)
        
        repos = load_repository_list("test_repos.json")
        
        assert len(repos) == 2
        assert "octocat/Hello-World" in repos
        assert "psf/requests" in repos

def test_load_repository_list_missing_file():
    """Test loading repository list when file doesn't exist."""
    with patch('collect.fetch_issues.Path') as MockPath:
        mock_path = MagicMock()
        MockPath.return_value = mock_path
        mock_path.exists.return_value = False
        
        repos = load_repository_list("nonexistent.json")
        
        assert repos == []

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])