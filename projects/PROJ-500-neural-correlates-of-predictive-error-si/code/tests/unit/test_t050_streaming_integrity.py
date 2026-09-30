"""
Unit tests for T050: Streaming Integrity Monitor.

Tests that the integrity monitor correctly detects truncated streams
and raises appropriate errors.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
from unittest.mock import MagicMock, patch
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.ingest import (
    StreamingIntegrityMonitor,
    DataIntegrityError,
    stream_dataset_chunks,
    download_and_process_streaming
)

class TestStreamingIntegrityMonitor:
    """Tests for StreamingIntegrityMonitor class."""

    def test_monitor_initialization(self):
        """Test that monitor initializes correctly."""
        monitor = StreamingIntegrityMonitor(
            expected_rows=1000,
            expected_size_bytes=1024*1024,
            dataset_name="test_dataset"
        )
        
        assert monitor.dataset_name == "test_dataset"
        assert monitor.expected_rows == 1000
        assert monitor.expected_size_bytes == 1024*1024
        assert monitor.cumulative_rows == 0
        assert monitor.cumulative_bytes == 0

    def test_update_method(self):
        """Test that update method correctly accumulates counts."""
        monitor = StreamingIntegrityMonitor(dataset_name="test")
        
        monitor.update(bytes_processed=100, rows_processed=10)
        assert monitor.cumulative_bytes == 100
        assert monitor.cumulative_rows == 10
        
        monitor.update(bytes_processed=200, rows_processed=20)
        assert monitor.cumulative_bytes == 300
        assert monitor.cumulative_rows == 30

    def test_finalize_success(self):
        """Test that finalize succeeds when expectations are met."""
        monitor = StreamingIntegrityMonitor(
            expected_rows=100,
            expected_size_bytes=1000,
            dataset_name="test"
        )
        
        monitor.cumulative_rows = 100
        monitor.cumulative_bytes = 1000
        
        result = monitor.finalize()
        assert result is True

    def test_finalize_success_with_actual_values(self):
        """Test that finalize succeeds when actual values exceed expectations."""
        monitor = StreamingIntegrityMonitor(
            expected_rows=100,
            expected_size_bytes=1000,
            dataset_name="test"
        )
        
        result = monitor.finalize(actual_rows=150, actual_size_bytes=1500)
        assert result is True
        assert monitor.cumulative_rows == 150
        assert monitor.cumulative_bytes == 1500

    def test_finalize_failure_truncated_rows(self):
        """Test that finalize raises error when rows are truncated."""
        monitor = StreamingIntegrityMonitor(
            expected_rows=100,
            dataset_name="test_dataset"
        )
        
        monitor.cumulative_rows = 50
        
        with pytest.raises(DataIntegrityError) as exc_info:
            monitor.finalize()
        
        assert "truncated" in str(exc_info.value).lower()
        assert "test_dataset" in str(exc_info.value)

    def test_finalize_failure_truncated_bytes(self):
        """Test that finalize raises error when bytes are truncated."""
        monitor = StreamingIntegrityMonitor(
            expected_size_bytes=1000,
            dataset_name="test_dataset"
        )
        
        monitor.cumulative_bytes = 500
        
        with pytest.raises(DataIntegrityError) as exc_info:
            monitor.finalize()
        
        assert "truncated" in str(exc_info.value).lower()
        assert "test_dataset" in str(exc_info.value)

    def test_finalize_no_expectations(self):
        """Test that finalize succeeds when no expectations are set."""
        monitor = StreamingIntegrityMonitor(dataset_name="test")
        
        monitor.cumulative_rows = 50
        monitor.cumulative_bytes = 500
        
        result = monitor.finalize()
        assert result is True

    def test_get_report(self):
        """Test that get_report returns correct data."""
        monitor = StreamingIntegrityMonitor(
            expected_rows=100,
            expected_size_bytes=1000,
            dataset_name="test"
        )
        
        monitor.cumulative_rows = 80
        monitor.cumulative_bytes = 800
        
        report = monitor.get_report()
        
        assert report["dataset_name"] == "test"
        assert report["expected_rows"] == 100
        assert report["expected_bytes"] == 1000
        assert report["actual_rows"] == 80
        assert report["actual_bytes"] == 800
        assert report["integrity_passed"] is False

class TestStreamDatasetChunks:
    """Tests for stream_dataset_chunks function."""

    def test_stream_dataset_chunks_basic(self):
        """Test basic streaming functionality."""
        # Create mock dataset iterator
        mock_data = [
            {"col1": 1, "col2": "a"},
            {"col1": 2, "col2": "b"},
            {"col1": 3, "col2": "c"}
        ]
        
        def mock_iterator():
            for item in mock_data:
                yield item
        
        monitor = StreamingIntegrityMonitor(dataset_name="test")
        
        chunks = list(stream_dataset_chunks(mock_iterator(), monitor, batch_size=2))
        
        assert len(chunks) == 2  # First batch of 2, second batch of 1
        assert len(chunks[0]) == 2
        assert len(chunks[1]) == 1

    def test_stream_dataset_chunks_truncated(self):
        """Test that truncated stream raises error."""
        # Create mock iterator that fails mid-stream
        def failing_iterator():
            yield {"col1": 1}
            raise Exception("Stream failed")
        
        monitor = StreamingIntegrityMonitor(dataset_name="test")
        
        with pytest.raises(DataIntegrityError):
            list(stream_dataset_chunks(failing_iterator(), monitor))

class TestDownloadAndProcessStreaming:
    """Tests for download_and_process_streaming function."""

    @patch('src.data.ingest.load_dataset')
    def test_download_and_process_streaming_success(self, mock_load_dataset):
        """Test successful streaming download."""
        # Mock dataset iterator
        mock_data = [
            {"col1": 1, "col2": "a"},
            {"col1": 2, "col2": "b"}
        ]
        
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter(mock_data))
        mock_load_dataset.return_value = mock_dataset
        
        df = download_and_process_streaming("test_dataset", expected_rows=2)
        
        assert len(df) == 2
        assert "col1" in df.columns
        assert "col2" in df.columns

    @patch('src.data.ingest.load_dataset')
    def test_download_and_process_streaming_truncated(self, mock_load_dataset):
        """Test that truncated stream raises error."""
        # Mock dataset iterator that returns fewer rows than expected
        mock_data = [
            {"col1": 1, "col2": "a"}
        ]
        
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter(mock_data))
        mock_load_dataset.return_value = mock_dataset
        
        with pytest.raises(DataIntegrityError):
            download_and_process_streaming("test_dataset", expected_rows=10)

    @patch('src.data.ingest.load_dataset')
    def test_download_and_process_streaming_empty(self, mock_load_dataset):
        """Test that empty stream raises error."""
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([]))
        mock_load_dataset.return_value = mock_dataset
        
        with pytest.raises(DataIntegrityError):
            download_and_process_streaming("test_dataset")

def test_data_integrity_error_message():
    """Test that DataIntegrityError has descriptive messages."""
    error = DataIntegrityError("Stream terminated unexpectedly")
    assert "Stream terminated unexpectedly" in str(error)