"""
Unit tests for the caching mechanism.
"""
import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import pytest

from code.utils.cache import Cache, compute_hash, cache_get, cache_set, get_cache
from code.utils.logging import CacheError


class TestCache:
    """Tests for the Cache class."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary directory for cache files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_init_creates_directory(self, temp_cache_dir):
        """Test that __init__ creates the cache directory."""
        cache = Cache(cache_dir=temp_cache_dir)
        assert os.path.exists(cache.cache_dir)

    def test_compute_hash(self):
        """Test hash computation."""
        data = "test function code"
        hash1 = compute_hash(data)
        hash2 = compute_hash(data)
        hash3 = compute_hash("different code")

        assert len(hash1) == 64  # SHA-256 hex length
        assert hash1 == hash2
        assert hash1 != hash3

    def test_set_and_get(self, temp_cache_dir):
        """Test setting and getting a value."""
        cache = Cache(cache_dir=temp_cache_dir)
        key = compute_hash("test data")
        data = {"result": "success", "metrics": {"complexity": 5}}

        cache.set(key, data)
        retrieved = cache.get(key)

        assert retrieved is not None
        assert retrieved == data

    def test_get_nonexistent_key(self, temp_cache_dir):
        """Test getting a key that doesn't exist."""
        cache = Cache(cache_dir=temp_cache_dir)
        key = "nonexistent_hash_12345678901234567890123456789012345678901234567890"

        retrieved = cache.get(key)
        assert retrieved is None

    def test_cache_expiration(self, temp_cache_dir):
        """Test that expired cache entries are removed."""
        cache = Cache(cache_dir=temp_cache_dir, ttl_days=0)  # Immediate expiration
        key = compute_hash("test data")
        data = {"result": "expired"}

        # Manually create an expired entry
        cache_path = cache._get_cache_path(key)
        entry = {
            'timestamp': (datetime.now() - timedelta(days=1)).isoformat(),
            'data': data
        }
        with open(cache_path, 'w') as f:
            json.dump(entry, f)

        retrieved = cache.get(key)
        assert retrieved is None
        assert not cache_path.exists()

    def test_clear_cache(self, temp_cache_dir):
        """Test clearing the cache."""
        cache = Cache(cache_dir=temp_cache_dir)

        # Add some entries
        for i in range(3):
            key = compute_hash(f"data_{i}")
            cache.set(key, {"index": i})

        count = cache.clear()
        assert count == 3

        # Verify files are gone
        assert len(list(Path(temp_cache_dir).glob("*.json"))) == 0

    def test_cache_stats(self, temp_cache_dir):
        """Test cache statistics."""
        cache = Cache(cache_dir=temp_cache_dir)

        # Add some entries
        for i in range(5):
            key = compute_hash(f"data_{i}")
            cache.set(key, {"index": i})

        stats = cache.stats()

        assert stats['total_files'] == 5
        assert stats['valid_entries'] == 5
        assert stats['expired_entries'] == 0
        assert stats['cache_dir'] == temp_cache_dir

    def test_corrupted_cache_entry(self, temp_cache_dir):
        """Test handling of corrupted cache entries."""
        cache = Cache(cache_dir=temp_cache_dir)
        key = compute_hash("test data")

        # Create a corrupted file
        cache_path = cache._get_cache_path(key)
        with open(cache_path, 'w') as f:
            f.write("not valid json {{{")

        retrieved = cache.get(key)
        assert retrieved is None
        assert not cache_path.exists()

    def test_unicode_data(self, temp_cache_dir):
        """Test caching unicode data."""
        cache = Cache(cache_dir=temp_cache_dir)
        key = compute_hash("unicode test")
        data = {"code": "def foo():\n    return '日本語'", "metrics": {"unicode": True}}

        cache.set(key, data)
        retrieved = cache.get(key)

        assert retrieved == data

    def test_large_data(self, temp_cache_dir):
        """Test caching larger data structures."""
        cache = Cache(cache_dir=temp_cache_dir)
        key = compute_hash("large data")
        data = {
            "code": "x = " + "a" * 10000,
            "metrics": {k: v for k, v in enumerate(range(1000))}
        }

        cache.set(key, data)
        retrieved = cache.get(key)

        assert retrieved == data

class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary directory for cache files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_get_cache_singleton(self, temp_cache_dir):
        """Test that get_cache returns a singleton."""
        # Reset the global cache
        import code.utils.cache as cache_module
        cache_module._default_cache = None

        cache1 = cache_module.get_cache(cache_dir=temp_cache_dir)
        cache2 = cache_module.get_cache()

        assert cache1 is cache2

    def test_cache_get_set_convenience(self, temp_cache_dir):
        """Test convenience functions."""
        import code.utils.cache as cache_module
        cache_module._default_cache = None

        # Set the default cache to our temp directory
        cache_module._default_cache = Cache(cache_dir=temp_cache_dir)

        key = compute_hash("convenience test")
        data = {"test": "value"}

        cache_set(key, data)
        retrieved = cache_get(key)

        assert retrieved == data