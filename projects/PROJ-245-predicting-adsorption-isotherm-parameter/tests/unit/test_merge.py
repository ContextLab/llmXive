"""
Unit tests for T061: Merge Chunks functionality.
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.merge import find_chunk_files, merge_parquet_files, ensure_directories, RAW_DATA_DIR, CHUNK_PATTERN


class TestFindChunkFiles:
    """Tests for find_chunk_files function."""

    def test_find_chunk_files_no_files_found(self, tmp_path):
        """Test that FileNotFoundError is raised when no chunk files exist."""
        with pytest.raises(FileNotFoundError) as exc_info:
            find_chunk_files(pattern="nonexistent_*.parquet", directory=tmp_path)
        
        assert "No chunk files found" in str(exc_info.value)

    def test_find_chunk_files_returns_sorted_list(self, tmp_path):
        """Test that chunk files are returned in sorted order."""
        # Create dummy chunk files
        (tmp_path / "streamed_chunk_001.parquet").touch()
        (tmp_path / "streamed_chunk_002.parquet").touch()
        (tmp_path / "streamed_chunk_010.parquet").touch()
        
        files = find_chunk_files(pattern="streamed_chunk_*.parquet", directory=tmp_path)
        
        assert len(files) == 3
        assert files[0].name == "streamed_chunk_001.parquet"
        assert files[1].name == "streamed_chunk_002.parquet"
        assert files[2].name == "streamed_chunk_010.parquet"


class TestMergeParquetFiles:
    """Tests for merge_parquet_files function."""

    def test_merge_single_file(self, tmp_path):
        """Test merging a single file."""
        # Create a test Parquet file
        df = pd.DataFrame({'a': [1, 2, 3], 'b': ['x', 'y', 'z']})
        input_file = tmp_path / "single.parquet"
        df.to_parquet(input_file)
        
        output_file = tmp_path / "merged.parquet"
        
        merge_parquet_files([input_file], output_file)
        
        assert output_file.exists()
        result_df = pd.read_parquet(output_file)
        assert len(result_df) == 3
        assert list(result_df.columns) == ['a', 'b']

    def test_merge_multiple_files(self, tmp_path):
        """Test merging multiple Parquet files."""
        # Create test Parquet files
        df1 = pd.DataFrame({'id': [1, 2], 'value': [10, 20]})
        df2 = pd.DataFrame({'id': [3, 4], 'value': [30, 40]})
        df3 = pd.DataFrame({'id': [5], 'value': [50]})
        
        input_files = []
        for i, df in enumerate([df1, df2, df3], 1):
            file_path = tmp_path / f"chunk_{i}.parquet"
            df.to_parquet(file_path)
            input_files.append(file_path)
        
        output_file = tmp_path / "merged.parquet"
        
        merge_parquet_files(input_files, output_file)
        
        assert output_file.exists()
        result_df = pd.read_parquet(output_file)
        assert len(result_df) == 5
        assert result_df['id'].tolist() == [1, 2, 3, 4, 5]
        assert result_df['value'].tolist() == [10, 20, 30, 40, 50]

    def test_merge_empty_list_raises_error(self, tmp_path):
        """Test that ValueError is raised when input list is empty."""
        output_file = tmp_path / "merged.parquet"
        
        with pytest.raises(ValueError) as exc_info:
            merge_parquet_files([], output_file)
        
        assert "No input files provided" in str(exc_info.value)

    def test_merge_preserves_schema(self, tmp_path):
        """Test that merging preserves column names and types."""
        df = pd.DataFrame({
            'string_col': ['a', 'b'],
            'int_col': [1, 2],
            'float_col': [1.1, 2.2]
        })
        
        input_file = tmp_path / "test.parquet"
        df.to_parquet(input_file)
        
        output_file = tmp_path / "merged.parquet"
        merge_parquet_files([input_file], output_file)
        
        result_df = pd.read_parquet(output_file)
        assert list(result_df.columns) == ['string_col', 'int_col', 'float_col']
        assert result_df['string_col'].dtype == object
        assert result_df['int_col'].dtype == 'int64'
        assert result_df['float_col'].dtype == 'float64'


class TestEnsureDirectories:
    """Tests for ensure_directories function."""

    def test_ensure_directories_creates_folder(self, tmp_path):
        """Test that ensure_directories creates the output directory."""
        test_dir = tmp_path / "new" / "nested" / "directory"
        
        # Mock the RAW_DATA_DIR for this test
        with patch('data.merge.RAW_DATA_DIR', test_dir):
            ensure_directories()
        
        assert test_dir.exists()
        assert test_dir.is_dir()