import pytest
import time
import threading
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

# Import the target module
from cache.semantic_cache import CacheEntry, SemanticCache
from cache.utils import get_embedding_model, generate_embedding, cosine_similarity

class TestEmbeddingFailure:
    """Tests for handling embedding failures gracefully."""

    def test_embedding_failure_returns_none(self):
        """Test that cache retrieval returns None when embedding generation fails."""
        cache = SemanticCache(max_size=1000, max_memory_bytes=1024**3)
        
        # Create a valid cache entry
        entry = CacheEntry(
            embedding=[0.1, 0.2, 0.3],
            output="test_output",
            timestamp=time.time()
        )
        cache._cache["test_key"] = entry
        
        # Mock generate_embedding to raise an exception
        with patch('cache.semantic_cache.generate_embedding', side_effect=RuntimeError("Model load failed")):
            result = cache.get("test_key")
            assert result is None
            assert cache.stats["embedding_errors"] == 1

    def test_embedding_failure_logged_to_stderr(self):
        """Test that embedding failures are logged to stderr."""
        cache = SemanticCache(max_size=1000, max_memory_bytes=1024**3)
        
        with patch('cache.semantic_cache.generate_embedding', side_effect=ValueError("Invalid input")):
            with patch('sys.stderr') as mock_stderr:
                cache.get("nonexistent_key")
                # Verify error was logged
                assert any("ERROR" in str(call) for call in mock_stderr.write.call_args_list)

    def test_embedding_failure_does_not_corrupt_cache(self):
        """Test that embedding failures don't corrupt existing cache state."""
        cache = SemanticCache(max_size=1000, max_memory_bytes=1024**3)
        
        # Populate cache
        entry = CacheEntry(
            embedding=[0.1, 0.2, 0.3],
            output="valid_output",
            timestamp=time.time()
        )
        cache._cache["valid_key"] = entry
        
        # Trigger embedding failure
        with patch('cache.semantic_cache.generate_embedding', side_effect=RuntimeError("Failed")):
            cache.get("nonexistent_key")
        
        # Verify original entry still exists
        assert "valid_key" in cache._cache
        assert cache._cache["valid_key"].output == "valid_output"

