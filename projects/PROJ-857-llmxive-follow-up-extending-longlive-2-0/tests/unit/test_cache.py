"""
Unit tests for the CacheManager LRU eviction policy.
"""
import os
import tempfile
import time
from pathlib import Path
import pytest

from code.data.cache import CacheManager


@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_cache_put_and_get(temp_cache_dir):
    """Test basic put and get operations."""
    manager = CacheManager(max_size_gb=1.0, cache_dir=str(temp_cache_dir))
    
    # Create a source file
    source = temp_cache_dir / "source.txt"
    source.write_text("test data")
    
    # Put into cache
    cached_path = manager.put("key1", source)
    
    # Verify it exists
    assert cached_path.exists()
    assert cached_path.read_text() == "test data"
    
    # Verify LRU update
    assert "key1" in manager._lru


def test_lru_eviction(temp_cache_dir):
    """Test that LRU eviction removes the oldest file when limit is reached."""
    # Set max size to 100 bytes
    manager = CacheManager(max_size_gb=1e-7, cache_dir=str(temp_cache_dir)) # ~100 bytes
    
    # Create source files
    file1 = temp_cache_dir / "file1.txt"
    file1.write_text("a" * 50)
    
    file2 = temp_cache_dir / "file2.txt"
    file2.write_text("b" * 50)
    
    file3 = temp_cache_dir / "file3.txt"
    file3.write_text("c" * 50)
    
    # Add file1
    manager.put("k1", file1)
    time.sleep(0.1) # Ensure distinct timestamps
    
    # Add file2
    manager.put("k2", file2)
    time.sleep(0.1)
    
    # Add file3 (should evict k1)
    manager.put("k3", file3)
    
    # k1 should be gone
    assert not manager.get("k1").exists() if manager.get("k1") else True
    assert not (temp_cache_dir / "k1").exists()
    
    # k2 and k3 should exist
    assert manager.get("k2").exists()
    assert manager.get("k3").exists()


def test_lru_access_order(temp_cache_dir):
    """Test that accessing a file updates its LRU order."""
    manager = CacheManager(max_size_gb=1e-7, cache_dir=str(temp_cache_dir))
    
    file1 = temp_cache_dir / "file1.txt"
    file1.write_text("a" * 50)
    
    file2 = temp_cache_dir / "file2.txt"
    file2.write_text("b" * 50)
    
    file3 = temp_cache_dir / "file3.txt"
    file3.write_text("c" * 50)
    
    # Add k1, k2
    manager.put("k1", file1)
    time.sleep(0.1)
    manager.put("k2", file2)
    time.sleep(0.1)
    
    # Access k1 to make it "newer"
    manager.get("k1")
    time.sleep(0.1)
    
    # Add k3 (should evict k2, the oldest)
    manager.put("k3", file3)
    
    # k2 should be gone
    assert not (temp_cache_dir / "k2").exists()
    # k1 and k3 should exist
    assert (temp_cache_dir / "k1").exists()
    assert (temp_cache_dir / "k3").exists()


def test_file_exceeds_max_size(temp_cache_dir):
    """Test that a file larger than max size raises an error."""
    manager = CacheManager(max_size_gb=1e-7, cache_dir=str(temp_cache_dir))
    
    large_file = temp_cache_dir / "large.txt"
    large_file.write_text("x" * 200) # Larger than max
    
    with pytest.raises(OSError):
        manager.put("huge", large_file)


def test_cache_clear(temp_cache_dir):
    """Test clearing the cache."""
    manager = CacheManager(max_size_gb=1.0, cache_dir=str(temp_cache_dir))
    
    source = temp_cache_dir / "src.txt"
    source.write_text("data")
    
    manager.put("k1", source)
    assert (temp_cache_dir / "k1").exists()
    
    manager.clear()
    assert not (temp_cache_dir / "k1").exists()
    assert len(manager._lru) == 0


def test_remove(temp_cache_dir):
    """Test removing a specific key."""
    manager = CacheManager(max_size_gb=1.0, cache_dir=str(temp_cache_dir))
    
    source = temp_cache_dir / "src.txt"
    source.write_text("data")
    
    manager.put("k1", source)
    assert manager.remove("k1") is True
    assert not (temp_cache_dir / "k1").exists()
    assert "k1" not in manager._lru
    
    assert manager.remove("nonexistent") is False
