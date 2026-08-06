"""
Unit tests for stream_utils module.
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os

from src.data.stream_utils import (
    stream_ebird_dataset,
    stream_and_process,
    count_total_rows
)


class TestStreamEbirdDataset:
    """Tests for stream_ebird_dataset function."""

    @patch('src.data.stream_utils.load_dataset')
    def test_stream_success(self, mock_load_dataset):
        """Test successful streaming of dataset."""
        # Mock dataset iterator
        mock_rows = [
            {"species": "sparrow", "lat": 40.0, "lon": -75.0, "date": "2023-03-01", "count": 5},
            {"species": "robin", "lat": 41.0, "lon": -74.0, "date": "2023-03-02", "count": 3},
            {"species": "sparrow", "lat": 40.5, "lon": -74.5, "date": "2023-03-03", "count": 7}
        ]

        mock_dataset = iter(mock_rows)
        mock_load_dataset.return_value = mock_dataset

        batches = list(stream_ebird_dataset("test/dataset", batch_size=2, split="train"))

        assert len(batches) == 2
        assert len(batches[0]) == 2
        assert len(batches[1]) == 1
        assert batches[0].columns.tolist() == ["species", "lat", "lon", "date", "count"]

    @patch('src.data.stream_utils.load_dataset')
    def test_stream_empty_dataset(self, mock_load_dataset):
        """Test streaming an empty dataset."""
        mock_load_dataset.return_value = iter([])

        batches = list(stream_ebird_dataset("test/dataset", batch_size=10, split="train"))

        assert len(batches) == 0

    @patch('src.data.stream_utils.load_dataset')
    def test_stream_load_failure(self, mock_load_dataset):
        """Test handling of dataset load failure."""
        mock_load_dataset.side_effect = Exception("Dataset not found")

        with pytest.raises(RuntimeError, match="Failed to load dataset"):
            list(stream_ebird_dataset("test/dataset", batch_size=10, split="train"))


class TestStreamAndProcess:
    """Tests for stream_and_process function."""

    @patch('src.data.stream_utils.stream_ebird_dataset')
    def test_stream_and_process_with_processor(self, mock_stream):
        """Test streaming with a processor function."""
        # Mock streaming to return sample data
        mock_df = pd.DataFrame({
            "species": ["sparrow", "robin"],
            "lat": [40.0, 41.0],
            "lon": [-75.0, -74.0],
            "date": ["2023-03-01", "2023-03-02"],
            "count": [5, 3]
        })
        mock_stream.return_value = iter([mock_df])

        def processor(df):
            return df[df["count"] > 0]

        stats = stream_and_process(
            "test/dataset",
            processor_func=processor,
            batch_size=10,
            output_dir=None,
            split="train"
        )

        assert stats["total_batches"] == 1
        assert stats["total_rows_processed"] == 2
        assert len(stats["errors"]) == 0

    @patch('src.data.stream_utils.stream_ebird_dataset')
    def test_stream_and_process_save_to_disk(self, mock_stream):
        """Test streaming with output to disk."""
        mock_df = pd.DataFrame({
            "species": ["sparrow"],
            "lat": [40.0],
            "lon": [-75.0],
            "date": ["2023-03-01"],
            "count": [5]
        })
        mock_stream.return_value = iter([mock_df])

        with tempfile.TemporaryDirectory() as tmpdir:
            stats = stream_and_process(
                "test/dataset",
                batch_size=10,
                output_dir=tmpdir,
                split="train"
            )

            assert stats["total_batches"] == 1
            output_file = Path(tmpdir) / "chunk_00000.parquet"
            assert output_file.exists()

    @patch('src.data.stream_utils.stream_ebird_dataset')
    def test_stream_and_process_processor_error(self, mock_stream):
        """Test handling of processor errors."""
        mock_df = pd.DataFrame({
            "species": ["sparrow"],
            "lat": [40.0],
            "lon": [-75.0],
            "date": ["2023-03-01"],
            "count": [5]
        })
        mock_stream.return_value = iter([mock_df])

        def bad_processor(df):
            raise ValueError("Processor error")

        stats = stream_and_process(
            "test/dataset",
            processor_func=bad_processor,
            batch_size=10,
            output_dir=None,
            split="train"
        )

        assert stats["total_batches"] == 1
        assert len(stats["errors"]) == 1
        assert "Error processing batch" in stats["errors"][0]


class TestCountTotalRows:
    """Tests for count_total_rows function."""

    @patch('src.data.stream_utils.stream_ebird_dataset')
    def test_count_rows(self, mock_stream):
        """Test counting total rows."""
        mock_dfs = [
            pd.DataFrame({"species": ["a", "b"]}),
            pd.DataFrame({"species": ["c", "d", "e"]})
        ]
        mock_stream.return_value = iter(mock_dfs)

        total = count_total_rows("test/dataset", split="train")

        assert total == 5

    @patch('src.data.stream_utils.stream_ebird_dataset')
    def test_count_empty_dataset(self, mock_stream):
        """Test counting rows in empty dataset."""
        mock_stream.return_value = iter([])

        total = count_total_rows("test/dataset", split="train")

        assert total == 0