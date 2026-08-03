"""
Unit tests for the local file caching mechanism.

Tests verify:
- Cache directory creation
- Response caching with checksums
- Cache retrieval and validation
- Cache invalidation on data change
- Cache statistics
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.cache_manager import CacheManager, get_cache_manager, cache_api_response, get_cached_api_response
from src.utils.checksum import generate_checksum


class TestCacheManager:
    """Test suite for CacheManager class."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary directory for cache tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def cache_manager(self, temp_cache_dir):
        """Create a CacheManager instance with temp directory."""
        return CacheManager(cache_dir=temp_cache_dir)

    def test_cache_dir_creation(self, temp_cache_dir):
        """Test that cache directory is created if it doesn't exist."""
        non_existent_dir = temp_cache_dir / "new_cache"
        assert not non_existent_dir.exists()
        
        manager = CacheManager(cache_dir=non_existent_dir)
        assert non_existent_dir.exists()
        assert non_existent_dir.is_dir()

    def test_cache_response(self, cache_manager):
        """Test caching an API response."""
        api_name = "npm"
        endpoint = "/packages/express"
        params = {"fields": "downloads,dependencies"}
        response_data = {
            "name": "express",
            "downloads": 1000000,
            "dependencies": ["body-parser", "cookie"]
        }

        cache_manager.cache_response(api_name, endpoint, params, response_data)

        # Verify files were created
        cache_key = cache_manager._generate_cache_key(api_name, endpoint, params)
        cache_path = cache_manager._get_cache_path(cache_key)
        checksum_path = cache_manager._get_checksum_path(cache_key)

        assert cache_path.exists()
        assert checksum_path.exists()

        # Verify content
        with open(cache_path, 'r') as f:
            loaded_data = json.load(f)
        assert loaded_data == response_data

        # Verify checksum
        with open(checksum_path, 'r') as f:
            stored_checksum = f.read().strip()
        
        expected_checksum = generate_checksum(response_data)
        assert stored_checksum == expected_checksum

    def test_get_cached_response(self, cache_manager):
        """Test retrieving a cached response."""
        api_name = "github"
        endpoint = "/repos/microsoft/typescript"
        params = {"per_page": 10}
        response_data = {
            "full_name": "microsoft/typescript",
            "created_at": "2014-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }

        # First, cache the response
        cache_manager.cache_response(api_name, endpoint, params, response_data)

        # Then retrieve it
        cached = cache_manager.get_cached_response(api_name, endpoint, params)
        assert cached == response_data

    def test_cache_miss_on_missing_file(self, cache_manager):
        """Test that get_cached_response returns None for missing cache."""
        api_name = "npm"
        endpoint = "/nonexistent"
        params = {}
        
        result = cache_manager.get_cached_response(api_name, endpoint, params)
        assert result is None

    def test_cache_invalidation_on_data_change(self, cache_manager):
        """Test that cache is invalidated when data changes but key is same."""
        api_name = "npm"
        endpoint = "/packages/lodash"
        params = {}
        original_data = {"name": "lodash", "version": "4.17.21"}
        modified_data = {"name": "lodash", "version": "4.17.22"}

        # Cache original data
        cache_manager.cache_response(api_name, endpoint, params, original_data)

        # Manually modify the cache file to simulate corruption/change
        cache_key = cache_manager._generate_cache_key(api_name, endpoint, params)
        cache_path = cache_manager._get_cache_path(cache_key)
        
        with open(cache_path, 'w') as f:
            json.dump(modified_data, f)

        # Should return None because checksum won't match
        result = cache_manager.get_cached_response(api_name, endpoint, params)
        assert result is None

    def test_cache_invalidation_on_checksum_mismatch(self, cache_manager):
        """Test cache invalidation when checksum file is corrupted."""
        api_name = "npm"
        endpoint = "/packages/react"
        params = {}
        response_data = {"name": "react", "version": "18.2.0"}

        cache_manager.cache_response(api_name, endpoint, params, response_data)

        # Corrupt the checksum file
        cache_key = cache_manager._generate_cache_key(api_name, endpoint, params)
        checksum_path = cache_manager._get_checksum_path(cache_key)
        
        with open(checksum_path, 'w') as f:
            f.write("invalid_checksum")

        # Should return None
        result = cache_manager.get_cached_response(api_name, endpoint, params)
        assert result is None

    def test_clear_cache_specific(self, cache_manager):
        """Test clearing a specific cache entry."""
        api_name = "npm"
        endpoint = "/packages/axios"
        params = {}
        response_data = {"name": "axios"}

        cache_manager.cache_response(api_name, endpoint, params, response_data)
        cache_key = cache_manager._generate_cache_key(api_name, endpoint, params)

        # Clear specific entry
        deleted = cache_manager.clear_cache(cache_key=cache_key)
        assert deleted == 2  # .json and .sha256 files

        assert not cache_manager._get_cache_path(cache_key).exists()
        assert not cache_manager._get_checksum_path(cache_key).exists()

    def test_clear_cache_all(self, cache_manager):
        """Test clearing all cache entries."""
        # Add multiple cache entries
        for i in range(3):
            cache_manager.cache_response(
                "npm", 
                f"/packages/pkg{i}", 
                {}, 
                {"name": f"pkg{i}"}
            )

        deleted = cache_manager.clear_cache()
        assert deleted == 6  # 3 .json + 3 .sha256 files

    def test_get_cache_stats(self, cache_manager):
        """Test getting cache statistics."""
        # Add some entries
        for i in range(2):
            cache_manager.cache_response(
                "npm", 
                f"/packages/stat{i}", 
                {}, 
                {"name": f"stat{i}", "size": 100 * (i + 1)}
            )

        stats = cache_manager.get_cache_stats()
        
        assert stats["total_entries"] == 2
        assert stats["checksum_files"] == 2
        assert stats["total_size_bytes"] > 0
        assert Path(stats["cache_dir"]) == cache_manager.cache_dir

    def test_deterministic_cache_key(self, cache_manager):
        """Test that cache key is deterministic regardless of param order."""
        api_name = "npm"
        endpoint = "/packages/test"
        
        params1 = {"a": 1, "b": 2, "c": 3}
        params2 = {"c": 3, "a": 1, "b": 2}  # Same params, different order

        key1 = cache_manager._generate_cache_key(api_name, endpoint, params1)
        key2 = cache_manager._generate_cache_key(api_name, endpoint, params2)

        assert key1 == key2

    def test_cache_key_uniqueness(self, cache_manager):
        """Test that different parameters produce different cache keys."""
        api_name = "npm"
        endpoint = "/packages/test"

        key1 = cache_manager._generate_cache_key(api_name, endpoint, {"a": 1})
        key2 = cache_manager._generate_cache_key(api_name, endpoint, {"a": 2})
        key3 = cache_manager._generate_cache_key(api_name, "/other", {"a": 1})

        assert key1 != key2
        assert key1 != key3
        assert key2 != key3


class TestConvenienceFunctions:
    """Test suite for convenience functions."""

    @pytest.fixture
    def temp_cache_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_get_cache_manager_singleton(self, temp_cache_dir):
        """Test that get_cache_manager returns a singleton instance."""
        with patch('src.utils.cache_manager.CacheManager') as mock_manager:
            # First call
            instance1 = get_cache_manager()
            # Second call (should not create new instance)
            instance2 = get_cache_manager()
            
            # Verify CacheManager was only instantiated once
            assert mock_manager.call_count == 1
            assert instance1 is instance2

    def test_cache_api_response_function(self, temp_cache_dir):
        """Test the cache_api_response convenience function."""
        with patch('src.utils.cache_manager.CacheManager') as MockManager:
            mock_instance = MagicMock()
            MockManager.return_value = mock_instance
            
            cache_api_response("npm", "/test", {"a": 1}, {"data": "value"})
            
            mock_instance.cache_response.assert_called_once_with(
                "npm", "/test", {"a": 1}, {"data": "value"}
            )

    def test_get_cached_api_response_function(self, temp_cache_dir):
        """Test the get_cached_api_response convenience function."""
        with patch('src.utils.cache_manager.CacheManager') as MockManager:
            mock_instance = MagicMock()
            mock_instance.get_cached_response.return_value = {"cached": "data"}
            MockManager.return_value = mock_instance
            
            result = get_cached_api_response("npm", "/test", {"a": 1})
            
            mock_instance.get_cached_response.assert_called_once_with(
                "npm", "/test", {"a": 1}
            )
            assert result == {"cached": "data"}