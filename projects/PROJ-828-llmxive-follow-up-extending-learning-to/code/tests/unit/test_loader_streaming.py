"""
Unit tests for the GSM8K Streaming Loader.

These tests verify that the streaming loader correctly interfaces with
the HuggingFace datasets library and adheres to the "fail loudly" policy.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.loader import (
    GSM8KStreamingLoader,
    load_gsm8k_streaming,
    verify_data_integrity,
    DATASET_NAME,
    SPLIT_NAME,
    CHUNK_SIZE
)

class TestGSM8KStreamingLoader:
    """Test cases for the GSM8KStreamingLoader class."""

    def test_init_default(self):
        """Test default initialization parameters."""
        loader = GSM8KStreamingLoader()
        assert loader.split == SPLIT_NAME
        assert loader.config == "main"
        assert loader.chunk_size == CHUNK_SIZE
        assert loader.dataset is None

    def test_init_custom(self):
        """Test initialization with custom parameters."""
        loader = GSM8KStreamingLoader(split="test", config="math", chunk_size=50)
        assert loader.split == "test"
        assert loader.config == "math"
        assert loader.chunk_size == 50

    @patch('src.data.loader.load_dataset')
    def test_load_success(self, mock_load_dataset):
        """Test successful dataset loading."""
        mock_dataset = MagicMock()
        mock_load_dataset.return_value = mock_dataset

        loader = GSM8KStreamingLoader()
        result = loader.load()

        mock_load_dataset.assert_called_once_with(
            DATASET_NAME,
            "main",
            split=SPLIT_NAME,
            streaming=True,
            trust_remote_code=True
        )
        assert loader.dataset == mock_dataset
        assert result is not None

    @patch('src.data.loader.load_dataset')
    def test_load_failure_raises_error(self, mock_load_dataset):
        """Test that load raises an exception on failure."""
        mock_load_dataset.side_effect = Exception("Network error")

        loader = GSM8KStreamingLoader()

        with pytest.raises(ConnectionError) as exc_info:
            loader.load()

        assert "Failed to fetch real GSM8K data" in str(exc_info.value)

    def test_iter_chunks_logic(self):
        """Test that iter_chunks yields correct chunk sizes."""
        # Create a mock dataset iterator
        mock_data = [
            {"id": i, "question": f"Question {i}", "answer": f"Answer {i}"}
            for i in range(250)
        ]
        mock_dataset_iter = iter(mock_data)

        loader = GSM8KStreamingLoader(chunk_size=100)
        loader.dataset = mock_dataset_iter

        chunks = list(loader.iter_chunks())

        assert len(chunks) == 3  # 100, 100, 50
        assert len(chunks[0]) == 100
        assert len(chunks[1]) == 100
        assert len(chunks[2]) == 50

    def test_iter_chunks_empty(self):
        """Test iter_chunks with empty dataset."""
        loader = GSM8KStreamingLoader(chunk_size=100)
        loader.dataset = iter([])

        chunks = list(loader.iter_chunks())
        assert len(chunks) == 0

    def test_get_sample(self):
        """Test retrieving a sample of examples."""
        mock_data = [
            {"id": i} for i in range(10)
        ]
        loader = GSM8KStreamingLoader()
        loader.dataset = iter(mock_data)

        sample = loader.get_sample(3)
        assert len(sample) == 3
        assert sample[0]["id"] == 0
        assert sample[2]["id"] == 2

class TestLoadGsm8kStreaming:
    """Test cases for the load_gsm8k_streaming function."""

    @patch('src.data.loader.GSM8KStreamingLoader')
    def test_load_gsm8k_streaming_function(self, MockLoader):
        """Test the convenience function."""
        mock_loader_instance = MagicMock()
        mock_loader_instance.iter_chunks.return_value = iter([{"id": 1}])
        MockLoader.return_value = mock_loader_instance

        result = load_gsm8k_streaming(split="test", chunk_size=50)

        MockLoader.assert_called_once_with(split="test", chunk_size=50)
        mock_loader_instance.load.assert_called_once()
        assert result == mock_loader_instance.iter_chunks.return_value

class TestDataIntegrity:
    """Test cases for verify_data_integrity function."""

    def test_verify_success(self):
        """Test verification with sufficient data."""
        mock_data = [
            {"id": i} for i in range(1000)
        ]
        loader = GSM8KStreamingLoader(chunk_size=100)
        loader.dataset = iter(mock_data)

        result = verify_data_integrity(loader, min_examples=1000)
        assert result is True

    def test_verify_failure_raises_error(self):
        """Test verification with insufficient data raises error."""
        mock_data = [
            {"id": i} for i in range(500)
        ]
        loader = GSM8KStreamingLoader(chunk_size=100)
        loader.dataset = iter(mock_data)

        with pytest.raises(RuntimeError) as exc_info:
            verify_data_integrity(loader, min_examples=1000)

        assert "Dataset integrity check failed" in str(exc_info.value)
        assert "500 examples" in str(exc_info.value)
        assert "1000" in str(exc_info.value)
