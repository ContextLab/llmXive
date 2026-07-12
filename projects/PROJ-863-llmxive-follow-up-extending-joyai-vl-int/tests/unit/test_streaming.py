"""
Unit tests for streaming and batching utilities.
"""

import gc
import os
import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.feature_extraction.streaming import (
    ChunkedFrameIterator,
    MemoryLimitExceeded,
    MemoryMonitor,
    create_batched_iterator,
    log_memory_snapshot,
    process_stream,
)

@pytest.fixture
def mock_frames():
    """Generates a list of mock frames."""
    return [np.random.rand(100, 100, 3).astype(np.float32) for _ in range(50)]

@pytest.fixture
def frame_generator(mock_frames):
    """Returns a generator for mock frames."""
    return iter(mock_frames)

class TestMemoryMonitor:
    def test_initialization(self):
        monitor = MemoryMonitor(limit_gb=6.0)
        assert monitor.limit_bytes == 6.0 * 1024**3
        assert monitor.get_current_usage() > 0

    def test_current_usage_gb(self):
        monitor = MemoryMonitor()
        usage_gb = monitor.get_current_usage_gb()
        assert isinstance(usage_gb, float)
        assert usage_gb > 0

    def test_peak_tracking(self):
        monitor = MemoryMonitor()
        initial_peak = monitor.get_peak_usage()
        monitor.update_peak()
        assert monitor.get_peak_usage() >= initial_peak

    def test_check_limit_within(self):
        monitor = MemoryMonitor(limit_gb=1000.0)  # Very high limit
        assert monitor.check_limit() is True

    def test_check_limit_exceeded(self, capsys):
        # Create a mock that simulates high memory
        with patch("psutil.Process") as MockProcess:
            mock_proc = MagicMock()
            mock_proc.memory_info.return_value = MagicMock(rss=10**12)  # 1TB
            MockProcess.return_value = mock_proc
            
            monitor = MemoryMonitor(limit_gb=1.0)
            assert monitor.check_limit() is False

    def test_force_gc(self):
        monitor = MemoryMonitor()
        # Just ensure it doesn't crash
        monitor.force_gc()

class TestChunkedFrameIterator:
    def test_basic_iteration(self, frame_generator):
        iterator = ChunkedFrameIterator(frame_generator, chunk_size=10)
        chunks = list(iterator)
        assert len(chunks) == 5  # 50 frames / 10 = 5 chunks
        assert len(chunks[0]) == 10

    def test_partial_final_chunk(self, mock_frames):
        # 51 frames, chunk size 10 -> 5 full, 1 partial
        gen = iter(mock_frames + [np.random.rand(10, 10, 3)])
        iterator = ChunkedFrameIterator(gen, chunk_size=10)
        chunks = list(iterator)
        assert len(chunks) == 6
        assert len(chunks[-1]) == 1

    def test_empty_generator(self):
        iterator = ChunkedFrameIterator(iter([]), chunk_size=10)
        chunks = list(iterator)
        assert len(chunks) == 0

    def test_memory_enforcement(self, mock_frames):
        # Mock a monitor that fails after first chunk
        mock_monitor = MagicMock(spec=MemoryMonitor)
        mock_monitor.limit_bytes = 10**12
        mock_monitor.get_current_usage.return_value = 10**11
        mock_monitor.update_peak = MagicMock()
        mock_monitor.check_limit = MagicMock(side_effect=[True, False])
        mock_monitor.force_gc = MagicMock()
        mock_monitor.enforce_limit = MagicMock()

        iterator = ChunkedFrameIterator(iter(mock_frames), chunk_size=10, monitor=mock_monitor)
        
        # First chunk succeeds
        chunk1 = next(iterator)
        assert len(chunk1) == 10
        
        # Second chunk should raise MemoryLimitExceeded
        with pytest.raises(MemoryLimitExceeded):
            next(iterator)

class TestProcessStream:
    def test_stream_processing(self, frame_generator):
        results = []
        def processor(chunk):
            results.append(len(chunk))
            return len(chunk)
        
        output = list(process_stream(frame_generator, processor, chunk_size=10))
        assert len(output) == 5
        assert all(r == 10 for r in output)

    def test_memory_limit_triggered(self, mock_frames):
        mock_monitor = MagicMock(spec=MemoryMonitor)
        mock_monitor.limit_bytes = 10**12
        mock_monitor.check_limit = MagicMock(side_effect=[True, False])
        mock_monitor.force_gc = MagicMock()
        mock_monitor.update_peak = MagicMock()

        def processor(chunk):
            return chunk

        with pytest.raises(MemoryLimitExceeded):
            list(process_stream(iter(mock_frames), processor, chunk_size=10, monitor=mock_monitor))

    def test_gc_cleanup(self, frame_generator):
        # Ensure GC is called
        gc.collect()
        results = list(process_stream(frame_generator, lambda c: c, chunk_size=10))
        assert len(results) == 5

class TestCreateBatchedIterator:
    def test_batching(self):
        data = list(range(10))
        batches = list(create_batched_iterator(iter(data), batch_size=3))
        assert len(batches) == 4
        assert batches[0] == [0, 1, 2]
        assert batches[-1] == [9]

    def test_empty_input(self):
        batches = list(create_batched_iterator(iter([]), batch_size=3))
        assert len(batches) == 0

    def test_exact_multiple(self):
        data = list(range(9))
        batches = list(create_batched_iterator(iter(data), batch_size=3))
        assert len(batches) == 3
        assert all(len(b) == 3 for b in batches)

class TestLogMemorySnapshot:
    def test_log_output(self, capsys):
        log_memory_snapshot("Test")
        captured = capsys.readouterr()
        assert "Current:" in captured.out
        assert "Peak:" in captured.out
        assert "Limit:" in captured.out