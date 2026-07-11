import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.utils.cache_manager import CacheManager, generate_checksum
from src.utils.checksum import write_checksum_file


@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def cache_manager(temp_cache_dir):
    """Create a CacheManager instance with temp directory."""
    return CacheManager(cache_dir=temp_cache_dir)


class TestCacheManager:
    """Test suite for CacheManager functionality."""

    def test_cache_directory_creation(self, temp_cache_dir):
        """Test that cache directory is created if it doesn't exist."""
        non_existent_dir = temp_cache_dir / "new_cache"
        manager = CacheManager(cache_dir=non_existent_dir)
        assert non_existent_dir.exists()
        assert manager.cache_dir == non_existent_dir

    def test_generate_cache_key(self, cache_manager):
        """Test cache key generation is deterministic."""
        endpoint = "/packages/lodash"
        params = {"timeout": 5000, "fields": "version"}
        
        key1 = cache_manager._generate_cache_key(endpoint, params)
        key2 = cache_manager._generate_cache_key(endpoint, params)
        
        assert key1 == key2
        assert len(key1) == 64  # SHA256 hex length

    def test_cache_key_varies_with_params(self, cache_manager):
        """Test that different params produce different keys."""
        endpoint = "/packages/lodash"
        params1 = {"timeout": 5000}
        params2 = {"timeout": 10000}
        
        key1 = cache_manager._generate_cache_key(endpoint, params1)
        key2 = cache_manager._generate_cache_key(endpoint, params2)
        
        assert key1 != key2

    def test_cache_key_varies_with_endpoint(self, cache_manager):
        """Test that different endpoints produce different keys."""
        params = {"timeout": 5000}
        endpoint1 = "/packages/lodash"
        endpoint2 = "/packages/express"
        
        key1 = cache_manager._generate_cache_key(endpoint1, params)
        key2 = cache_manager._generate_cache_key(endpoint2, params)
        
        assert key1 != key2

    def test_is_cached_returns_false_for_missing_cache(self, cache_manager):
        """Test is_cached returns False when cache doesn't exist."""
        endpoint = "/packages/test"
        params = {"version": "1.0"}
        
        assert not cache_manager.is_cached(endpoint, params)

    def test_set_and_get_cache(self, cache_manager):
        """Test basic cache set and get operations."""
        endpoint = "/packages/lodash"
        params = {"fields": "version"}
        response_data = {
            "name": "lodash",
            "version": "4.17.21",
            "downloads": 1000000
        }
        
        # Set cache
        cache_key = cache_manager.set(endpoint, params, response_data)
        
        # Verify files exist
        cache_path = cache_manager._get_cache_path(cache_key)
        checksum_path = cache_manager._get_checksum_path(cache_key)
        assert cache_path.exists()
        assert checksum_path.exists()
        
        # Get cache
        cached_data = cache_manager.get(endpoint, params)
        assert cached_data is not None
        assert cached_data["data"]["name"] == "lodash"
        assert cached_data["data"]["version"] == "4.17.21"

    def test_cache_integrity_verification(self, cache_manager):
        """Test that cache integrity is verified via checksum."""
        endpoint = "/packages/test"
        params = {"version": "1.0"}
        response_data = {"value": "test"}
        
        # Set cache
        cache_key = cache_manager.set(endpoint, params, response_data)
        
        # Corrupt the cache file
        cache_path = cache_manager._get_cache_path(cache_key)
        with open(cache_path, 'w') as f:
            f.write('{"corrupted": true}')
        
        # Verify is_cached returns False
        assert not cache_manager.is_cached(endpoint, params)
        
        # Verify get returns None
        assert cache_manager.get(endpoint, params) is None

    def test_cache_persistence(self, cache_manager):
        """Test that cache persists across manager instances."""
        endpoint = "/packages/persistent"
        params = {"test": "value"}
        response_data = {"data": "persistent"}
        
        # Set cache with first instance
        cache_manager.set(endpoint, params, response_data)
        
        # Create new instance
        new_manager = CacheManager(cache_dir=cache_manager.cache_dir)
        
        # Verify cache is accessible
        assert new_manager.is_cached(endpoint, params)
        cached = new_manager.get(endpoint, params)
        assert cached["data"]["data"] == "persistent"

    def test_clear_cache(self, cache_manager):
        """Test cache clearing functionality."""
        endpoint1 = "/packages/test1"
        endpoint2 = "/packages/test2"
        params = {"test": "value"}
        
        # Set multiple caches
        cache_manager.set(endpoint1, params, {"data": "1"})
        cache_manager.set(endpoint2, params, {"data": "2"})
        
        # Verify they exist
        assert cache_manager.is_cached(endpoint1, params)
        assert cache_manager.is_cached(endpoint2, params)
        
        # Clear cache
        deleted_count = cache_manager.clear()
        assert deleted_count == 2
        
        # Verify they're gone
        assert not cache_manager.is_cached(endpoint1, params)
        assert not cache_manager.is_cached(endpoint2, params)

    def test_get_stats(self, cache_manager):
        """Test cache statistics retrieval."""
        endpoint = "/packages/stats"
        params = {"test": "value"}
        response_data = {"data": "test"}
        
        # Add some cache entries
        for i in range(3):
            cache_manager.set(endpoint, {**params, "i": i}, response_data)
        
        stats = cache_manager.get_stats()
        
        assert "cache_dir" in stats
        assert "total_files" in stats
        assert "total_size_bytes" in stats
        assert stats["total_files"] == 3
        assert stats["total_size_mb"] >= 0

    def test_invalid_json_handling(self, cache_manager):
        """Test handling of invalid JSON in cache file."""
        endpoint = "/packages/invalid"
        params = {"version": "1.0"}
        response_data = {"valid": True}
        
        # Set cache
        cache_key = cache_manager.set(endpoint, params, response_data)
        
        # Corrupt with invalid JSON
        cache_path = cache_manager._get_cache_path(cache_key)
        with open(cache_path, 'w') as f:
            f.write('not valid json {')
        
        # Verify get returns None and doesn't crash
        result = cache_manager.get(endpoint, params)
        assert result is None

    def test_checksum_file_format(self, cache_manager):
        """Test that checksum files contain valid SHA256 hashes."""
        endpoint = "/packages/checksum"
        params = {"test": "value"}
        response_data = {"data": "test"}
        
        cache_key = cache_manager.set(endpoint, params, response_data)
        checksum_path = cache_manager._get_checksum_path(cache_key)
        
        with open(checksum_path, 'r') as f:
            checksum = f.read().strip()
        
        # SHA256 hex is 64 characters
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)

class TestCacheManagerEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_params(self, cache_manager):
        """Test caching with empty parameters."""
        endpoint = "/packages/empty"
        params = {}
        response_data = {"data": "test"}
        
        cache_key = cache_manager.set(endpoint, params, response_data)
        cached = cache_manager.get(endpoint, params)
        
        assert cached is not None
        assert cached["data"]["data"] == "test"

    def test_special_characters_in_params(self, cache_manager):
        """Test caching with special characters in parameters."""
        endpoint = "/packages/special"
        params = {"filter": "name:lodash@^4.0.0", "sort": "downloads desc"}
        response_data = {"data": "test"}
        
        cache_key = cache_manager.set(endpoint, params, response_data)
        assert cache_manager.is_cached(endpoint, params)

    def test_large_response_data(self, cache_manager):
        """Test caching large response data."""
        endpoint = "/packages/large"
        params = {"version": "1.0"}
        # Create a large response (1MB of data)
        large_data = {"data": "x" * (1024 * 1024)}
        
        cache_key = cache_manager.set(endpoint, params, large_data)
        cached = cache_manager.get(endpoint, params)
        
        assert cached is not None
        assert len(cached["data"]["data"]) == 1024 * 1024

    def test_concurrent_cache_access(self, cache_manager):
        """Test that cache handles concurrent access safely."""
        endpoint = "/packages/concurrent"
        params = {"test": "value"}
        response_data = {"data": "test"}
        
        # Set cache
        cache_manager.set(endpoint, params, response_data)
        
        # Read multiple times
        for _ in range(10):
            cached = cache_manager.get(endpoint, params)
            assert cached is not None

    def test_cache_key_normalization(self, cache_manager):
        """Test that params are normalized for consistent hashing."""
        endpoint = "/packages/normal"
        params1 = {"b": 2, "a": 1}  # Different order
        params2 = {"a": 1, "b": 2}
        response_data = {"data": "test"}
        
        # Both should produce same key
        key1 = cache_manager._generate_cache_key(endpoint, params1)
        key2 = cache_manager._generate_cache_key(endpoint, params2)
        
        assert key1 == key2

def test_convenience_functions(temp_cache_dir):
    """Test convenience functions work correctly."""
    with patch('src.utils.cache_manager.CacheManager') as MockManager:
        mock_instance = MagicMock()
        MockManager.return_value = mock_instance
        
        from src.utils.cache_manager import (
            get_cache_manager,
            cache_response,
            get_cached_response,
            is_response_cached
        )
        
        # Test get_cache_manager returns instance
        manager = get_cache_manager()
        assert manager == mock_instance
        
        # Test cache_response
        mock_instance.set.return_value = "test_key"
        result = cache_response("/test", {"p": 1}, {"d": 1})
        assert result == "test_key"
        mock_instance.set.assert_called_once_with("/test", {"p": 1}, {"d": 1})
        
        # Test get_cached_response
        mock_instance.get.return_value = {"data": "value"}
        result = get_cached_response("/test", {"p": 1})
        assert result == {"data": "value"}
        
        # Test is_response_cached
        mock_instance.is_cached.return_value = True
        result = is_response_cached("/test", {"p": 1})
        assert result is True