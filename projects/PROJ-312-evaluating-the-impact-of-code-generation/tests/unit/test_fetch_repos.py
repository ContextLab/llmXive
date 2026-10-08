"""
Unit tests for fetch_repos module.
Tests T012a logic: fetching repos and saving to JSON.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module to test
# We need to adjust the import path if running from tests/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from fetch_repos import fetch_repos_from_github, main, REPO_LIMIT

@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    mock = MagicMock()
    return mock

@patch('fetch_repos.api_request_with_backoff')
def test_fetch_repos_from_github_success(mock_request, mock_logger):
    """Test successful fetching of repositories."""
    # Mock response data
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {"full_name": "repo1/repo1", "stargazers_count": 10000},
            {"full_name": "repo2/repo2", "stargazers_count": 9000}
        ]
    }
    mock_request.return_value = mock_response

    repos = fetch_repos_from_github("test=query", "TestLang", mock_logger)

    assert len(repos) == 2
    assert repos[0]["name"] == "repo1/repo1"
    assert repos[0]["stars"] == 10000
    assert mock_logger.info.called

@patch('fetch_repos.api_request_with_backoff')
def test_fetch_repos_handles_empty_response(mock_request, mock_logger):
    """Test handling of empty response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": []}
    mock_request.return_value = mock_response

    repos = fetch_repos_from_github("test=query", "TestLang", mock_logger)

    assert len(repos) == 0
    mock_logger.info.assert_any_call("No more items found.")

@patch('fetch_repos.api_request_with_backoff')
def test_fetch_repos_stops_at_limit(mock_request, mock_logger):
    """Test that fetching stops at REPO_LIMIT."""
    # Create enough items to exceed the limit
    items = [{"full_name": f"repo{i}/repo{i}", "stargazers_count": 10000} for i in range(REPO_LIMIT + 10)]
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": items}
    mock_request.return_value = mock_response

    repos = fetch_repos_from_github("test=query", "TestLang", mock_logger)

    assert len(repos) == REPO_LIMIT
    assert mock_logger.info.called

@patch('fetch_repos.api_request_with_backoff')
def test_fetch_repos_handles_error(mock_request, mock_logger):
    """Test handling of API error."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_request.return_value = mock_response

    repos = fetch_repos_from_github("test=query", "TestLang", mock_logger)

    assert len(repos) == 0
    mock_logger.error.assert_called()

def test_main_creates_output_file():
    """Test that main() creates the output JSON file."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "data" / "raw" / "repos.json"
        
        # Patch the OUTPUT_PATH in the module
        with patch('fetch_repos.OUTPUT_PATH', output_path):
            # Mock the fetch functions to return empty lists to avoid real API calls
            with patch('fetch_repos.fetch_repos_from_github') as mock_fetch:
                mock_fetch.return_value = []
                
                # Run main
                main()
                
                # Check if file was created
                assert output_path.exists()
                
                # Check content
                with open(output_path, 'r') as f:
                    data = json.load(f)
                    assert data == []
