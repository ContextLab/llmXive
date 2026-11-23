"""
Unit tests for the Streaming Data Loader (T047).

These tests verify that:
1. The loader raises an error if streaming is disabled.
2. The loader raises a RuntimeError if the real source fails (no synthetic fallback).
3. The chunking function works correctly.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add code to path if running from tests/
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from data.loader import (
    load_streaming_dataset,
    process_stream_in_chunks,
    get_dataset_statistics
)


class TestStreamingLoader:
    """Tests for the streaming data loader functionality."""

    def test_streaming_must_be_true(self):
        """Verify that disabling streaming raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            load_streaming_dataset(streaming=False)
        
        assert "Streaming mode is REQUIRED" in str(excinfo.value)

    @patch("data.loader.load_dataset")
    def test_load_dataset_called_with_streaming_true(self, mock_load_dataset):
        """Verify that load_dataset is called with streaming=True."""
        mock_dataset = MagicMock()
        mock_load_dataset.return_value = mock_dataset
        
        # Call the function
        result = load_streaming_dataset(
            dataset_name="test/dataset",
            split="train",
            streaming=True
        )
        
        # Verify the call
        mock_load_dataset.assert_called_once_with(
            "test/dataset",
            split="train",
            streaming=True,
            trust_remote_code=False
        )

    @patch("data.loader.load_dataset")
    def test_process_stream_in_chunks(self, mock_load_dataset):
        """Verify chunking logic."""
        # Mock a dataset that yields rows
        mock_dataset = [
            {"id": 1, "value": "a"},
            {"id": 2, "value": "b"},
            {"id": 3, "value": "c"},
            {"id": 4, "value": "d"},
            {"id": 5, "value": "e"},
        ]
        mock_load_dataset.return_value = mock_dataset
        
        stream = load_streaming_dataset(streaming=True)
        chunks = list(process_stream_in_chunks(stream, chunk_size=2))
        
        assert len(chunks) == 3  # 2 + 2 + 1
        assert len(chunks[0]) == 2
        assert len(chunks[1]) == 2
        assert len(chunks[2]) == 1
        assert chunks[0][0]["id"] == 1

    @patch("data.loader.load_dataset")
    def test_get_dataset_statistics(self, mock_load_dataset):
        """Verify statistics collection."""
        mock_dataset = [
            {"id": 1, "val": 10},
            {"id": 2, "val": 20},
            {"id": 3, "val": 30},
        ]
        mock_load_dataset.return_value = mock_dataset
        
        stream = load_streaming_dataset(streaming=True)
        stats = get_dataset_statistics(stream, sample_limit=2)
        
        assert stats["total_rows_processed"] == 2
        assert stats["columns"] is not None
        assert "id" in stats["columns"]

    def test_fail_loudly_on_real_source_failure(self):
        """
        Verify that if load_dataset fails, the loader raises RuntimeError
        and does NOT fall back to synthetic data.
        """
        with patch("data.loader.load_dataset") as mock_load_dataset:
            mock_load_dataset.side_effect = Exception("Network Error")
            
            with pytest.raises(RuntimeError) as excinfo:
                load_streaming_dataset(streaming=True)
            
            assert "NO synthetic fallback is allowed" in str(excinfo.value)
            assert "must fail here" in str(excinfo.value).lower()