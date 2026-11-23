"""
Unit tests for the caching mechanism.
"""
import json
import os
import time
import tempfile
from pathlib import Path
import pytest

from utils.cache import Cache, CacheError

@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_cache_init_creates_directory(temp_cache_dir):
    """Test that Cache initialization creates the directory."""
    cache = Cache(cache_dir=temp_cache_dir)
    assert Path(temp_cache_dir).exists()
    assert cache.cache_dir == Path(temp_cache_dir)

def test_compute_hash(temp_cache_dir):
    """Test hash computation."""
    cache = Cache(cache_dir=temp_cache_dir)
    data = "def hello(): pass"
    hash1 = cache.compute_hash(data)
    hash2 = cache.compute_hash(data)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex length
    
    # Different data should produce different hash
    hash3 = cache.compute_hash("def world(): pass")
    assert hash1 != hash3

def test_set_and_get(temp_cache_dir):
    """Test basic set and get operations."""
    cache = Cache(cache_dir=temp_cache_dir)
    key = "test_key_123"
    value = {"code": "print('hello')", "metrics": {"loc": 1}}
    
    cache.set(key, value)
    retrieved = cache.get(key)
    
    assert retrieved == value

def test_get_missing_key(temp_cache_dir):
    """Test getting a non-existent key returns None."""
    cache = Cache(cache_dir=temp_cache_dir)
    result = cache.get("non_existent_key")
    assert result is None

def test_cache_clear(temp_cache_dir):
    """Test clearing the cache."""
    cache = Cache(cache_dir=temp_cache_dir)
    
    cache.set("key1", {"data": 1})
    cache.set("key2", {"data": 2})
    assert len(list(Path(temp_cache_dir).glob("*.json"))) == 2
    
    cache.clear()
    assert len(list(Path(temp_cache_dir).glob("*.json"))) == 0

def test_cache_delete(temp_cache_dir):
    """Test deleting a specific key."""
    cache = Cache(cache_dir=temp_cache_dir)
    
    cache.set("key1", {"data": 1})
    cache.set("key2", {"data": 2})
    
    assert cache.delete("key1") is True
    assert cache.get("key1") is None
    assert cache.get("key2") == {"data": 2}
    
    assert cache.delete("non_existent") is False

def test_cache_ttl_expiration(temp_cache_dir):
    """Test that cache entries expire after TTL."""
    cache = Cache(cache_dir=temp_cache_dir, ttl_seconds=1)
    
    key = "ttl_test"
    cache.set(key, {"data": "value"})
    assert cache.get(key) == {"data": "value"}
    
    # Wait for expiration
    time.sleep(1.1)
    assert cache.get(key) is None

def test_cache_ttl_no_expiration(temp_cache_dir):
    """Test that cache entries do not expire before TTL."""
    cache = Cache(cache_dir=temp_cache_dir, ttl_seconds=10)
    
    key = "ttl_no_expire"
    cache.set(key, {"data": "value"})
    
    # Should still be valid
    retrieved = cache.get(key)
    assert retrieved == {"data": "value"}

def test_cache_corrupted_file(temp_cache_dir):
    """Test handling of corrupted cache files."""
    cache = Cache(cache_dir=temp_cache_dir)
    key = "corrupted"
    
    # Create a corrupted file
    path = Path(temp_cache_dir) / f"{key}.json"
    with open(path, 'w') as f:
        f.write("{ invalid json }")
    
    # Should return None and not crash
    result = cache.get(key)
    assert result is None
    
    # File should be removed
    assert not path.exists()

def test_cache_stats(temp_cache_dir):
    """Test cache statistics."""
    cache = Cache(cache_dir=temp_cache_dir)
    
    cache.set("key1", {"data": "a" * 100})
    cache.set("key2", {"data": "b" * 200})
    
    stats = cache.stats()
    assert stats['entry_count'] == 2
    assert stats['cache_dir'] == temp_cache_dir
    assert stats['total_size_bytes'] > 0
    assert stats['ttl_seconds'] == 86400  # Default TTL

def test_cache_set_error_handling(temp_cache_dir):
    """Test error handling when writing fails."""
    # Make directory read-only to simulate write error
    os.chmod(temp_cache_dir, 0o444)
    cache = Cache(cache_dir=temp_cache_dir)
    
    with pytest.raises(CacheError):
        cache.set("key", {"data": "value"})
    
    # Restore permissions for cleanup
    os.chmod(temp_cache_dir, 0o755)
