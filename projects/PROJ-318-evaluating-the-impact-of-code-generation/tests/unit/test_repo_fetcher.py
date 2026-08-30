"""
Unit tests for the Repo Fetcher module.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from utils.repo_fetcher import (
    fetch_package_info,
    extract_github_url,
    fetch_top_repos_from_pypi,
    fetch_fallback_repos,
    validate_repo_list_schema,
    create_repo_list_file,
    RepoFetcherException
)

def test_extract_github_url_priority():
    """Test that GitHub URL is extracted with correct priority."""
    # Test Source Code priority
    data = {
        "info": {
            "project_urls": {
                "Source Code": "https://github.com/user/repo",
                "Homepage": "https://example.com"
            }
        }
    }
    assert extract_github_url(data) == "https://github.com/user/repo"

    # Test Repository priority when Source Code missing
    data = {
        "info": {
            "project_urls": {
                "Repository": "https://github.com/user/repo2",
                "Homepage": "https://example.com"
            }
        }
    }
    assert extract_github_url(data) == "https://github.com/user/repo2"

    # Test Homepage fallback
    data = {
        "info": {
            "project_urls": {
                "Homepage": "https://github.com/user/repo3"
            },
            "home_page": "https://example.com"
        }
    }
    assert extract_github_url(data) == "https://github.com/user/repo3"

    # Test no GitHub URL
    data = {
        "info": {
            "project_urls": {
                "Homepage": "https://example.com"
            }
        }
    }
    assert extract_github_url(data) is None

def test_validate_repo_list_schema_valid():
    """Test validation with valid data."""
    valid_repos = [
        {"repo_url": "https://pypi.org/project/req", "github_url": "https://github.com/u/r", "star_count": 100},
        {"repo_url": "https://pypi.org/project/req2", "github_url": "https://github.com/u/r2", "star_count": 200}
    ]
    assert validate_repo_list_schema(valid_repos) is True

def test_validate_repo_list_schema_missing_field():
    """Test validation with missing required field."""
    invalid_repos = [
        {"repo_url": "https://pypi.org/project/req", "star_count": 100} # Missing github_url
    ]
    assert validate_repo_list_schema(invalid_repos) is False

def test_validate_repo_list_schema_invalid_star_count():
    """Test validation with invalid star_count type."""
    invalid_repos = [
        {"repo_url": "https://pypi.org/project/req", "github_url": "https://github.com/u/r", "star_count": "many"}
    ]
    assert validate_repo_list_schema(invalid_repos) is False

def test_create_repo_list_file():
    """Test creation of the repo list file."""
    repos = [
        {"repo_url": "https://pypi.org/project/req", "github_url": "https://github.com/u/r", "star_count": 100}
    ]
    output_path = Path("data/raw/test_repo_list.json")
    try:
        result_path = create_repo_list_file(repos, output_path)
        assert result_path.exists()
        with open(result_path, 'r') as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["github_url"] == "https://github.com/u/r"
    finally:
        if output_path.exists():
            output_path.unlink()

@patch('utils.repo_fetcher.fetch_package_info')
@patch('utils.repo_fetcher.requests.get')
def test_fetch_top_repos_from_pypi_mocks(mock_get, mock_fetch_info):
    """Test fetching top repos with mocked network calls."""
    # Mock fetch_package_info to return a dummy dict
    mock_fetch_info.return_value = {
        "info": {
            "project_urls": {"Source Code": "https://github.com/test/repo"},
            "name": "test_pkg"
        }
    }
    # Mock GitHub API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"stargazers_count": 1000}
    mock_get.return_value = mock_response

    # This test might be complex due to the list iteration, so we just ensure it runs without error
    # and returns a list of dicts.
    # We limit the list to 1 item for speed in test
    with patch('utils.repo_fetcher.popular_packages', ['test_pkg']):
        repos = fetch_top_repos_from_pypi()
        assert isinstance(repos, list)
        assert len(repos) == 1
        assert "github_url" in repos[0]
        assert "star_count" in repos[0]

def test_fetch_fallback_repos():
    """Test fallback repo fetching returns correct structure."""
    repos = fetch_fallback_repos()
    assert isinstance(repos, list)
    assert len(repos) > 0
    for repo in repos:
        assert "repo_url" in repo
        assert "github_url" in repo
        assert "star_count" in repo
        assert isinstance(repo["star_count"], int)
