"""
Unit tests for the CacheManager class.

Tests cover:
- Cache key generation
- Cache hit/miss behavior
- Checksum verification
- Immutability (no overwrites)
- Error handling
"""
import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone
import hashlib

from src.utils.cache_manager import CacheManager, get_cached_or_fetch
from src.utils.checksum import generate_checksum


class TestCacheManager:
    """Test suite for CacheManager functionality."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary directory for cache tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def cache_manager(self, temp_cache_dir):
        """Create a CacheManager instance with temporary directory."""
        return CacheManager(cache_dir=temp_cache_dir)

    def test_cache_key_generation_deterministic(self, cache_manager):
        """Test that cache key generation is deterministic for same params."""
        params = {"package": "lodash", "version": "4.17.21"}
        key1 = cache_manager._generate_cache_key(params)
        key2 = cache_manager._generate_cache_key(params)
        assert key1 == key2
        assert len(key1) == 16  # Expected length

    def test_cache_key_generation_different_params(self, cache_manager):
        """Test that different params produce different cache keys."""
        params1 = {"package": "lodash"}
        params2 = {"package": "react"}
        key1 = cache_manager._generate_cache_key(params1)
        key2 = cache_manager._generate_cache_key(params2)
        assert key1 != key2

    def test_is_cached_miss_initially(self, cache_manager):
        """Test that is_cached returns False for non-existent cache."""
        params = {"package": "nonexistent"}
        assert cache_manager.is_cached(params) is False

    def test_save_and_load_from_cache(self, cache_manager):
        """Test basic save and load functionality."""
        params = {"package": "test-package"}
        data = {"result": "success", "value": 42}
        
        # Save
        cache_path = cache_manager.save_to_cache(params, data)
        assert cache_path.exists()
        
        # Load
        loaded_data = cache_manager.load_from_cache(params)
        assert loaded_data is not None
        assert loaded_data["result"] == "success"
        assert loaded_data["value"] == 42
        assert "_cached_at" in loaded_data
        assert "_cache_key" in loaded_data

    def test_cache_immutability_prevents_overwrite(self, cache_manager):
        """Test that saving to existing cache raises FileExistsError."""
        params = {"package": "immutable-test"}
        data1 = {"version": 1}
        data2 = {"version": 2}
        
        # First save succeeds
        cache_manager.save_to_cache(params, data1)
        
        # Second save should raise
        with pytest.raises(FileExistsError):
            cache_manager.save_to_cache(params, data2)
        
        # Verify original data is unchanged
        loaded = cache_manager.load_from_cache(params)
        assert loaded["version"] == 1

    def test_checksum_verification_on_load(self, cache_manager):
        """Test that corrupted cache files are detected via checksum."""
        params = {"package": "corruption-test"}
        data = {"original": "data"}
        
        # Save valid cache
        cache_path = cache_manager.save_to_cache(params, data)
        checksum_path = cache_manager._get_checksum_path(
            cache_manager._generate_cache_key(params)
        )
        
        # Corrupt the file
        with open(cache_path, 'w') as f:
            f.write('corrupted content')
        
        # Load should fail with ValueError
        with pytest.raises(ValueError, match="Checksum mismatch"):
            cache_manager.load_from_cache(params)

    def test_load_from_cache_missing_file(self, cache_manager):
        """Test loading when cache file doesn't exist."""
        params = {"package": "missing-file"}
        result = cache_manager.load_from_cache(params)
        assert result is None

    def test_load_from_cache_invalid_json(self, cache_manager):
        """Test loading when cache contains invalid JSON."""
        params = {"package": "invalid-json"}
        cache_key = cache_manager._generate_cache_key(params)
        cache_path = cache_manager._get_cache_path(cache_key)
        checksum_path = cache_manager._get_checksum_path(cache_key)
        
        # Write invalid JSON
        with open(cache_path, 'w') as f:
            f.write('not valid json {{{')
        
        # Write a checksum (even if mismatched)
        checksum = generate_checksum('not valid json {{{')
        checksum_path.write_text(checksum)
        
        # Load should return None (not raise)
        result = cache_manager.load_from_cache(params)
        assert result is None

    def test_get_cache_stats(self, cache_manager, temp_cache_dir):
        """Test cache statistics reporting."""
        # Initially empty
        stats = cache_manager.get_cache_stats()
        assert stats["cache_files"] == 0
        assert stats["checksum_files"] == 0
        
        # Add some files
        for i in range(3):
            params = {"package": f"pkg-{i}"}
            cache_manager.save_to_cache(params, {"data": i})
        
        stats = cache_manager.get_cache_stats()
        assert stats["cache_files"] == 3
        assert stats["checksum_files"] == 3
        assert stats["total_files"] == 6
        assert stats["total_size_bytes"] > 0

    def test_clear_cache_dry_run(self, cache_manager, temp_cache_dir):
        """Test clear_cache with dry_run=True."""
        # Add files
        for i in range(2):
            params = {"package": f"pkg-{i}"}
            cache_manager.save_to_cache(params, {"data": i})
        
        result = cache_manager.clear_cache(dry_run=True)
        assert result["dry_run"] is True
        assert result["would_delete"] == 4  # 2 json + 2 sha256
        
        # Files should still exist
        assert len(list(temp_cache_dir.glob("*"))) == 4

    def test_clear_cache_actual(self, cache_manager, temp_cache_dir):
        """Test actual cache clearing."""
        # Add files
        for i in range(2):
            params = {"package": f"pkg-{i}"}
            cache_manager.save_to_cache(params, {"data": i})
        
        result = cache_manager.clear_cache(dry_run=False)
        assert result["deleted"] == 4
        assert len(list(temp_cache_dir.glob("*"))) == 0

    def test_get_cached_or_fetch_hit(self, cache_manager):
        """Test get_cached_or_fetch when cache hit occurs."""
        params = {"package": "fetch-test"}
        data = {"fetched": False}
        
        # Pre-populate cache
        cache_manager.save_to_cache(params, data)
        
        fetch_called = False
        def mock_fetch():
            nonlocal fetch_called
            fetch_called = True
            return {"fetched": True}
        
        result = get_cached_or_fetch(cache_manager, params, mock_fetch)
        assert result["fetched"] is False  # From cache
        assert fetch_called is False  # Fetch function not called

    def test_get_cached_or_fetch_miss(self, cache_manager):
        """Test get_cached_or_fetch when cache miss occurs."""
        params = {"package": "fetch-miss-test"}
        
        fetch_data = {"fetched": True, "value": 123}
        def mock_fetch():
            return fetch_data
        
        result = get_cached_or_fetch(cache_manager, params, mock_fetch)
        assert result["fetched"] is True
        assert result["value"] == 123
        
        # Verify it was cached
        assert cache_manager.is_cached(params) is True

    def test_cache_with_string_data(self, cache_manager):
        """Test caching string data instead of dict."""
        params = {"package": "string-test"}
        string_data = '{"raw": "json", "value": "test"}'
        
        cache_path = cache_manager.save_to_cache(params, string_data)
        assert cache_path.exists()
        
        # Check file content
        with open(cache_path, 'r') as f:
            content = f.read()
        assert content == string_data

    def test_cache_path_construction(self, cache_manager):
        """Test that cache paths are constructed correctly."""
        params = {"package": "path-test"}
        cache_key = cache_manager._generate_cache_key(params)
        
        cache_path = cache_manager._get_cache_path(cache_key, "json")
        assert cache_path.name == f"{cache_key}.json"
        assert cache_path.parent == cache_manager.cache_dir

        checksum_path = cache_manager._get_checksum_path(cache_key)
        assert checksum_path.name == f"{cache_key}.sha256"
        assert checksum_path.parent == cache_manager.cache_dir