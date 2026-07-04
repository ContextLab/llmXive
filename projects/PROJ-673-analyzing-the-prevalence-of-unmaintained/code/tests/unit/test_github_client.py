"""
Unit tests for the GithubClient module.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from src.services.github_client import GithubClient


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "GITHUB_TOKEN": "test_token_123",
        "RATE_LIMIT": 100
    }


@pytest.fixture
def client(mock_config):
    """Create a GithubClient instance with mocked config."""
    with patch('src.services.github_client.get_config', return_value=mock_config):
        return GithubClient()


def test_client_initialization(client):
    """Test that client initializes with correct headers."""
    assert client.token == "test_token_123"
    assert client.rate_limit == 100
    assert "Authorization" in client.session.headers


@patch('src.services.github_client.requests.Session')
def test_get_commit_date_success(mock_session, client):
    """Test successful retrieval of commit date."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "commit": {
            "committer": {
                "date": "2023-10-15T10:30:00Z"
            }
        }
    }]
    
    mock_session_instance = mock_session.return_value
    mock_session_instance.get.return_value = mock_response
    
    result = client.get_commit_date("owner", "repo")
    
    assert result is not None
    assert result.year == 2023
    assert result.month == 10
    assert result.day == 15


@patch('src.services.github_client.requests.Session')
def test_get_commit_date_not_found(mock_session, client):
    """Test handling of 404 response."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    
    mock_session_instance = mock_session.return_value
    mock_session_instance.get.return_value = mock_response
    
    result = client.get_commit_date("owner", "nonexistent")
    
    assert result is None


@patch('src.services.github_client.requests.Session')
def test_get_release_date_success(mock_session, client):
    """Test successful retrieval of release date."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "published_at": "2023-09-20T14:45:00Z"
    }]
    
    mock_session_instance = mock_session.return_value
    mock_session_instance.get.return_value = mock_response
    
    result = client.get_release_date("owner", "repo")
    
    assert result is not None
    assert result.year == 2023
    assert result.month == 9
    assert result.day == 20


@patch('src.services.github_client.requests.Session')
def test_get_release_date_empty(mock_session, client):
    """Test handling of empty releases list."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    
    mock_session_instance = mock_session.return_value
    mock_session_instance.get.return_value = mock_response
    
    result = client.get_release_date("owner", "repo")
    
    assert result is None


@patch('src.services.github_client.requests.Session')
def test_fetch_repository_metadata(mock_session, client):
    """Test fetching both commit and release dates."""
    # Mock commit response
    mock_commit_response = MagicMock()
    mock_commit_response.status_code = 200
    mock_commit_response.json.return_value = [{
        "commit": {
            "committer": {
                "date": "2023-10-15T10:30:00Z"
            }
        }
    }]
    
    # Mock release response
    mock_release_response = MagicMock()
    mock_release_response.status_code = 200
    mock_release_response.json.return_value = [{
        "published_at": "2023-09-20T14:45:00Z"
    }]
    
    mock_session_instance = mock_session.return_value
    mock_session_instance.get.side_effect = [mock_commit_response, mock_release_response]
    
    result = client.fetch_repository_metadata("owner/repo")
    
    assert "last_commit_date" in result
    assert "last_release_date" in result
    assert result["last_commit_date"] is not None
    assert result["last_release_date"] is not None


@patch('src.services.github_client.requests.Session')
def test_fetch_repository_metadata_invalid_name(mock_session, client):
    """Test handling of invalid repository name."""
    result = client.fetch_repository_metadata("invalid_name")
    
    assert result["last_commit_date"] is None
    assert result["last_release_date"] is None


def test_parse_date_invalid(client):
    """Test parsing of invalid date strings."""
    assert client._parse_date(None) is None
    assert client._parse_date("") is None
    assert client._parse_date("not-a-date") is None


def test_parse_date_valid(client):
    """Test parsing of valid date strings."""
    result = client._parse_date("2023-10-15T10:30:00Z")
    assert result is not None
    assert result.year == 2023
    assert result.month == 10
    assert result.day == 15
