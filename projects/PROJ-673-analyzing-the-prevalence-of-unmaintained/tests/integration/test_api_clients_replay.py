"""
Integration test for replaying NPM/GitHub API responses using cached snapshots.

This test adheres to Constitution Principle VI (API Snapshot Integrity) and
FR-007 (real-call testing) by verifying that the API clients can successfully
load and return data from pre-fetched cache files in `data/raw/` instead of
making live network calls.

Prerequisites:
- T008 (Caching) must be complete.
- Cache files must exist in `data/raw/` with the correct naming convention
  (hash of request params + timestamp).

Usage:
pytest tests/integration/test_api_clients_replay.py -v
"""
import json
import os
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import pytest

# Import clients to test
from src.services.npm_client import NpmClient
from src.services.github_client import GithubClient
from src.services.audit_client import AuditClient
from src.utils.cache import save_response_to_cache, load_from_cache
from src.config.settings import get_config


def _generate_cache_filename(params: dict) -> str:
    """Generate the cache filename based on request parameters."""
    param_str = json.dumps(params, sort_keys=True)
    param_hash = hashlib.md5(param_str.encode()).hexdigest()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"{param_hash}_{timestamp}.json"


def _create_mock_cache_file(cache_dir: Path, service: str, params: dict, mock_data: dict) -> Path:
    """
    Creates a mock cache file in the specified directory.
    Returns the path to the created file.
    """
    filename = _generate_cache_filename(params)
    file_path = cache_dir / filename
    
    # Ensure the file content matches what the cache loader expects
    cache_entry = {
        "service": service,
        "request_params": params,
        "response": mock_data,
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "checksum": hashlib.sha256(json.dumps(mock_data).encode()).hexdigest()
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(cache_entry, f, indent=2)
    
    return file_path


class TestNpmClientReplay:
    """Tests for replaying NPM API responses from cache."""

    @pytest.fixture(autouse=True)
    def setup_cache_dir(self, tmp_path):
        """Set up a temporary directory for cache files."""
        self.cache_dir = tmp_path / "data" / "raw"
        self.cache_dir.mkdir(parents=True)
        
        # Mock config to use our temporary cache directory
        self.mock_config = MagicMock()
        self.mock_config.DATA_RAW_DIR = str(self.cache_dir)
        
        # Patch the get_config function to return our mock config
        with patch('src.services.npm_client.get_config', return_value=self.mock_config):
            self.client = NpmClient()
            yield

    def test_replay_top_packages(self):
        """Test that NpmClient can replay top packages data from cache."""
        # Prepare mock data
        mock_response = {
            "objects": [
                {
                    "package": {
                        "name": "lodash",
                        "version": "4.17.21",
                        "date": "2021-02-18T22:32:24.112Z"
                    },
                    "downloads": 45000000
                },
                {
                    "package": {
                        "name": "express",
                        "version": "4.18.2",
                        "date": "2022-10-12T18:15:32.441Z"
                    },
                    "downloads": 32000000
                }
            ]
        }

        # Create cache file with specific params
        search_params = {"range": "top", "count": 2}
        cache_file = _create_mock_cache_file(
            self.cache_dir, 
            "npm_top_packages", 
            search_params, 
            mock_response
        )

        # Verify cache file exists
        assert cache_file.exists(), f"Cache file {cache_file} was not created"

        # Mock the cache loader to return our specific file
        def mock_load_from_cache(params):
            if params == search_params:
                return load_from_cache(params)
            return None

        with patch('src.services.npm_client.load_from_cache', side_effect=mock_load_from_cache):
            # Call the method that would normally hit the API
            # We are testing that it uses the cache
            result = self.client.get_top_packages(count=2)

        # Verify the result matches our cached data
        assert result is not None, "Result should not be None"
        assert len(result) == 2, f"Expected 2 packages, got {len(result)}"
        assert result[0]['name'] == 'lodash', "First package should be lodash"
        assert result[1]['name'] == 'express', "Second package should be express"

    def test_cache_miss_raises_error(self):
        """Test that a cache miss results in an appropriate error or fallback behavior."""
        # Request data that doesn't exist in cache
        search_params = {"range": "top", "count": 999}
        
        # Ensure no cache file exists for these params
        existing_files = list(self.cache_dir.glob("*.json"))
        for f in existing_files:
            f.unlink()
        
        # Mock load_from_cache to return None (cache miss)
        with patch('src.services.npm_client.load_from_cache', return_value=None):
            # The client should attempt to fetch from API, which will fail in this test
            # because we are not mocking the actual API call
            with pytest.raises(Exception):
                self.client.get_top_packages(count=999)


class TestGithubClientReplay:
    """Tests for replaying GitHub API responses from cache."""

    @pytest.fixture(autouse=True)
    def setup_cache_dir(self, tmp_path):
        """Set up a temporary directory for cache files."""
        self.cache_dir = tmp_path / "data" / "raw"
        self.cache_dir.mkdir(parents=True)
        
        self.mock_config = MagicMock()
        self.mock_config.DATA_RAW_DIR = str(self.cache_dir)
        
        with patch('src.services.github_client.get_config', return_value=self.mock_config):
            self.client = GithubClient()
            yield

    def test_replay_commit_date(self):
        """Test that GithubClient can replay commit date data from cache."""
        mock_response = {
            "commit": {
                "author": {
                    "date": "2023-05-15T14:30:00Z"
                }
            },
            "sha": "abc123def456"
        }

        repo_params = {
            "owner": "lodash",
            "repo": "lodash",
            "endpoint": "commits"
        }

        cache_file = _create_mock_cache_file(
            self.cache_dir,
            "github_commits",
            repo_params,
            mock_response
        )

        assert cache_file.exists()

        def mock_load_from_cache(params):
            if params == repo_params:
                return load_from_cache(params)
            return None

        with patch('src.services.github_client.load_from_cache', side_effect=mock_load_from_cache):
            result = self.client.get_last_commit_date("lodash", "lodash")

        assert result is not None
        assert result == "2023-05-15T14:30:00Z"

    def test_replay_release_date(self):
        """Test that GithubClient can replay release date data from cache."""
        mock_response = [
            {
                "tag_name": "v4.17.21",
                "published_at": "2021-02-18T22:32:24Z"
            }
        ]

        repo_params = {
            "owner": "lodash",
            "repo": "lodash",
            "endpoint": "releases"
        }

        cache_file = _create_mock_cache_file(
            self.cache_dir,
            "github_releases",
            repo_params,
            mock_response
        )

        assert cache_file.exists()

        def mock_load_from_cache(params):
            if params == repo_params:
                return load_from_cache(params)
            return None

        with patch('src.services.github_client.load_from_cache', side_effect=mock_load_from_cache):
            result = self.client.get_last_release_date("lodash", "lodash")

        assert result is not None
        assert result == "2021-02-18T22:32:24Z"


class TestAuditClientReplay:
    """Tests for replaying NPM Audit API responses from cache."""

    @pytest.fixture(autouse=True)
    def setup_cache_dir(self, tmp_path):
        """Set up a temporary directory for cache files."""
        self.cache_dir = tmp_path / "data" / "raw"
        self.cache_dir.mkdir(parents=True)
        
        self.mock_config = MagicMock()
        self.mock_config.DATA_RAW_DIR = str(self.cache_dir)
        
        with patch('src.services.audit_client.get_config', return_value=self.mock_config):
            self.client = AuditClient()
            yield

    def test_replay_audit_data(self):
        """Test that AuditClient can replay audit data from cache."""
        mock_response = {
            "advisories": {
                "CVE-2021-23337": {
                    "module_name": "lodash",
                    "severity": "high",
                    "vulnerable_versions": "<4.17.21"
                },
                "CVE-2020-8203": {
                    "module_name": "lodash",
                    "severity": "critical",
                    "vulnerable_versions": "<4.17.19"
                }
            }
        }

        audit_params = {
            "package": "lodash@4.17.20",
            "endpoint": "audit"
        }

        cache_file = _create_mock_cache_file(
            self.cache_dir,
            "npm_audit",
            audit_params,
            mock_response
        )

        assert cache_file.exists()

        def mock_load_from_cache(params):
            if params == audit_params:
                return load_from_cache(params)
            return None

        with patch('src.services.audit_client.load_from_cache', side_effect=mock_load_from_cache):
            result = self.client.fetch_audit_data("lodash", "4.17.20")

        assert result is not None
        assert len(result['advisories']) == 2
        assert "CVE-2021-23337" in result['advisories']
        assert "CVE-2020-8203" in result['advisories']

class TestCacheIntegrity:
    """Tests to verify cache integrity and reproducibility."""

    def test_cache_filename_deterministic(self):
        """Verify that cache filenames are deterministic for the same input."""
        params = {"key": "value", "number": 123}
        
        filename1 = _generate_cache_filename(params)
        filename2 = _generate_cache_filename(params)
        
        # The hash part should be identical, only timestamp may differ
        hash1 = filename1.split('_')[0]
        hash2 = filename2.split('_')[0]
        
        assert hash1 == hash2, "Cache filenames must be deterministic for same input"

    def test_cache_content_matches_input(self):
        """Verify that cache content matches the input data."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_dir = Path(tmp_dir) / "data" / "raw"
            cache_dir.mkdir(parents=True)
            
            original_data = {"test": "data", "value": 42}
            params = {"query": "test"}
            
            cache_file = _create_mock_cache_file(
                cache_dir, 
                "test_service", 
                params, 
                original_data
            )
            
            # Load from cache
            loaded_data = load_from_cache(params)
            
            assert loaded_data is not None
            assert loaded_data == original_data, "Loaded data must match original data"