"""
Unit tests for trajectory streaming utilities.

These tests verify the functionality of the trajectory_utils module,
including streaming, batching, and error handling.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import numpy as np

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.trajectory_utils import (
    stream_trajectory_data,
    _batch_to_dict,
    _check_memory_pressure,
    get_trajectory_schema,
    run_trajectory_streaming_pipeline
)


class TestBatchToDict:
    """Tests for the _batch_to_dict helper function."""

    def test_empty_batch(self):
        """Test that an empty batch returns an empty dictionary."""
        result = _batch_to_dict([])
        assert result == {}

    def test_single_row(self):
        """Test conversion of a single row batch."""
        batch = [{"species": "bird1", "lat": 40.0, "lon": -70.0}]
        result = _batch_to_dict(batch)
        
        assert "species" in result
        assert "lat" in result
        assert "lon" in result
        assert isinstance(result["species"], np.ndarray)
        assert result["species"][0] == "bird1"
        assert result["lat"][0] == 40.0

    def test_multiple_rows(self):
        """Test conversion of multiple rows."""
        batch = [
            {"species": "bird1", "lat": 40.0, "lon": -70.0},
            {"species": "bird2", "lat": 41.0, "lon": -71.0}
        ]
        result = _batch_to_dict(batch)
        
        assert len(result["species"]) == 2
        assert len(result["lat"]) == 2
        assert result["species"][0] == "bird1"
        assert result["species"][1] == "bird2"


class TestStreamTrajectoryData:
    """Tests for the stream_trajectory_data function."""

    @patch('src.models.trajectory_utils.load_dataset')
    def test_streaming_success(self, mock_load_dataset):
        """Test successful streaming of dataset."""
        # Mock dataset
        mock_dataset = MagicMock()
        mock_split = MagicMock()
        mock_split.column_names = ["species", "lat", "lon"]
        mock_split.__iter__ = MagicMock(return_value=iter([
            {"species": "bird1", "lat": 40.0, "lon": -70.0},
            {"species": "bird2", "lat": 41.0, "lon": -71.0}
        ]))
        mock_dataset.__getitem__ = MagicMock(return_value=mock_split)
        mock_load_dataset.return_value = mock_dataset

        batches = list(stream_trajectory_data(
            dataset_name="test/dataset",
            streaming=True,
            batch_size=1
        ))

        assert len(batches) == 2
        assert "species" in batches[0]
        assert len(batches[0]["species"]) == 1

    @patch('src.models.trajectory_utils.load_dataset')
    def test_streaming_with_columns_filter(self, mock_load_dataset):
        """Test streaming with column filtering."""
        mock_dataset = MagicMock()
        mock_split = MagicMock()
        mock_split.column_names = ["species", "lat", "lon", "date"]
        mock_split.select_columns = MagicMock(return_value=mock_split)
        mock_split.__iter__ = MagicMock(return_value=iter([
            {"species": "bird1", "lat": 40.0, "lon": -70.0}
        ]))
        mock_dataset.__getitem__ = MagicMock(return_value=mock_split)
        mock_load_dataset.return_value = mock_dataset

        batches = list(stream_trajectory_data(
            dataset_name="test/dataset",
            streaming=True,
            columns=["species", "lat"]
        ))

        assert len(batches) == 1
        assert "species" in batches[0]
        assert "lat" in batches[0]
        assert "lon" not in batches[0]

    @patch('src.models.trajectory_utils.load_dataset')
    def test_streaming_dataset_not_found(self, mock_load_dataset):
        """Test error handling when dataset is not found."""
        mock_load_dataset.side_effect = Exception("Dataset not found")

        with pytest.raises(RuntimeError, match="Dataset streaming failed"):
            list(stream_trajectory_data(dataset_name="nonexistent/dataset"))


class TestGetTrajectorySchema:
    """Tests for the get_trajectory_schema function."""

    @patch('src.models.trajectory_utils.load_dataset')
    def test_get_schema_success(self, mock_load_dataset):
        """Test successful schema retrieval."""
        mock_dataset = MagicMock()
        mock_split = MagicMock()
        mock_split.column_names = ["species", "lat", "lon"]
        mock_split.features = {"species": "string", "lat": "float64", "lon": "float64"}
        mock_dataset.__getitem__ = MagicMock(return_value=mock_split)
        mock_load_dataset.return_value = mock_dataset

        schema = get_trajectory_schema("test/dataset")

        assert "species" in schema
        assert "lat" in schema
        assert schema["species"] == "string"

    @patch('src.models.trajectory_utils.load_dataset')
    def test_get_schema_error(self, mock_load_dataset):
        """Test error handling for schema retrieval."""
        mock_load_dataset.side_effect = Exception("Access denied")

        with pytest.raises(RuntimeError, match="Schema retrieval failed"):
            get_trajectory_schema("test/dataset")


class TestRunTrajectoryStreamingPipeline:
    """Tests for the run_trajectory_streaming_pipeline function."""

    @patch('src.models.trajectory_utils.stream_trajectory_data')
    def test_pipeline_success(self, mock_stream):
        """Test successful pipeline execution."""
        mock_stream.return_value = [
            {"species": np.array(["bird1"]), "lat": np.array([40.0])},
            {"species": np.array(["bird2"]), "lat": np.array([41.0])}
        ]

        stats = run_trajectory_streaming_pipeline(
            dataset_name="test/dataset",
            batch_size=1
        )

        assert stats["status"] == "success"
        assert stats["total_rows"] == 2
        assert stats["batches_processed"] == 2
        assert stats["dataset_name"] == "test/dataset"

    @patch('src.models.trajectory_utils.stream_trajectory_data')
    def test_pipeline_failure(self, mock_stream):
        """Test pipeline error handling."""
        mock_stream.side_effect = RuntimeError("Stream failed")

        with pytest.raises(RuntimeError, match="Pipeline failed"):
            run_trajectory_streaming_pipeline(dataset_name="test/dataset")


class TestMemoryPressure:
    """Tests for memory pressure checking."""

    def test_memory_check_no_error(self):
        """Test that memory check doesn't raise error under normal conditions."""
        # This should not raise an exception
        _check_memory_pressure()

    @patch('src.models.trajectory_utils.psutil')
    def test_memory_check_with_psutil(self, mock_psutil):
        """Test memory check with psutil available."""
        # Mock psutil to simulate high memory usage
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 8 * 1024 * 1024 * 1024  # 8GB
        
        mock_virtual = MagicMock()
        mock_virtual.total = 10 * 1024 * 1024 * 1024  # 10GB total
        
        mock_psutil.Process.return_value = mock_process
        mock_psutil.virtual_memory.return_value = mock_virtual

        # Should not raise with 80% usage (threshold is > 80%)
        _check_memory_pressure()

        # Test with > 80% usage
        mock_process.memory_info.return_value.rss = 9 * 1024 * 1024 * 1024  # 9GB
        with pytest.raises(MemoryError, match="Memory usage"):
            _check_memory_pressure()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])