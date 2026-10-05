import pytest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from fetch_repos import fetch_repos_from_github, TARGET_COUNT

@pytest.fixture
def mock_response_data():
    return {
        "items": [
            {"full_name": f"test/repo-{i}", "stargazers_count": 10000 - i}
            for i in range(10)
        ]
    }

@patch('fetch_repos.api_request_with_backoff')
def test_fetch_repos_success(mock_api_call, mock_response_data):
    """Test that fetch_repos_from_github correctly parses and limits results."""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.status_code = 200
    mock_api_call.return_value = mock_response

    # Request 5 repos, but mock only provides 10 per page
    result = fetch_repos_from_github("Test", "test_query", target_count=5)

    assert len(result) == 5
    assert result[0]["name"] == "test/repo-0"
    assert result[0]["stars"] == 10000
    assert "stars" in result[0]

@patch('fetch_repos.api_request_with_backoff')
def test_fetch_repos_pagination(mock_api_call, mock_response_data):
    """Test that pagination logic works when target count > per_page."""
    # Mock response for page 1
    page1_data = mock_response_data
    # Mock response for page 2 (different items)
    page2_data = {
        "items": [
            {"full_name": f"test/repo-page2-{i}", "stargazers_count": 5000 - i}
            for i in range(10)
        ]
    }

    mock_response1 = MagicMock()
    mock_response1.json.return_value = page1_data
    mock_response1.status_code = 200

    mock_response2 = MagicMock()
    mock_response2.json.return_value = page2_data
    mock_response2.status_code = 200

    # Return page 1 first, then page 2
    mock_api_call.side_effect = [mock_response1, mock_response2]

    # Request 15 repos (need 2 pages)
    result = fetch_repos_from_github("Test", "test_query", target_count=15)

    assert len(result) == 15
    assert "repo-page2-0" in result[10]["name"]
    assert mock_api_call.call_count == 2

@patch('fetch_repos.api_request_with_github')
def test_fetch_repos_empty_response(mock_api_call):
    """Test handling of empty API response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"items": []}
    mock_response.status_code = 200
    mock_api_call.return_value = mock_response

    result = fetch_repos_from_github("Test", "test_query", target_count=5)

    assert len(result) == 0
    mock_api_call.assert_called_once()