"""
Unit tests for streaming utilities.
"""

import json
import tempfile
from unittest.mock import MagicMock, patch
import pytest

from src.data.stream_utils import (
    load_trajectory_dataset,
    stream_trajectory_chunks,
    process_streaming_trajectories,
    count_streaming_examples,
    save_streamed_trajectories,
    filter_streaming_dataset,
    sample_streaming_dataset,
    get_dataset_info,
)


class TestLoadTrajectoryDataset:
    """Tests for load_trajectory_dataset function."""

    def test_load_with_streaming(self):
        """Test loading dataset with streaming enabled."""
        mock_dataset = MagicMock()
        with patch("src.data.stream_utils.load_dataset", return_value=mock_dataset):
            result = load_trajectory_dataset("test_dataset", streaming=True)
            assert result == mock_dataset
            # Verify streaming=True was passed
            call_args = mock_dataset.__class__.load_dataset.call_args
            assert call_args[1]["streaming"] is True

    def test_load_without_streaming(self):
        """Test loading dataset with streaming disabled."""
        mock_dataset = MagicMock()
        with patch("src.data.stream_utils.load_dataset", return_value=mock_dataset):
            result = load_trajectory_dataset("test_dataset", streaming=False)
            assert result == mock_dataset

    def test_load_fails_loudly(self):
        """Test that load_dataset fails loudly on error (no synthetic fallback)."""
        with patch("src.data.stream_utils.load_dataset", side_effect=Exception("Connection error")):
            with pytest.raises(RuntimeError, match="Failed to load real dataset"):
                load_trajectory_dataset("nonexistent_dataset")


class TestStreamTrajectoryChunks:
    """Tests for stream_trajectory_chunks function."""

    def test_streaming_chunks(self):
        """Test that data is streamed in correct chunk sizes."""
        # Create mock dataset
        mock_data = [{"id": i, "data": f"example_{i}"} for i in range(250)]
        
        chunks = list(stream_trajectory_chunks(mock_data, chunk_size=100))
        
        assert len(chunks) == 3  # 2 full chunks + 1 partial
        assert len(chunks[0]) == 100
        assert len(chunks[1]) == 100
        assert len(chunks[2]) == 50

    def test_streaming_single_chunk(self):
        """Test streaming when data fits in one chunk."""
        mock_data = [{"id": i} for i in range(50)]
        
        chunks = list(stream_trajectory_chunks(mock_data, chunk_size=100))
        
        assert len(chunks) == 1
        assert len(chunks[0]) == 50

    def test_empty_dataset(self):
        """Test streaming from empty dataset."""
        mock_data = []
        
        chunks = list(stream_trajectory_chunks(mock_data, chunk_size=100))
        
        assert len(chunks) == 0


class TestProcessStreamingTrajectories:
    """Tests for process_streaming_trajectories function."""

    def test_processing_function(self):
        """Test that processor function is applied correctly."""
        mock_data = [{"value": i} for i in range(10)]
        
        def double_value(example):
            return {"value": example["value"] * 2}
        
        results = list(process_streaming_trajectories(mock_data, double_value))
        
        assert len(results) == 10
        assert results[0]["value"] == 0
        assert results[1]["value"] == 2
        assert results[5]["value"] == 10

    def test_filtering_none_results(self):
        """Test that None results are filtered out."""
        mock_data = [{"value": i} for i in range(10)]
        
        def selective_processor(example):
            if example["value"] % 2 == 0:
                return example
            return None
        
        results = list(process_streaming_trajectories(mock_data, selective_processor))
        
        assert len(results) == 5  # Only even values


class TestFilterStreamingDataset:
    """Tests for filter_streaming_dataset function."""

    def test_filter_function(self):
        """Test filtering with a custom function."""
        mock_data = [{"value": i} for i in range(20)]
        
        def is_even(example):
            return example["value"] % 2 == 0
        
        results = list(filter_streaming_dataset(mock_data, is_even))
        
        assert len(results) == 10
        assert all(r["value"] % 2 == 0 for r in results)

    def test_filter_all(self):
        """Test filter that keeps all items."""
        mock_data = [{"value": i} for i in range(10)]
        
        def keep_all(example):
            return True
        
        results = list(filter_streaming_dataset(mock_data, keep_all))
        
        assert len(results) == 10


class TestSampleStreamingDataset:
    """Tests for sample_streaming_dataset function."""

    def test_sample_size(self):
        """Test that correct sample size is returned."""
        mock_data = [{"value": i} for i in range(100)]
        
        results = list(sample_streaming_dataset(mock_data, sample_size=20))
        
        assert len(results) == 20

    def test_sample_less_than_total(self):
        """Test sampling when sample_size < total."""
        mock_data = [{"value": i} for i in range(50)]
        
        results = list(sample_streaming_dataset(mock_data, sample_size=10))
        
        assert len(results) == 10


class TestSaveStreamedTrajectories:
    """Tests for save_streamed_trajectories function."""

    def test_save_jsonl_format(self):
        """Test saving in JSONL format."""
        mock_data = [{"id": i, "data": f"example_{i}"} for i in range(10)]
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            output_path = f.name
        
        try:
            result_path = save_streamed_trajectories(mock_data, output_path, format="jsonl")
            
            assert result_path == output_path
            
            with open(output_path, "r") as f:
                lines = f.readlines()
            
            assert len(lines) == 10
            
            # Verify each line is valid JSON
            for line in lines:
                json.loads(line)
        finally:
            import os
            os.unlink(output_path)

    def test_save_json_format(self):
        """Test saving in JSON format."""
        mock_data = [{"id": i, "data": f"example_{i}"} for i in range(10)]
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name
        
        try:
            result_path = save_streamed_trajectories(mock_data, output_path, format="json")
            
            assert result_path == output_path
            
            with open(output_path, "r") as f:
                data = json.load(f)
            
            assert len(data) == 10
        finally:
            import os
            os.unlink(output_path)

    def test_invalid_format(self):
        """Test that invalid format raises error."""
        mock_data = [{"id": 1}]
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            output_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported format"):
                save_streamed_trajectories(mock_data, output_path, format="invalid")
        finally:
            import os
            os.unlink(output_path)

class TestGetDatasetInfo:
    """Tests for get_dataset_info function."""

    def test_get_info(self):
        """Test getting dataset information."""
        mock_dataset = MagicMock()
        mock_dataset.features = {"id": "int", "data": "string"}
        
        info = get_dataset_info(mock_dataset)
        
        assert "type" in info
        assert "features" in info

    def test_info_without_features(self):
        """Test info for dataset without features attribute."""
        mock_dataset = MagicMock(spec=[])
        
        info = get_dataset_info(mock_dataset)
        
        assert "type" in info