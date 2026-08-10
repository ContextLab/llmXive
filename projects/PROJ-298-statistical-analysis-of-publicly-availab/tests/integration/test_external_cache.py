"""
Integration tests for T051: API Rate-Limiting and Caching in external.py
"""
import os
import json
import time
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path if needed
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.external import (
    ensure_cache_dir,
    load_cache,
    save_cache,
    is_cache_valid,
    get_from_cache,
    set_cache,
    CACHE_TTL_HOURS,
    GITHUB_CACHE_FILE,
    NPM_CACHE_FILE
)


class TestCachingLogic:
    """Test the caching mechanisms independently of network calls."""

    def test_ensure_cache_dir_creates_directory(self, tmp_path):
        """Test that ensure_cache_dir creates the directory if it doesn't exist."""
        # Temporarily override CACHE_DIR for testing
        import data.external as ext_module
        original_cache_dir = ext_module.CACHE_DIR
        test_cache_dir = tmp_path / "test_cache"
        ext_module.CACHE_DIR = test_cache_dir
        
        try:
            ext_module.ensure_cache_dir()
            assert test_cache_dir.exists()
            assert test_cache_dir.is_dir()
        finally:
            ext_module.CACHE_DIR = original_cache_dir

    def test_load_cache_returns_empty_if_missing(self, tmp_path):
        """Test loading from a non-existent cache file."""
        non_existent = tmp_path / "missing.json"
        result = load_cache(non_existent)
        assert "_metadata" in result
        assert "entries" in result
        assert isinstance(result["entries"], dict)

    def test_load_cache_returns_data_if_exists(self, tmp_path):
        """Test loading from an existing cache file."""
        cache_file = tmp_path / "existing.json"
        test_data = {"_metadata": {"created_at": time.time()}, "entries": {"key1": {"data": "value1"}}}
        
        with open(cache_file, 'w') as f:
            json.dump(test_data, f)
        
        result = load_cache(cache_file)
        assert result["entries"]["key1"]["data"] == "value1"

    def test_is_cache_valid_within_ttl(self):
        """Test cache validity within TTL."""
        valid_entry = {"created_at": time.time()}
        assert is_cache_valid(valid_entry) is True

    def test_is_cache_valid_expired(self):
        """Test cache validity after TTL."""
        # Create an entry from 25 hours ago
        old_time = time.time() - (25 * 3600)
        expired_entry = {"created_at": old_time}
        assert is_cache_valid(expired_entry) is False

    def test_get_from_cache_hits_valid(self, tmp_path):
        """Test successful cache hit."""
        cache_file = tmp_path / "cache.json"
        current_time = time.time()
        test_data = {
            "_metadata": {"created_at": current_time},
            "entries": {
                "test_key": {"created_at": current_time, "data": "test_value"}
            }
        }
        with open(cache_file, 'w') as f:
            json.dump(test_data, f)
        
        result = get_from_cache(cache_file, "test_key")
        assert result == "test_value"

    def test_get_from_cache_miss_expired(self, tmp_path):
        """Test cache miss due to expiration."""
        cache_file = tmp_path / "cache.json"
        old_time = time.time() - (25 * 3600)
        test_data = {
            "_metadata": {"created_at": old_time},
            "entries": {
                "test_key": {"created_at": old_time, "data": "test_value"}
            }
        }
        with open(cache_file, 'w') as f:
            json.dump(test_data, f)
        
        result = get_from_cache(cache_file, "test_key")
        assert result is None

    def test_set_cache_persists(self, tmp_path):
        """Test that set_cache writes to disk."""
        cache_file = tmp_path / "cache.json"
        set_cache(cache_file, "new_key", "new_value")
        
        assert cache_file.exists()
        with open(cache_file, 'r') as f:
            data = json.load(f)
        
        assert "new_key" in data["entries"]
        assert data["entries"]["new_key"]["data"] == "new_value"


@pytest.mark.integration
class TestExternalFetchCaching:
    """Integration tests for the actual fetch functions (mocked network)."""

    @patch('data.external.requests.get')
    def test_fetch_github_uses_cache(self, mock_get, tmp_path):
        """Test that fetch_github_stars uses cache on second call."""
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total_count": 1,
            "items": [{"full_name": "test/repo", "stargazers_count": 100, "html_url": "http://test.com"}]
        }
        mock_get.return_value = mock_response

        # Override cache paths for test
        import data.external as ext_module
        original_github_cache = ext_module.GITHUB_CACHE_FILE
        original_cache_dir = ext_module.CACHE_DIR
        
        test_cache_dir = tmp_path / "test_cache"
        test_cache_dir.mkdir()
        ext_module.CACHE_DIR = test_cache_dir
        ext_module.GITHUB_CACHE_FILE = test_cache_dir / "github_test.json"

        try:
            # First call - should hit network
            result1 = ext_module.fetch_github_stars("python")
            assert result1 is not None
            assert len(result1["repos"]) == 1
            
            # Reset mock to ensure it wasn't called again
            mock_get.reset_mock()
            
            # Second call - should hit cache
            result2 = ext_module.fetch_github_stars("python")
            
            # Verify network was NOT called
            mock_get.assert_not_called()
            
            # Verify results are the same
            assert result1 == result2
        finally:
            ext_module.GITHUB_CACHE_FILE = original_github_cache
            ext_module.CACHE_DIR = original_cache_dir

    @patch('data.external.requests.get')
    def test_fetch_npm_uses_cache(self, mock_get, tmp_path):
        """Test that fetch_npm_downloads uses cache on second call."""
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "objects": [
                {
                    "package": {
                        "name": "lodash",
                        "version": "4.17.21"
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        import data.external as ext_module
        original_npm_cache = ext_module.NPM_CACHE_FILE
        original_cache_dir = ext_module.CACHE_DIR
        
        test_cache_dir = tmp_path / "test_cache"
        test_cache_dir.mkdir()
        ext_module.CACHE_DIR = test_cache_dir
        ext_module.NPM_CACHE_FILE = test_cache_dir / "npm_test.json"

        try:
            # First call
            result1 = ext_module.fetch_npm_downloads("lodash")
            assert result1 is not None
            
            mock_get.reset_mock()
            
            # Second call
            result2 = ext_module.fetch_npm_downloads("lodash")
            
            # Verify network was NOT called
            mock_get.assert_not_called()
            assert result1 == result2
        finally:
            ext_module.NPM_CACHE_FILE = original_npm_cache
            ext_module.CACHE_DIR = original_cache_dir