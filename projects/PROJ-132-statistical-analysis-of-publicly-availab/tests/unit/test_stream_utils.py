"""
Unit tests for stream_utils.py
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import json

from src.data.stream_utils import (
    stream_ebird_data,
    get_dataset_info,
    run_streaming_pipeline
)


class TestStreamUtils:
    """Tests for streaming utilities."""

    def test_get_dataset_info_exists(self):
        """Test that we can get info for the verified dataset."""
        info = get_dataset_info("vvud/eb-data")
        assert info is not None
        assert "dataset_name" in info
        assert info["dataset_name"] == "vvud/eb-data"

    def test_stream_ebird_data_returns_generator(self):
        """Test that stream_ebird_data returns a generator."""
        gen = stream_ebird_data("vvud/eb-data", chunk_size=1000)
        # Just check it's an iterator, don't exhaust it in unit test
        assert hasattr(gen, '__iter__')

    def test_stream_ebird_data_columns_filter(self):
        """Test that column filtering works."""
        columns = ["species", "lat", "lon"]
        gen = stream_ebird_data(
            "vvud/eb-data",
            columns=columns,
            chunk_size=100
        )

        # Get first chunk
        first_chunk = next(gen)
        assert isinstance(first_chunk, pd.DataFrame)
        assert all(col in first_chunk.columns for col in columns)
        assert len(first_chunk.columns) == len(columns)

    def test_run_streaming_pipeline_creates_files(self):
        """Test that the streaming pipeline creates output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = run_streaming_pipeline(
                output_dir=tmpdir,
                dataset_name="vvud/eb-data",
                columns=["species", "lat", "lon", "date", "count", "checklist_id"]
            )

            # Check summary file exists
            summary_file = Path(output_dir) / "streaming_summary.json"
            assert summary_file.exists()

            # Check summary content
            with open(summary_file, 'r') as f:
                summary = json.load(f)

            assert summary["dataset_name"] == "vvud/eb-data"
            assert summary["total_chunks"] > 0
            assert summary["total_rows"] > 0

            # Check that at least one chunk file exists
            chunk_files = list(Path(output_dir).glob("stream_chunk_*.parquet"))
            assert len(chunk_files) > 0

    def test_stream_ebird_data_empty_columns(self):
        """Test streaming with no columns specified (should load all)."""
        gen = stream_ebird_data("vvud/eb-data", columns=None, chunk_size=100)
        first_chunk = next(gen)
        assert isinstance(first_chunk, pd.DataFrame)
        assert len(first_chunk.columns) > 0

    def test_stream_ebird_data_large_chunk_size(self):
        """Test streaming with a larger chunk size."""
        gen = stream_ebird_data("vvud/eb-data", chunk_size=50000)
        first_chunk = next(gen)
        assert isinstance(first_chunk, pd.DataFrame)
        assert len(first_chunk) <= 50000