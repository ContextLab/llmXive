"""
Unit tests for code/loaders.py functionality.
Tests chunked parquet loading and memory mapping strategies.
"""
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Import the module under test
from loaders import load_chunked_parquet, load_parquet_as_df

class TestLoaders:
    """Tests for loader functions."""

    def test_load_parquet_as_df(self, temp_dir, sample_moral_machine_data):
        """Test loading a small parquet file into a DataFrame."""
        # Write test data
        test_file = temp_dir / "test_data.parquet"
        sample_moral_machine_data.to_parquet(test_file)

        # Load and verify
        df = load_parquet_as_df(test_file)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(sample_moral_machine_data)
        assert list(df.columns) == list(sample_moral_machine_data.columns)

    def test_load_chunked_parquet(self, temp_dir, sample_moral_machine_data):
        """Test loading parquet in chunks."""
        # Write test data
        test_file = temp_dir / "test_chunked.parquet"
        sample_moral_machine_data.to_parquet(test_file)

        # Load in chunks
        chunks = list(load_chunked_parquet(test_file, chunk_size=10))

        assert len(chunks) > 0
        total_rows = sum(len(chunk) for chunk in chunks)
        assert total_rows == len(sample_moral_machine_data)

        # Verify data integrity across chunks
        combined = pd.concat(chunks, ignore_index=True)
        pd.testing.assert_frame_equal(
            combined.sort_values("id").reset_index(drop=True),
            sample_moral_machine_data.sort_values("id").reset_index(drop=True)
        )

    def test_load_chunked_parquet_empty(self, temp_dir):
        """Test loading an empty parquet file."""
        test_file = temp_dir / "empty.parquet"
        pd.DataFrame({"col": []}).to_parquet(test_file)

        chunks = list(load_chunked_parquet(test_file, chunk_size=10))
        assert len(chunks) == 0

    def test_load_nonexistent_file(self, temp_dir):
        """Test that loading a non-existent file raises an error."""
        test_file = temp_dir / "missing.parquet"

        with pytest.raises(FileNotFoundError):
            load_parquet_as_df(test_file)

        with pytest.raises(FileNotFoundError):
            list(load_chunked_parquet(test_file, chunk_size=10))

    def test_chunk_size_larger_than_data(self, temp_dir, sample_moral_machine_data):
        """Test loading with a chunk size larger than the dataset."""
        test_file = temp_dir / "large_chunk.parquet"
        sample_moral_machine_data.to_parquet(test_file)

        # Chunk size larger than total rows
        chunks = list(load_chunked_parquet(test_file, chunk_size=1000))

        assert len(chunks) == 1
        assert len(chunks[0]) == len(sample_moral_machine_data)
