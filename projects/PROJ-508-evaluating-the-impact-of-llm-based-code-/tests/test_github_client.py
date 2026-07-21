"""
Tests for the GitHub API client (code/utils/github_client.py).
"""
import time
from unittest.mock import Mock, patch

import pytest
import requests

from utils.github_client import GitHubClient


def test_client_initialization(monkeypatch):
    """Test that the client initializes with the correct token."""
    monkeypatch.setenv("GITHUB_TOKEN", "test_token_123")
    client = GitHubClient()
    assert client.token == "test_token_123"


@patch("utils.github_client.requests.get")
def test_fetch_repository_success(mock_get, monkeypatch):
    """Test successful repository fetch."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"name": "test-repo", "language": "Python"}
    mock_get.return_value = mock_response

    monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    client = GitHubClient()

    result = client.fetch_repository("owner", "repo")

    assert result["name"] == "test-repo"
    mock_get.assert_called_once()


@patch("utils.github_client.requests.get")
def test_fetch_repository_retry_logic(mock_get, monkeypatch):
    """Test that the client retries on 403/429 errors."""
    # First two calls fail, third succeeds
    mock_fail = Mock()
    mock_fail.status_code = 429
    mock_fail.headers = {"Retry-After": "1"}

    mock_success = Mock()
    mock_success.status_code = 200
    mock_success.json.return_value = {"name": "retry-repo"}

    mock_get.side_effect = [mock_fail, mock_fail, mock_success]

    monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    client = GitHubClient()

    # Patch the sleep function to speed up tests
    with patch("utils.github_client.time.sleep"):
        result = client.fetch_repository("owner", "retry-repo")

    assert result["name"] == "retry-repo"
    assert mock_get.call_count == 3
