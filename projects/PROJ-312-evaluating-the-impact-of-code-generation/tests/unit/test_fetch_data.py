import pytest
import json
import os
from unittest.mock import patch, MagicMock

# Import the function we are testing (assuming it's in code/fetch_data.py)
# We need to adjust the import path based on the project structure provided
# The prompt says "code/fetch_data.py" exists, so we import from it.
# However, in a standard test setup, we might need to adjust sys.path.
# Given the constraints, we assume the test runs from the project root or code dir.
# Let's assume the test is in tests/unit/ and fetch_data is in code/.
# We will import directly from the module if the path is set up, 
# or mock the dependencies.

# Since we cannot rely on sys.path in this snippet without setup, 
# we will mock the external calls and test the logic.

# Mocking the api_request_with_backoff and logging
import sys
import importlib.util

# Dynamically load fetch_data module to ensure we get the latest code
spec = importlib.util.spec_from_file_location("fetch_data", "code/fetch_data.py")
fetch_data_module = importlib.util.module_from_spec(spec)

# Mock dependencies before loading
sys.modules['utils'] = MagicMock()
sys.modules['logging_config'] = MagicMock()

spec.loader.exec_module(fetch_data_module)

fetch_repos_from_github = fetch_data_module.fetch_repos_from_github

@patch('fetch_data_module.api_request_with_backoff')
def test_fetch_repos_from_github_python(mock_request):
    # Mock response for Python search
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "items": [
            {"full_name": "org/repo1", "stargazers_count": 10000},
            {"full_name": "org/repo2", "stargazers_count": 9000},
        ]
    }
    mock_request.return_value = mock_response

    result = fetch_repos_from_github(top_n=2, languages=["Python"])
    
    assert len(result) == 2
    assert result[0]["name"] == "org/repo1"
    assert result[0]["stars"] == 10000
    assert result[1]["name"] == "org/repo2"
    assert result[1]["stars"] == 9000

@patch('fetch_data_module.api_request_with_backoff')
def test_fetch_repos_from_github_empty(mock_request):
    mock_response = MagicMock()
    mock_response.json.return_value = {"items": []}
    mock_request.return_value = mock_response

    result = fetch_repos_from_github(top_n=2, languages=["Python"])
    assert len(result) == 0

@patch('fetch_data_module.api_request_with_backoff')
def test_fetch_repos_from_github_pagination(mock_request):
    # Simulate two pages of results
    page1 = MagicMock()
    page1.json.return_value = {
        "items": [
            {"full_name": "org/repo1", "stargazers_count": 10000},
            {"full_name": "org/repo2", "stargazers_count": 9000},
        ]
    }
    page2 = MagicMock()
    page2.json.return_value = {
        "items": [
            {"full_name": "org/repo3", "stargazers_count": 8000},
        ]
    }
    
    # Mock side effect to return page1 then page2
    mock_request.side_effect = [page1, page2]

    result = fetch_repos_from_github(top_n=3, languages=["Python"])
    
    assert len(result) == 3
    assert result[2]["name"] == "org/repo3"
    # Verify the second call was made
    assert mock_request.call_count == 2
