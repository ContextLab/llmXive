"""
Unit tests for Repository Metadata Enrichment (T045)
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Mock the utils.config to avoid loading real config in tests
@pytest.fixture
def mock_config():
    return {
        "paths": {
            "data": "/tmp/data",
            "processed": "/tmp/data/processed",
            "logs": "/tmp/data/logs"
        },
        "api": {
            "github_token": "fake_token"
        }
    }

@pytest.fixture
def sample_parquet(tmp_path):
    """Create a sample parquet file for testing."""
    df = pd.DataFrame({
        'repository': ['owner/repo1', 'owner/repo2', 'owner/repo3'],
        'created_at': ['2021-01-01', '2021-02-01', '2021-03-01'],
        'closed_at': ['2021-01-02', '2021-02-02', '2021-03-02']
    })
    path = tmp_path / "test_data.parquet"
    df.to_parquet(path)
    return path

def test_load_repository_list(sample_parquet):
    """Test extraction of unique repositories."""
    from collect.enrich_metadata import load_repository_list
    
    repos = load_repository_list(sample_parquet)
    assert 'owner/repo1' in repos
    assert 'owner/repo2' in repos
    assert len(repos) == 3

@patch('collect.enrich_metadata.requests.get')
def test_fetch_repo_metadata(mock_get):
    """Test metadata fetching logic."""
    from collect.enrich_metadata import fetch_repo_metadata

    # Mock repo details response
    mock_repo_resp = MagicMock()
    mock_repo_resp.status_code = 200
    mock_repo_resp.json.return_value = {
        "language": "Python",
        "stargazers_count": 100
    }
    
    # Mock contributors response (per_page=1, no link header -> 1 contributor)
    mock_contrib_resp = MagicMock()
    mock_contrib_resp.status_code = 200
    mock_contrib_resp.headers = {}
    mock_contrib_resp.json.return_value = [{"id": 1}]

    def side_effect(url, *args, **kwargs):
        if 'contributors' in url:
            return mock_contrib_resp
        return mock_repo_resp

    mock_get.side_effect = side_effect

    result = fetch_repo_metadata('owner/repo1', 'fake_token')
    
    assert result['repo_id'] == 'owner/repo1'
    assert result['language'] == 'Python'
    assert result['star_count'] == 100
    assert result['contributor_count'] == 1

@patch('collect.enrich_metadata.requests.get')
def test_fetch_repo_metadata_rate_limit(mock_get):
    """Test rate limit handling (403 -> wait -> retry)."""
    from collect.enrich_metadata import fetch_repo_metadata

    # First call 403, second call 200
    mock_403 = MagicMock()
    mock_403.status_code = 403
    
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {"language": "Java", "stargazers_count": 50}
    
    # Mock contributors for the retry
    mock_contrib = MagicMock()
    mock_contrib.status_code = 200
    mock_contrib.headers = {}
    mock_contrib.json.return_value = [{"id": 1}]

    call_count = 0
    def side_effect(url, *args, **kwargs):
        nonlocal call_count
        if 'contributors' in url:
            return mock_contrib
        
        if call_count == 0:
            call_count += 1
            return mock_403
        return mock_200

    mock_get.side_effect = side_effect

    # Should wait and retry
    result = fetch_repo_metadata('owner/repo1', 'fake_token')
    
    assert result['language'] == 'Java'
    assert mock_get.call_count >= 2 # 1st fail, 2nd success, plus contributors

def test_enrich_metadata_integration(sample_parquet, tmp_path):
    """Integration test for the full enrichment flow (mocked API)."""
    from collect.enrich_metadata import enrich_metadata
    
    output_meta = tmp_path / "metadata.json"
    output_merged = tmp_path / "merged.parquet"
    
    with patch('collect.enrich_metadata.requests.get') as mock_get:
        # Setup mocks
        mock_repo = MagicMock()
        mock_repo.status_code = 200
        mock_repo.json.return_value = {"language": "TypeScript", "stargazers_count": 200}
        
        mock_contrib = MagicMock()
        mock_contrib.status_code = 200
        mock_contrib.headers = {}
        mock_contrib.json.return_value = [{"id": 1}, {"id": 2}] # 2 contributors

        def side_effect(url, *args, **kwargs):
            if 'contributors' in url:
                return mock_contrib
            return mock_repo

        mock_get.side_effect = side_effect

        enrich_metadata(sample_parquet, output_meta, output_merged)

        # Check outputs
        assert output_meta.exists()
        assert output_merged.exists()

        with open(output_meta) as f:
            data = json.load(f)
            assert len(data) == 3
            assert data[0]['language'] == 'TypeScript'

        # Check merged file
        df_merged = pd.read_parquet(output_merged)
        assert 'language' in df_merged.columns
        assert df_merged['language'].iloc[0] == 'TypeScript'