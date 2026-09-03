import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from utils.repo_fetcher import (
    fetch_top_repos_from_pypi,
    fetch_fallback_repos,
    validate_repo_list_schema,
    create_repo_list_file,
    FALLBACK_REPOS
)
from utils.exceptions import RepoFetcherException

@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path

def test_fetch_fallback_repos_count():
    """Test that fallback repos returns exactly 20 items (or the defined constant)"""
    repos = fetch_fallback_repos()
    assert len(repos) == 20

def test_fetch_fallback_repos_schema():
    """Test that fallback repos have the required schema"""
    repos = fetch_fallback_repos()
    assert validate_repo_list_schema(repos) is True

def test_validate_repo_list_schema_valid():
    """Test schema validation with valid data"""
    valid_data = [
        {"repo_url": "http://a.com", "github_url": "http://b.com", "star_count": 100},
        {"repo_url": "http://c.com", "github_url": "http://d.com", "star_count": 200}
    ]
    assert validate_repo_list_schema(valid_data) is True

def test_validate_repo_list_schema_missing_field():
    """Test schema validation with missing field"""
    invalid_data = [
        {"repo_url": "http://a.com", "github_url": "http://b.com"} # Missing star_count
    ]
    assert validate_repo_list_schema(invalid_data) is False

def test_validate_repo_list_schema_invalid_type():
    """Test schema validation with invalid type"""
    invalid_data = [
        {"repo_url": "http://a.com", "github_url": "http://b.com", "star_count": "many"}
    ]
    assert validate_repo_list_schema(invalid_data) is False

def test_create_repo_list_file(temp_dir):
    """Test creating the repo list file"""
    repos = fetch_fallback_repos()
    output_path = temp_dir / "test_repos.json"
    
    create_repo_list_file(repos, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 20
    assert validate_repo_list_schema(data) is True
    
    # Check sorting (descending by star_count)
    for i in range(len(data) - 1):
        assert data[i]['star_count'] >= data[i+1]['star_count']

@patch('utils.repo_fetcher.requests.Session')
def test_fetch_top_repos_from_pypi_fallback_on_api_failure(mock_session_class):
    """Test that API failure triggers fallback"""
    mock_session = MagicMock()
    mock_session.get.side_effect = Exception("Network error")
    mock_session_class.return_value = mock_session
    
    repos = fetch_top_repos_from_pypi()
    
    # Should fall back to the verified list
    assert len(repos) == 20
    assert repos[0] == FALLBACK_REPOS[0]