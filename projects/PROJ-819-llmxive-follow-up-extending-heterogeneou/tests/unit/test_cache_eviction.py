import os
import json
import tempfile
import time
import pytest
import numpy as np
from pathlib import Path

from cache.semantic_cache import CacheEntry, SemanticCache

@pytest.fixture
def temp_log_file():
    """Create a temporary file for eviction logging."""
    fd, path = tempfile.mkstemp(suffix='.log')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)

@pytest.fixture
def sample_embedding():
    """Generate a sample embedding vector."""
    return np.random.rand(768).astype(np.float32)

def test_lru_eviction_policy(temp_log_file, sample_embedding):
    """Test that LRU eviction works and logs events."""
    cache = SemanticCache(max_size=3, eviction_log_path=temp_log_file)
    
    # Add 3 entries (filling the cache)
    entry1 = CacheEntry(
        embedding=sample_embedding,
        output="output1",
        timestamp=time.time(),
        prompt="prompt1"
    )
    entry2 = CacheEntry(
        embedding=sample_embedding,
        output="output2",
        timestamp=time.time(),
        prompt="prompt2"
    )
    entry3 = CacheEntry(
        embedding=sample_embedding,
        output="output3",
        timestamp=time.time(),
        prompt="prompt3"
    )
    
    cache.set("key1", entry1)
    cache.set("key2", entry2)
    cache.set("key3", entry3)
    
    assert len(cache) == 3
    
    # Access key1 to make it recently used
    cache.get("key1")
    
    # Add a 4th entry - should evict key2 (oldest)
    entry4 = CacheEntry(
        embedding=sample_embedding,
        output="output4",
        timestamp=time.time(),
        prompt="prompt4"
    )
    
    # Check log file before
    initial_log_size = 0
    if os.path.exists(temp_log_file):
        with open(temp_log_file, 'r') as f:
            initial_log_size = sum(1 for _ in f)
    
    cache.set("key4", entry4)
    
    # Verify eviction happened
    assert len(cache) == 3
    assert "key1" in cache
    assert "key3" in cache
    assert "key4" in cache
    assert "key2" not in cache  # Should be evicted
    
    # Verify log file was updated
    assert os.path.exists(temp_log_file)
    with open(temp_log_file, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == initial_log_size + 1
    
    # Verify log content
    log_data = json.loads(lines[-1])
    assert log_data["evicted_key"] == "key2"
    assert log_data["evicted_prompt"] == "prompt2"
    assert log_data["reason"] == "LRU_EVICTION_LIMIT_EXCEEDED"

def test_no_eviction_when_below_limit(temp_log_file, sample_embedding):
    """Test that no eviction occurs when cache is not full."""
    cache = SemanticCache(max_size=5, eviction_log_path=temp_log_file)
    
    entry = CacheEntry(
        embedding=sample_embedding,
        output="output",
        timestamp=time.time(),
        prompt="prompt"
    )
    
    cache.set("key1", entry)
    
    # No log entries should exist
    if os.path.exists(temp_log_file):
        with open(temp_log_file, 'r') as f:
            content = f.read()
        assert len(content.strip()) == 0

def test_update_existing_key_no_eviction(temp_log_file, sample_embedding):
    """Test that updating an existing key does not cause eviction."""
    cache = SemanticCache(max_size=2, eviction_log_path=temp_log_file)
    
    entry1 = CacheEntry(
        embedding=sample_embedding,
        output="output1",
        timestamp=time.time(),
        prompt="prompt1"
    )
    entry2 = CacheEntry(
        embedding=sample_embedding,
        output="output2",
        timestamp=time.time(),
        prompt="prompt2"
    )
    
    cache.set("key1", entry1)
    cache.set("key2", entry2)
    
    # Update key1
    entry1_updated = CacheEntry(
        embedding=sample_embedding,
        output="output1_updated",
        timestamp=time.time(),
        prompt="prompt1_updated"
    )
    
    cache.set("key1", entry1_updated)
    
    # Should still be 2 entries, no eviction
    assert len(cache) == 2
    assert cache.get("key1").output == "output1_updated"
    
    # No new log entries
    with open(temp_log_file, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 0  # No evictions happened

def test_eviction_log_path_creation(temp_log_file, sample_embedding):
    """Test that the log directory is created if it doesn't exist."""
    # Create a path in a non-existent directory
    temp_dir = tempfile.mkdtemp()
    nested_log_path = os.path.join(temp_dir, "subdir", "eviction.log")
    
    cache = SemanticCache(max_size=1, eviction_log_path=nested_log_path)
    
    entry = CacheEntry(
        embedding=sample_embedding,
        output="output",
        timestamp=time.time(),
        prompt="prompt"
    )
    
    cache.set("key1", entry)
    cache.set("key2", entry)  # This should evict key1
    
    # Verify log file exists
    assert os.path.exists(nested_log_path)
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
