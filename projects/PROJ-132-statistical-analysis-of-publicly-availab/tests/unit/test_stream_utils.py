"""
Unit tests for the streaming utilities module.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.data.stream_utils import (
    stream_ebird_data,
    process_streamed_chunks,
    get_dataset_info,
    run_streaming_pipeline
)


class TestStreamEbirdData:
    """Tests for stream_ebird_data function."""

    @patch('src.data.stream_utils.load_dataset')
    def test_stream_success(self, mock_load_dataset):
        """Test successful streaming of dataset chunks."""
        # Mock dataset iterator
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {"species": "A", "lat": 1.0, "lon": 1.0},
            {"species": "B", "lat": 2.0, "lon": 2.0},
            {"species": "C", "lat": 3.0, "lon": 3.0},
            {"species": "D", "lat": 4.0, "lon": 4.0},
        ]))
        mock_load_dataset.return_value = mock_dataset

        chunks = list(stream_ebird_data(chunk_size=2))

        assert len(chunks) == 2
        assert chunks[0]["count"] == 2
        assert chunks[1]["count"] == 2
        assert chunks[0]["total_rows"] == 2
        assert chunks[1]["total_rows"] == 4

    @patch('src.data.stream_utils.load_dataset')
    def test_stream_empty_dataset(self, mock_load_dataset):
        """Test streaming with empty dataset."""
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([]))
        mock_load_dataset.return_value = mock_dataset

        chunks = list(stream_ebird_data(chunk_size=2))

        assert len(chunks) == 0

    @patch('src.data.stream_utils.load_dataset')
    def test_stream_invalid_chunk_size(self, mock_load_dataset):
        """Test that invalid chunk size raises ValueError."""
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            list(stream_ebird_data(chunk_size=0))

    @patch('src.data.stream_utils.load_dataset')
    def test_stream_load_failure(self, mock_load_dataset):
        """Test that dataset load failure raises RuntimeError."""
        mock_load_dataset.side_effect = Exception("Dataset not found")

        with pytest.raises(RuntimeError, match="Failed to load dataset"):
            list(stream_ebird_data())


class TestProcessStreamedChunks:
    """Tests for process_streamed_chunks function."""

    @patch('src.data.stream_utils.stream_ebird_data')
    def test_process_with_callback(self, mock_stream):
        """Test processing with a custom callback function."""
        mock_stream.return_value = [
            {"rows": [{"species": "A"}], "count": 1, "total_rows": 1},
            {"rows": [{"species": "B"}], "count": 1, "total_rows": 2},
        ]

        processed_count = 0

        def callback(chunk_data):
            nonlocal processed_count
            processed_count += 1

        stats = process_streamed_chunks(processing_fn=callback)

        assert stats["total_chunks"] == 2
        assert stats["total_rows"] == 2
        assert processed_count == 2

    @patch('src.data.stream_utils.stream_ebird_data')
    def test_process_without_callback(self, mock_stream):
        """Test processing without callback."""
        mock_stream.return_value = [
            {"rows": [{"species": "A"}], "count": 1, "total_rows": 1},
        ]

        stats = process_streamed_chunks()

        assert stats["total_chunks"] == 1
        assert stats["total_rows"] == 1
        assert "rows_per_chunk" in stats


class TestGetDatasetInfo:
    """Tests for get_dataset_info function."""

    @patch('src.data.stream_utils.load_dataset')
    def test_get_info_success(self, mock_load_dataset):
        """Test successful retrieval of dataset info."""
        mock_dataset = MagicMock()
        mock_dataset.features = {"species": "string", "lat": "float"}
        mock_dataset.__iter__ = MagicMock(return_value=iter(["train", "test"]))
        mock_load_dataset.return_value = mock_dataset

        info = get_dataset_info()

        assert "features" in info
        assert "dataset_name" in info
        assert info["dataset_name"] == "vvud/eb-data"

    @patch('src.data.stream_utils.load_dataset')
    def test_get_info_failure(self, mock_load_dataset):
        """Test that info retrieval failure raises RuntimeError."""
        mock_load_dataset.side_effect = Exception("Not found")

        with pytest.raises(RuntimeError, match="Failed to get dataset info"):
            get_dataset_info()


class TestRunStreamingPipeline:
    """Tests for run_streaming_pipeline function."""

    @patch('src.data.stream_utils.process_streamed_chunks')
    @patch('src.data.stream_utils.get_dataset_info')
    def test_pipeline_with_output(self, mock_info, mock_process):
        """Test pipeline with output file generation."""
        mock_process.return_value = {"total_chunks": 1, "total_rows": 10}
        mock_info.return_value = {"features": ["species"]}

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.json"

            result = run_streaming_pipeline(output_path=output_path)

            assert result == output_path
            assert output_path.exists()

            with open(output_path) as f:
                data = json.load(f)

            assert "total_chunks" in data
            assert "dataset_info" in data

    @patch('src.data.stream_utils.process_streamed_chunks')
    @patch('src.data.stream_utils.get_dataset_info')
    def test_pipeline_without_output(self, mock_info, mock_process):
        """Test pipeline without output file."""
        mock_process.return_value = {"total_chunks": 1}
        mock_info.return_value = {}

        result = run_streaming_pipeline(output_path=None)

        assert result is None