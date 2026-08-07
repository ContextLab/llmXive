"""
Unit tests for the RULER dataset downloader (code/data/download.py).
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from data.download import download_ruler_streaming, get_ruler_dataset_info


class TestDownloadRulerStreaming:
    """Tests for the streaming download function."""

    def test_streaming_success(self):
        """Test that streaming returns items when source is available."""
        mock_item = {
            "id": "test-123",
            "text": "This is a test document for RULER.",
            "label": 0
        }
        
        # Mock the load_dataset function to return a mock iterable
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([mock_item, mock_item]))
        
        with patch("data.download.load_dataset", return_value=mock_dataset):
            stream = download_ruler_streaming(
                dataset_name="hkust-nlp/ruler",
                subset="sustest",
                split="train"
            )
            
            items = list(stream)
            assert len(items) == 2
            assert items[0]["id"] == "test-123"

    def test_streaming_empty_dataset_raises(self):
        """Test that an empty dataset raises RuntimeError."""
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([]))
        
        with patch("data.download.load_dataset", return_value=mock_dataset):
            with pytest.raises(RuntimeError, match="is empty"):
                list(download_ruler_streaming())

    def test_streaming_connection_failure_raises_connection_error(self):
        """Test that network failure raises ConnectionError (fail loudly)."""
        with patch("data.download.load_dataset", side_effect=Exception("Network unreachable")):
            with pytest.raises(ConnectionError, match="CRITICAL FAILURE"):
                list(download_ruler_streaming())

    def test_streaming_no_synthetic_fallback(self):
        """Verify that no synthetic data is generated on failure."""
        # This is implicitly tested by test_streaming_connection_failure_raises_connection_error
        # because if it fell back to synthetic, it wouldn't raise an error.
        with patch("data.download.load_dataset", side_effect=Exception("Network error")):
            try:
                list(download_ruler_streaming())
                assert False, "Should have raised ConnectionError"
            except ConnectionError:
                pass  # Expected

class TestGetRulerDatasetInfo:
    """Tests for the dataset info retrieval function."""

    def test_info_retrieval_success(self):
        """Test successful retrieval of dataset info."""
        mock_features = {"text": "string", "label": "int"}
        mock_ds = MagicMock()
        mock_ds.features = mock_features
        
        with patch("data.download.load_dataset", return_value=mock_ds):
            with patch("data.download.DatasetDict") as mock_dict_class:
                # Simulate DatasetDict behavior if needed, or just mock the return
                # The function handles both Dataset and DatasetDict
                # Let's mock the streaming load specifically
                pass

        # Simplified test: just ensure it calls load_dataset
        mock_ds_stream = MagicMock()
        mock_ds_stream.features = {"text": "string"}
        
        with patch("data.download.load_dataset", return_value=mock_ds_stream):
            info = get_ruler_dataset_info()
            assert "features" in info
            assert info["features"] == {"text": "string"}

    def test_info_connection_failure_raises(self):
        """Test that info retrieval failure raises ConnectionError."""
        with patch("data.download.load_dataset", side_effect=Exception("Network error")):
            with pytest.raises(ConnectionError, match="Failed to retrieve metadata"):
                get_ruler_dataset_info()