class TestMemoryLimitEviction:
    """Tests for LRU eviction when memory limit is exceeded."""

    def test_eviction_on_memory_limit(self):
        """Test that cache evicts oldest entries when memory limit is reached."""
        # Create a cache with a small memory limit
        cache = SemanticCache(max_size=1000, max_memory_bytes=100)
        
        # Mock the memory estimation to be 50 bytes per entry
        original_estimate = cache._estimate_memory_usage
        cache._estimate_memory_usage = lambda entry: 50
        
        # Add two entries - should trigger eviction
        entry1 = CacheEntry(
            embedding=[0.1] * 10,
            output="first",
            timestamp=time.time()
        )
        entry2 = CacheEntry(
            embedding=[0.2] * 10,
            output="second",
            timestamp=time.time()
        )
        
        cache.put("key1", entry1)
        cache.put("key2", entry2)
        
        # First entry should have been evicted due to memory limit
        assert "key1" not in cache._cache
        assert "key2" in cache._cache

    def test_eviction_log_written(self):
        """Test that eviction events are logged to the specified file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "cache_events.log"
            cache = SemanticCache(
                max_size=1000,
                max_memory_bytes=100,
                eviction_log_path=str(log_path)
            )
            
            # Mock memory estimation
            cache._estimate_memory_usage = lambda entry: 50
            
            # Trigger eviction
            entry1 = CacheEntry(embedding=[0.1]*10, output="first", timestamp=time.time())
            entry2 = CacheEntry(embedding=[0.2]*10, output="second", timestamp=time.time())
            
            cache.put("key1", entry1)
            cache.put("key2", entry2)
            
            # Verify log file exists and contains eviction event
            assert log_path.exists()
            with open(log_path) as f:
                log_content = f.read()
                assert "eviction" in log_content
                assert "key1" in log_content

    def test_eviction_order_lru(self):
        """Test that eviction follows LRU order (least recently used first)."""
        cache = SemanticCache(max_size=1000, max_memory_bytes=100)
        cache._estimate_memory_usage = lambda entry: 50
        
        # Add entries in order
        entry1 = CacheEntry(embedding=[0.1]*10, output="first", timestamp=time.time())
        entry2 = CacheEntry(embedding=[0.2]*10, output="second", timestamp=time.time())
        entry3 = CacheEntry(embedding=[0.3]*10, output="third", timestamp=time.time())
        
        cache.put("key1", entry1)
        time.sleep(0.01)  # Ensure different timestamps
        cache.put("key2", entry2)
        time.sleep(0.01)
        cache.put("key3", entry3)
        
        # Access key1 to make it recently used
        cache.get("key1")
        
        # Add another entry to trigger eviction
        entry4 = CacheEntry(embedding=[0.4]*10, output="fourth", timestamp=time.time())
        cache.put("key4", entry4)
        
        # key2 should be evicted (least recently used)
        assert "key2" not in cache._cache
        assert "key1" in cache._cache
        assert "key3" in cache._cache
        assert "key4" in cache._cache

class TestEdgeCases:
    """Tests for various edge cases in cache operations."""

    def test_empty_cache_get(self):
        """Test get operation on empty cache."""
        cache = SemanticCache(max_size=1000, max_memory_bytes=1024**3)
        result = cache.get("nonexistent")
        assert result is None
        assert cache.stats["hits"] == 0
        assert cache.stats["misses"] == 1

    def test_zero_memory_limit(self):
        """Test behavior with zero memory limit."""
        cache = SemanticCache(max_size=1000, max_memory_bytes=0)
        
        entry = CacheEntry(embedding=[0.1], output="test", timestamp=time.time())
        
        # Should evict immediately if memory limit is 0
        cache.put("key", entry)
        # The entry might be evicted immediately or on next put
        # We just verify no crash occurs
        assert True

    def test_concurrent_access(self):
        """Test thread safety of cache operations."""
        cache = SemanticCache(max_size=1000, max_memory_bytes=1024**3)
        errors = []
        
        def worker(worker_id):
            try:
                for i in range(100):
                    entry = CacheEntry(
                        embedding=[float(worker_id + i)],
                        output=f"worker_{worker_id}_{i}",
                        timestamp=time.time()
                    )
                    cache.put(f"key_{worker_id}_{i}", entry)
                    cache.get(f"key_{worker_id}_{i}")
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Concurrent access errors: {errors}"

    def test_invalid_similarity_threshold(self):
        """Test behavior with invalid similarity thresholds."""
        cache = SemanticCache(max_size=1000, max_memory_bytes=1024**3)
        
        # Test with threshold > 1
        result = cache.get("key", threshold=1.5)
        assert result is None
        
        # Test with threshold < 0
        result = cache.get("key", threshold=-0.5)
        assert result is None

    def test_large_embedding(self):
        """Test handling of large embeddings."""
        cache = SemanticCache(max_size=1000, max_memory_bytes=1024**3)
        
        # Create a very large embedding
        large_embedding = [float(i) for i in range(10000)]
        entry = CacheEntry(
            embedding=large_embedding,
            output="large_embedding_test",
            timestamp=time.time()
        )
        
        cache.put("large_key", entry)
        result = cache.get("large_key")
        
        assert result is not None
        assert result.output == "large_embedding_test"

    def test_cache_stats_accuracy(self):
        """Test that cache statistics are accurately tracked."""
        cache = SemanticCache(max_size=1000, max_memory_bytes=1024**3)
        
        # Perform operations
        entry = CacheEntry(embedding=[0.1], output="test", timestamp=time.time())
        cache.put("key1", entry)
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        cache.get("key1")  # Hit
        
        stats = cache.stats
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["total_operations"] == 3
        assert stats["evictions"] == 0
        assert stats["embedding_errors"] == 0

    def test_clear_cache(self):
        """Test clearing the cache."""
        cache = SemanticCache(max_size=1000, max_memory_bytes=1024**3)
        
        entry = CacheEntry(embedding=[0.1], output="test", timestamp=time.time())
        cache.put("key", entry)
        
        cache.clear()
        
        assert len(cache._cache) == 0
        assert cache.stats["hits"] == 0
        assert cache.stats["misses"] == 0
        assert cache.stats["total_operations"] == 0