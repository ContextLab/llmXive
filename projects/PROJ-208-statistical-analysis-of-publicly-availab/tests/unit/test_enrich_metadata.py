"""
Unit tests for Repository Metadata Enrichment (T045)
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test
# Adjust import path based on project structure
from code.collect.enrich_metadata import (
    load_repository_list,
    fetch_repo_metadata,
    enrich_metadata,
    main
)
from code.utils.api_client import GitHubAPIClient
from code.utils.config import get_config

@pytest.fixture
def mock_config():
    """Mock configuration for tests."""
    config = MagicMock()
    config.get_path.side_effect = lambda key: {
        'processed_cleaned_issues': 'data/processed/cleaned_issues.csv',
        'repo_metadata': 'data/processed/repo_metadata.json',
        'log_dir': 'data/logs'
    }.get(key, 'data/processed/cleaned_issues.csv')
    return config

@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample cleaned_issues.csv for testing."""
    csv_path = tmp_path / "cleaned_issues.csv"
    content = """repository,created_at,closed_at,resolution_time_hours,labels,assignee,comments_count
    owner/repo1,2023-01-01,2023-01-02,24,"bug",user1,5
    owner/repo2,2023-02-01,2023-02-05,96,"feature",user2,10
    owner/repo3,2023-03-01,2023-03-01,0,"docs",user3,2
    """
    csv_path.write_text(content)
    return str(csv_path)

@pytest.fixture
def mock_api_client():
    """Mock GitHub API client."""
    client = MagicMock(spec=GitHubAPIClient)
    client.headers = {"Accept": "application/vnd.github.v3+json"}
    client.session = MagicMock()
    return client

def test_load_repository_list(sample_csv):
    """Test loading unique repositories from CSV."""
    repos = load_repository_list(sample_csv)
    expected = {"owner/repo1", "owner/repo2", "owner/repo3"}
    assert repos == expected
    assert len(repos) == 3

def test_fetch_repo_metadata_success(mock_api_client):
    """Test successful metadata fetch."""
    # Mock repo details response
    repo_response = {
        'language': 'Python',
        'stargazers_count': 150
    }
    mock_api_client.get_repo.return_value = repo_response

    # Mock contributors response
    contributors_response = MagicMock()
    contributors_response.status_code = 200
    contributors_response.headers = {
        'Link': '<https://api.github.com/repositories/123/contributors?page=2>; rel="last"'
    }
    contributors_response.json.return_value = [{'id': 1}]
    mock_api_client.session.get.return_value = contributors_response

    result = fetch_repo_metadata(mock_api_client, "owner/test_repo")

    assert result is not None
    assert result['repo_id'] == "owner/test_repo"
    assert result['language'] == 'Python'
    assert result['star_count'] == 150
    assert result['contributor_count'] == 2  # Parsed from Link header

def test_fetch_repo_metadata_failure(mock_api_client):
    """Test metadata fetch failure."""
    mock_api_client.get_repo.return_value = None
    
    result = fetch_repo_metadata(mock_api_client, "owner/invalid_repo")
    assert result is None

def test_enrich_metadata_integration(sample_csv, mock_api_client, tmp_path):
    """Test full enrichment flow."""
    # Mock API responses
    def mock_get_repo(repo):
        return {
            'language': 'Python' if 'repo1' in repo else 'JavaScript',
            'stargazers_count': 100
        }

    def mock_get_contributors(url, headers, params):
        response = MagicMock()
        response.status_code = 200
        response.headers = {} # No link header -> 1 page
        response.json.return_value = [{'id': 1}]
        return response

    mock_api_client.get_repo.side_effect = mock_get_repo
    mock_api_client.session.get.side_effect = mock_get_contributors

    output_path = tmp_path / "metadata.json"
    stats = enrich_metadata(
        {"owner/repo1", "owner/repo2"},
        mock_api_client,
        str(output_path)
    )

    assert stats['successful'] == 2
    assert stats['failed'] == 0
    assert output_path.exists()

    with open(output_path) as f:
        data = json.load(f)
    
    assert len(data['metadata']) == 2
    assert 'repo_id' in data['metadata'][0]
    assert 'language' in data['metadata'][0]
    assert 'star_count' in data['metadata'][0]
    assert 'contributor_count' in data['metadata'][0]

def test_main_integration(sample_csv, mock_config, mock_api_client, tmp_path, monkeypatch):
    """Test main function execution."""
    # Patch config and paths
    monkeypatch.setattr('code.collect.enrich_metadata.get_config', lambda: mock_config)
    
    # Override config paths to use temp dir
    def mock_get_path(key):
        if key == 'processed_cleaned_issues':
            return str(sample_csv)
        elif key == 'repo_metadata':
            return str(tmp_path / "metadata.json")
        return 'data/processed/cleaned_issues.csv'
    
    mock_config.get_path.side_effect = mock_get_path

    # Mock API client creation
    with patch('code.collect.enrich_metadata.GitHubAPIClient', return_value=mock_api_client):
        # Mock get_repo and get for contributors
        mock_api_client.get_repo.return_value = {'language': 'Python', 'stargazers_count': 50}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.json.return_value = [{'id': 1}]
        mock_api_client.session.get.return_value = mock_resp

        # Run main
        main()

        # Verify output file exists
        output_file = tmp_path / "metadata.json"
        assert output_file.exists()
        
        with open(output_file) as f:
            data = json.load(f)
        
        assert 'metadata' in data
        assert len(data['metadata']) > 0