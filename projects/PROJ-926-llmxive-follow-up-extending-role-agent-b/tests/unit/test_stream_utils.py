"""
Unit tests for streaming utilities.
These tests verify the logic of stream_utils without requiring real network access
by mocking the Hugging Face datasets library.
"""
import json
import tempfile
from unittest.mock import MagicMock, patch, mock_open
import pytest
from datasets import Dataset

from src.data.stream_utils import (
    load_trajectory_dataset,
    stream_trajectory_chunks,
    process_streaming_trajectories,
    count_streaming_examples,
    save_streamed_trajectories,
    filter_streaming_dataset,
    sample_streaming_dataset,
    get_dataset_info
)


class TestLoadTrajectoryDataset:
    @patch("src.data.stream_utils.load_dataset")
    def test_load_streaming_dataset(self, mock_load_dataset):
        """Test loading a dataset in streaming mode."""
        mock_dataset = MagicMock()
        mock_load_dataset.return_value = mock_dataset

        dataset = load_trajectory_dataset("test/dataset", streaming=True)

        mock_load_dataset.assert_called_once_with(
            "test/dataset",
            split="train",
            streaming=True
        )
        assert dataset == mock_dataset

    @patch("src.data.stream_utils.load_dataset")
    def test_load_non_streaming_dataset(self, mock_load_dataset):
        """Test loading a dataset in non-streaming mode."""
        mock_dataset = MagicMock()
        mock_load_dataset.return_value = mock_dataset

        dataset = load_trajectory_dataset("test/dataset", streaming=False)

        mock_load_dataset.assert_called_once_with(
            "test/dataset",
            split="train",
            streaming=False
        )
        assert dataset == mock_dataset

    @patch("src.data.stream_utils.load_dataset")
    def test_load_dataset_failure_raises_error(self, mock_load_dataset):
        """Test that load_dataset raises an error on failure."""
        mock_load_dataset.side_effect = Exception("Network error")

        with pytest.raises(RuntimeError, match="Failed to load real dataset"):
            load_trajectory_dataset("test/dataset")


class TestStreamTrajectoryChunks:
    def test_stream_trajectory_chunks(self):
        """Test chunking of a dataset."""
        mock_data = [{"id": i, "data": f"item_{i}"} for i in range(10)]
        mock_dataset = iter(mock_data)

        chunks = list(stream_trajectory_chunks(mock_dataset, chunk_size=3))

        assert len(chunks) == 4  # 3 chunks of 3, 1 chunk of 1
        assert len(chunks[0]) == 3
        assert len(chunks[-1]) == 1

    def test_stream_trajectory_chunks_empty(self):
        """Test chunking of an empty dataset."""
        mock_dataset = iter([])

        chunks = list(stream_trajectory_chunks(mock_dataset, chunk_size=3))

        assert chunks == []


class TestProcessStreamingTrajectories:
    def test_process_streaming_trajectories(self):
        """Test processing a streaming dataset."""
        mock_data = [{"id": i, "value": i * 2} for i in range(5)]
        mock_dataset = iter(mock_data)

        def processor(item):
            return {"id": item["id"], "processed": item["value"] * 2}

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            output_path = f.name

        count = process_streaming_trajectories(mock_dataset, processor, output_path)

        assert count == 5

        with open(output_path, 'r') as f:
            results = json.load(f)

        assert len(results) == 5
        assert results[0]["processed"] == 0
        assert results[1]["processed"] == 4

    def test_process_streaming_trajectories_with_errors(self):
        """Test processing with some items raising errors."""
        mock_data = [
            {"id": 0, "value": 1},
            {"id": 1, "value": "invalid"},  # This will cause an error
            {"id": 2, "value": 3}
        ]
        mock_dataset = iter(mock_data)

        def processor(item):
            if item["value"] == "invalid":
                raise ValueError("Invalid value")
            return {"id": item["id"], "processed": item["value"] * 2}

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            output_path = f.name

        count = process_streaming_trajectories(mock_dataset, processor, output_path)

        # Should process 2 out of 3 items
        assert count == 2


class TestFilterStreamingDataset:
    def test_filter_streaming_dataset(self):
        """Test filtering a streaming dataset."""
        mock_data = [{"id": i, "value": i} for i in range(10)]
        mock_dataset = iter(mock_data)

        filtered = list(filter_streaming_dataset(mock_dataset, lambda x: x["value"] % 2 == 0))

        assert len(filtered) == 5
        assert all(item["value"] % 2 == 0 for item in filtered)

    def test_filter_streaming_dataset_empty(self):
        """Test filtering an empty dataset."""
        mock_dataset = iter([])

        filtered = list(filter_streaming_dataset(mock_dataset, lambda x: True))

        assert filtered == []


class TestSampleStreamingDataset:
    def test_sample_streaming_dataset(self):
        """Test sampling from a streaming dataset."""
        mock_data = [{"id": i} for i in range(100)]
        mock_dataset = iter(mock_data)

        sample = list(sample_streaming_dataset(mock_dataset, n_samples=10, seed=42))

        assert len(sample) == 10
        # Check that IDs are unique
        ids = [item["id"] for item in sample]
        assert len(ids) == len(set(ids))

    def test_sample_streaming_dataset_small(self):
        """Test sampling when n_samples > dataset size."""
        mock_data = [{"id": i} for i in range(5)]
        mock_dataset = iter(mock_data)

        sample = list(sample_streaming_dataset(mock_dataset, n_samples=10, seed=42))

        assert len(sample) == 5


class TestSaveStreamedTrajectories:
    def test_save_streamed_trajectories(self):
        """Test saving a streaming dataset to JSON."""
        mock_data = [{"id": i, "data": f"item_{i}"} for i in range(10)]
        mock_dataset = iter(mock_data)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            output_path = f.name

        count = save_streamed_trajectories(mock_dataset, output_path, chunk_size=3)

        assert count == 10

        with open(output_path, 'r') as f:
            results = json.load(f)

        assert len(results) == 10

    def test_save_streamed_trajectories_empty(self):
        """Test saving an empty dataset."""
        mock_dataset = iter([])

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            output_path = f.name

        count = save_streamed_trajectories(mock_dataset, output_path)

        assert count == 0


class TestGetDatasetInfo:
    def test_get_dataset_info(self):
        """Test getting dataset info."""
        mock_dataset = MagicMock()
        mock_dataset.features = {"id": "int", "data": "str"}
        mock_dataset.split = "train"

        info = get_dataset_info(mock_dataset)

        assert info["split"] == "train"
        assert "features" in info

    def test_get_dataset_info_no_features(self):
        """Test getting dataset info without features."""
        mock_dataset = MagicMock()
        del mock_dataset.features
        mock_dataset.split = "validation"

        info = get_dataset_info(mock_dataset)

        assert info["split"] == "validation"
        assert info["features"] is None
