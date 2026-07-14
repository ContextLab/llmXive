"""
Unit tests for memory management utilities.
"""
import pytest
import gc
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.memory_manager import (
    MemoryMonitor,
    MemoryExhaustedError,
    memory_limited,
    LRUContextCache,
    get_global_monitor,
    batch_process_with_memory_control,
    DEFAULT_MEMORY_LIMIT_MB,
    DEFAULT_CACHE_SIZE
)

class TestMemoryMonitor:
    """Tests for MemoryMonitor class."""
    
    def test_init_default_limit(self):
        """Test initialization with default limit."""
        monitor = MemoryMonitor()
        assert monitor.limit_mb == DEFAULT_MEMORY_LIMIT_MB
        assert monitor.limit_bytes == DEFAULT_MEMORY_LIMIT_MB * 1024 * 1024
    
    def test_init_custom_limit(self):
        """Test initialization with custom limit."""
        custom_limit = 4000
        monitor = MemoryMonitor(limit_mb=custom_limit)
        assert monitor.limit_mb == custom_limit
        assert monitor.limit_bytes == custom_limit * 1024 * 1024
    
    def test_get_current_usage_mb(self):
        """Test that get_current_usage_mb returns a number."""
        monitor = MemoryMonitor()
        usage = monitor.get_current_usage_mb()
        assert isinstance(usage, float)
        assert usage >= 0
    
    @patch('utils.memory_manager.gc.collect')
    def test_check_and_throttle_normal(self, mock_gc):
        """Test that check_and_throttle returns False when under limit."""
        monitor = MemoryMonitor(limit_mb=1000)
        
        # Mock usage to be low
        with patch.object(monitor, 'get_current_usage_mb', return_value=100.0):
            result = monitor.check_and_throttle()
            assert result is False
            mock_gc.assert_not_called()
    
    @patch('utils.memory_manager.gc.collect')
    def test_check_and_throttle_warning(self, mock_gc):
        """Test cleanup when usage is at warning level."""
        monitor = MemoryMonitor(limit_mb=1000)
        
        # Mock usage to be at 75%
        with patch.object(monitor, 'get_current_usage_mb', return_value=750.0):
            result = monitor.check_and_throttle()
            assert result is True
            mock_gc.assert_called()
    
    def test_register_cache_clear(self):
        """Test registering a cache clear callback."""
        monitor = MemoryMonitor()
        callback_called = [False]
        
        def dummy_callback():
            callback_called[0] = True
        
        monitor.register_cache_clear(dummy_callback)
        
        # Trigger cleanup
        with patch.object(monitor, 'get_current_usage_mb', return_value=800.0):
            monitor.check_and_throttle()
        
        assert callback_called[0] is True
    
    def test_emergency_cleanup_raises_on_critical(self):
        """Test that emergency cleanup raises on critical memory."""
        monitor = MemoryMonitor(limit_mb=1000)
        
        # Mock critical usage
        with patch.object(monitor, 'get_current_usage_mb', return_value=960.0):
            with pytest.raises(MemoryExhaustedError):
                monitor._emergency_cleanup()

class TestLRUContextCache:
    """Tests for LRUContextCache class."""
    
    def test_init(self):
        """Test initialization."""
        cache = LRUContextCache(max_size=10)
        assert cache.max_size == 10
        assert len(cache) == 0
    
    def test_put_and_get(self):
        """Test basic put and get operations."""
        cache = LRUContextCache(max_size=5)
        cache.put("key1", "value1")
        
        assert cache.get("key1") == "value1"
        assert cache.get("nonexistent") is None
    
    def test_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = LRUContextCache(max_size=3)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Add one more to trigger eviction
        cache.put("key4", "value4")
        
        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
    
    def test_access_order_update(self):
        """Test that accessing an item updates its order."""
        cache = LRUContextCache(max_size=3)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Access key1 to make it most recently used
        cache.get("key1")
        
        # Add key4, should evict key2 (not key1)
        cache.put("key4", "value4")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
    
    def test_clear(self):
        """Test clearing the cache."""
        cache = LRUContextCache(max_size=5)
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        cache.clear()
        
        assert len(cache) == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None

class TestMemoryLimitedContextManager:
    """Tests for memory_limited context manager."""
    
    def test_context_manager_execution(self):
        """Test that context manager executes successfully."""
        with memory_limited(5000) as monitor:
            assert monitor is not None
            assert monitor.limit_mb == 5000
    
    def test_gc_restoration(self):
        """Test that GC threshold is restored after context."""
        original_threshold = gc.get_threshold()
        
        with memory_limited(5000):
            # Inside context, GC threshold might be changed
            pass
        
        # After context, it should be restored
        assert gc.get_threshold() == original_threshold

class TestBatchProcessWithMemoryControl:
    """Tests for batch_process_with_memory_control function."""
    
    def test_basic_processing(self):
        """Test basic batch processing."""
        items = [1, 2, 3, 4, 5]
        results = batch_process_with_memory_control(
            items, 
            lambda x: x * 2,
            batch_size=2
        )
        
        assert results == [2, 4, 6, 8, 10]
    
    def test_error_handling(self):
        """Test that errors in processing don't stop the whole batch."""
        items = [1, 2, 3, 4, 5]
        
        def processor(x):
            if x == 3:
                raise ValueError("Test error")
            return x * 2
        
        results = batch_process_with_memory_control(
            items, 
            processor,
            batch_size=2
        )
        
        # Should have None for the failed item
        assert results[0] == 2
        assert results[1] == 4
        assert results[2] is None
        assert results[3] == 8
        assert results[4] == 10
    
    def test_memory_monitor_integration(self):
        """Test integration with memory monitor."""
        items = [1, 2, 3]
        monitor = MemoryMonitor(limit_mb=1000)
        
        results = batch_process_with_memory_control(
            items,
            lambda x: x * 2,
            batch_size=1,
            memory_monitor=monitor
        )
        
        assert results == [2, 4, 6]

class TestGlobalMonitor:
    """Tests for global monitor functionality."""
    
    def test_get_global_monitor_singleton(self):
        """Test that get_global_monitor returns the same instance."""
        monitor1 = get_global_monitor()
        monitor2 = get_global_monitor()
        
        assert monitor1 is monitor2
    
    def test_global_monitor_default_limit(self):
        """Test that global monitor uses default limit."""
        monitor = get_global_monitor()
        assert monitor.limit_mb == DEFAULT_MEMORY_LIMIT_MB

if __name__ == "__main__":
    pytest.main([__file__, "-v"])