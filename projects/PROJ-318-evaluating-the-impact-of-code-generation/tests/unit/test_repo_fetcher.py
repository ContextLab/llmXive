"""
Unit tests for the repo_fetcher module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module
# Adjust import path based on project structure
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.repo_fetcher import (
    fetch_github_stars,
    fetch_top_repos_from_pypi,
    validate_repo_list_schema,
    create_repo_list_file,
    main,
    TARGET_COUNT,
    UNIQUE_TOP_PACKAGES
)
from utils.exceptions import RepoFetcherException

def test_validate_repo_list_schema_valid():
    """Test schema validation with valid data."""
    repos = [
        {"repo_url": "https://pypi.org/project/requests/", "github_url": "https://github.com/requests/requests", "star_count": 50000},
        {"repo_url": "https://pypi.org/project/pandas/", "github_url": "https://github.com/pandas-dev/pandas", "star_count": 40000}
    ]
    assert validate_repo_list_schema(repos) is True

def test_validate_repo_list_schema_invalid_missing_field():
    """Test schema validation with missing field."""
    repos = [
        {"repo_url": "https://pypi.org/project/requests/", "github_url": "https://github.com/requests/requests"}
    ]
    assert validate_repo_list_schema(repos) is False

def test_validate_repo_list_schema_invalid_type():
    """Test schema validation with wrong type for star_count."""
    repos = [
        {"repo_url": "https://pypi.org/project/requests/", "github_url": "https://github.com/requests/requests", "star_count": "50000"}
    ]
    assert validate_repo_list_schema(repos) is False

@patch('utils.repo_fetcher.requests.get')
def test_fetch_github_stars_success(mock_get):
    """Test successful fetch of GitHub stars."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"stargazers_count": 1000}
    mock_get.return_value = mock_response

    stars = fetch_github_stars("owner/repo")
    assert stars == 1000
    mock_get.assert_called_once()

@patch('utils.repo_fetcher.requests.get')
def test_fetch_github_stars_failure(mock_get):
    """Test fetch failure returns None."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    stars = fetch_github_stars("owner/repo")
    assert stars is None

@patch('utils.repo_fetcher.fetch_github_stars')
def test_fetch_top_repos_from_pypi_success(mock_fetch_stars):
    """Test successful fetch of top repos."""
    # Mock the fetch_github_stars to return valid stars for all packages
    mock_fetch_stars.side_effect = lambda x: 1000  # Return 1000 for all

    repos = fetch_top_repos_from_pypi()
    assert len(repos) == TARGET_COUNT
    assert all("repo_url" in r for r in repos)
    assert all("github_url" in r for r in repos)
    assert all("star_count" in r for r in repos)

@patch('utils.repo_fetcher.fetch_github_stars')
def test_fetch_top_repos_from_pypi_failure_too_few(mock_fetch_stars):
    """Test failure when not enough repos are fetched."""
    # Mock to return None for some packages, resulting in fewer than 20
    call_count = 0
    def mock_side_effect(x):
        nonlocal call_count
        call_count += 1
        if call_count < 10:  # Only 10 successful
            return 1000
        return None

    mock_fetch_stars.side_effect = mock_side_effect

    with pytest.raises(RepoFetcherException):
        fetch_top_repos_from_pypi()

def test_create_repo_list_file():
    """Test writing repo list to file."""
    repos = [
        {"repo_url": "https://pypi.org/project/requests/", "github_url": "https://github.com/requests/requests", "star_count": 50000}
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.json"
        create_repo_list_file(repos, output_path)
        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["star_count"] == 50000

@patch('utils.repo_fetcher.fetch_top_repos_from_pypi')
@patch('utils.repo_fetcher.create_repo_list_file')
@patch('builtins.open')
def test_main(mock_open, mock_create, mock_fetch):
    """Test main function execution."""
    mock_fetch.return_value = [
        {"repo_url": "url", "github_url": "gh", "star_count": 100}
    ] * 20
    mock_create.return_value = None

    # Mock Path to avoid actual file system operations
    with patch('utils.repo_fetcher.Path') as mock_path:
        mock_path.return_value.mkdir.return_value = None
        mock_path.return_value.__truediv__.return_value = mock_path.return_value
        mock_path.return_value.parent = mock_path.return_value

        # This would normally write files, but we mock it
        # We just check that the functions are called
        try:
            main()
        except Exception:
            # Expected because of mocking
            pass

        mock_fetch.assert_called_once()
        # The rest is mocked, so we can't test file writing directly in unit test
        # Integration test would be better for file I/O