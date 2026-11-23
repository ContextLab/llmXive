"""
Unit tests for T040: Verify streaming memory trigger logic.

Tests that streaming.py correctly triggers batch processing at memory threshold.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import gc

# Add code/src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.pipeline.streaming import (
    get_current_memory_usage_bytes,
    should_trigger_batch_processing,
    trigger_memory_cleanup,
    process_batch_with_memory_check
)


class TestMemoryUsage:
    """Tests for memory usage detection functions."""

    @patch('src.pipeline.streaming.psutil.Process')
    def test_get_current_memory_usage_bytes_returns_number(self, mock_process):
        """Test that memory usage function returns a numeric value."""
        # Mock process to return a specific memory usage
        mock_proc_instance = MagicMock()
        mock_proc_instance.memory_info.return_value = MagicMock(rss=1024 * 1024 * 100)  # 100MB
        mock_process.return_value = mock_proc_instance
        
        memory = get_current_memory_usage_bytes()
        
        assert isinstance(memory, (int, float))
        assert memory > 0
        mock_process.assert_called_once()
        mock_proc_instance.memory_info.assert_called_once()


class TestBatchProcessingTrigger:
    """Tests for batch processing trigger logic."""

    def test_should_trigger_batch_processing_below_threshold(self):
        """Test trigger logic when memory is below threshold."""
        # Mock memory usage to be 5 GB (below 6.5 GB threshold)
        mock_memory = 5 * 1024 * 1024 * 1024  # 5 GB in bytes
        
        with patch('src.pipeline.streaming.get_current_memory_usage_bytes', return_value=mock_memory):
            result = should_trigger_batch_processing(threshold_bytes=6.5 * 1024 * 1024 * 1024)
            
            assert result is False

    def test_should_trigger_batch_processing_above_threshold(self):
        """Test trigger logic when memory exceeds threshold."""
        # Mock memory usage to be 7 GB (above 6.5 GB threshold)
        mock_memory = 7 * 1024 * 1024 * 1024  # 7 GB in bytes
        
        with patch('src.pipeline.streaming.get_current_memory_usage_bytes', return_value=mock_memory):
            result = should_trigger_batch_processing(threshold_bytes=6.5 * 1024 * 1024 * 1024)
            
            assert result is True

    def test_should_trigger_batch_processing_at_exact_threshold(self):
        """Test trigger logic when memory is exactly at threshold."""
        threshold = 6.5 * 1024 * 1024 * 1024
        
        with patch('src.pipeline.streaming.get_current_memory_usage_bytes', return_value=threshold):
            result = should_trigger_batch_processing(threshold_bytes=threshold)
            
            # Should trigger when at or above threshold
            assert result is True


class TestMemoryCleanup:
    """Tests for memory cleanup functions."""

    @patch('src.pipeline.streaming.gc.collect')
    @patch('src.pipeline.streaming.gc.garbage')
    def test_trigger_memory_cleanup_calls_gc(self, mock_garbage, mock_collect):
        """Test that cleanup function calls garbage collection."""
        # Mock garbage list to have items
        mock_garbage.__len__.return_value = 10
        
        trigger_memory_cleanup()
        
        mock_collect.assert_called_once()
        assert mock_collect.call_count >= 1

    @patch('src.pipeline.streaming.gc.collect')
    @patch('src.pipeline.streaming.gc.garbage')
    def test_trigger_memory_cleanup_returns_cleared_count(self, mock_garbage, mock_collect):
        """Test that cleanup function returns count of cleared objects."""
        mock_garbage.__len__.return_value = 100
        
        result = trigger_memory_cleanup()
        
        assert isinstance(result, int)
        assert result >= 0
