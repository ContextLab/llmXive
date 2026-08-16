"""
Integration tests for GitHub API client.
"""
import pytest
import time
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure the project root is in the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.utils.github_client import GitHubClient

@pytest.mark.skip(reason="Requires real API key and network access")
def test_github_client_fetch_repo():
    """Test fetching a real repository."""
    client = GitHubClient(api_key="test_key")
    # This would make a real API call if not skipped
    # repo = client.get_repo("octocat/Hello-World")
    # assert repo is not None
    pass

def test_github_client_retry_logic_on_failure():
    """
    Integration test for GitHub API retry logic.
    Verifies that the client attempts multiple requests before failing
    when the API returns a 503 error.
    """
    client = GitHubClient(api_key="test_key", max_retries=3, retry_delay=0.1)
    
    # Mock the requests.get method to simulate a persistent 503 error
    with patch('code.utils.github_client.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception) as exc_info:
            client._request("GET", "https://api.github.com/repos/test")
        
        # Verify that get was called exactly max_retries + 1 times (initial + retries)
        # Note: The logic usually does initial call + retries, so total calls = max_retries + 1
        # If max_retries=3, we expect 4 calls.
        assert mock_get.call_count == 4
        assert "503" in str(exc_info.value)

def test_github_client_succeeds_after_retry():
    """
    Integration test for GitHub API retry logic.
    Verifies that the client succeeds if the API eventually returns a 200.
    """
    client = GitHubClient(api_key="test_key", max_retries=3, retry_delay=0.1)
    
    call_count = 0
    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        mock_response = MagicMock()
        if call_count < 3:
            mock_response.status_code = 503
        else:
            mock_response.status_code = 200
            mock_response.json.return_value = {"name": "test-repo"}
            mock_response.raise_for_status = MagicMock()
        return mock_response

    with patch('code.utils.github_client.requests.get', side_effect=side_effect):
        result = client._request("GET", "https://api.github.com/repos/test")
        assert result.status_code == 200
        assert result.json() == {"name": "test-repo"}
        assert call_count == 3

def test_github_client_no_retry_on_404():
    """
    Integration test for GitHub API retry logic.
    Verifies that client does NOT retry on 404 (client error).
    """
    client = GitHubClient(api_key="test_key", max_retries=3, retry_delay=0.1)
    
    with patch('code.utils.github_client.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception):
            client._request("GET", "https://api.github.com/repos/test")
        
        # Should only be called once (no retry for 404)
        assert mock_get.call_count == 1