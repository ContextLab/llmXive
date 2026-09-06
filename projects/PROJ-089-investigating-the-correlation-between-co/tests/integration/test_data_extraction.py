"""
Integration tests for data extraction module.
Tests T010: Query GitHub API and filter repos.
"""
import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

from code.data_extraction import query_github_repos, save_repos_metadata

@pytest.fixture
def mock_github_response():
    """Mock GitHub API response."""
    return {
        "items": [
            {
                "id": 12345,
                "full_name": "test/repo1",
                "html_url": "https://github.com/test/repo1",
                "stargazers_count": 6000,
                "language": "Python",
                "created_at": "2020-01-01T00:00:00Z",
                "default_branch": "main"
            },
            {
                "id": 67890,
                "full_name": "test/repo2",
                "html_url": "https://github.com/test/repo2",
                "stargazers_count": 10000,
                "language": "Java",
                "created_at": "2019-05-15T00:00:00Z",
                "default_branch": "master"
            }
        ]
    }

def test_query_github_repos_filters(mock_github_response):
    """Test that query_github_repos correctly filters by stars and age."""
    with patch('code.data_extraction.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_github_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        repos = query_github_repos(min_stars=500, min_age_years=2, max_results=10)

        assert len(repos) == 2
        assert repos[0]["stargazers_count"] >= 500
        assert repos[1]["stargazers_count"] >= 500
        # Check that repo_id is present
        assert "repo_id" in repos[0]
        assert "repo_id" in repos[1]

def test_save_repos_metadata_creates_file(tmp_path):
    """Test that save_repos_metadata creates a valid CSV."""
    repos = [
        {"repo_id": "1", "full_name": "a/b", "html_url": "url", "stargazers_count": 1000, "language": "Py", "created_at": "2020", "default_branch": "main"}
    ]
    output_path = tmp_path / "test_repos.csv"
    
    save_repos_metadata(repos, output_path)
    
    assert output_path.exists()
    df = pd.read_csv(output_path)
    assert len(df) == 1
    assert df.iloc[0]["repo_id"] == "1"
    assert df.iloc[0]["full_name"] == "a/b"
    assert "total_lines_changed" not in df.columns # Metadata only
    assert "stargazers_count" in df.columns
