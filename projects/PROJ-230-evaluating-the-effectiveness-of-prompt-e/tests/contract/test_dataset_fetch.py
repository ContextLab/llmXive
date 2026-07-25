"""
Contract tests for dataset fetch functionality in src/ingestion/download_datasets.py.

These tests verify the interface and behavior of the dataset fetching module
without requiring actual network access or large dataset downloads.
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
from pathlib import Path

# Ensure the src directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.ingestion.download_datasets import (
    ensure_dirs,
    fetch_dataset,
    extract_code_columns,
    main
)
from datasets import Dataset


class TestDatasetFetchContract:
    """Contract tests for the dataset fetch module."""

    def test_ensure_dirs_creates_directory_structure(self, tmp_path):
        """Test that ensure_dirs creates the required directory structure."""
        # Arrange
        data_raw_dir = tmp_path / "data" / "raw"
        
        # Act
        result = ensure_dirs(data_raw_dir)
        
        # Assert
        assert result is True
        assert data_raw_dir.exists()
        assert data_raw_dir.is_dir()

    def test_ensure_dirs_existing_directory(self, tmp_path):
        """Test that ensure_dirs returns True when directory already exists."""
        # Arrange
        data_raw_dir = tmp_path / "data" / "raw"
        data_raw_dir.mkdir(parents=True)
        
        # Act
        result = ensure_dirs(data_raw_dir)
        
        # Assert
        assert result is True

    @patch('src.ingestion.download_datasets.load_dataset')
    def test_fetch_dataset_returns_dataset_object(self, mock_load_dataset, tmp_path):
        """Test that fetch_dataset returns a proper Dataset object."""
        # Arrange
        mock_dataset = MagicMock(spec=Dataset)
        mock_dataset.__len__ = MagicMock(return_value=100)
        mock_dataset.column_names = ['python_code', 'javascript_code', 'other_field']
        mock_load_dataset.return_value = mock_dataset
        
        data_raw_dir = tmp_path / "data" / "raw"
        data_raw_dir.mkdir(parents=True)
        
        # Act
        result = fetch_dataset(
            dataset_name="codeparrot/code-trans-py-js",
            cache_dir=str(data_raw_dir),
            streaming=False
        )
        
        # Assert
        assert result is not None
        assert isinstance(result, MagicMock)
        mock_load_dataset.assert_called_once_with(
            "codeparrot/code-trans-py-js",
            cache_dir=str(data_raw_dir),
            streaming=False
        )

    @patch('src.ingestion.download_datasets.load_dataset')
    def test_fetch_dataset_with_streaming(self, mock_load_dataset, tmp_path):
        """Test that fetch_dataset correctly passes streaming parameter."""
        # Arrange
        mock_dataset = MagicMock(spec=Dataset)
        mock_load_dataset.return_value = mock_dataset
        
        data_raw_dir = tmp_path / "data" / "raw"
        data_raw_dir.mkdir(parents=True)
        
        # Act
        result = fetch_dataset(
            dataset_name="codeparrot/code-trans-py-js",
            cache_dir=str(data_raw_dir),
            streaming=True
        )
        
        # Assert
        mock_load_dataset.assert_called_once_with(
            "codeparrot/code-trans-py-js",
            cache_dir=str(data_raw_dir),
            streaming=True
        )

    def test_extract_code_columns_with_valid_dataset(self):
        """Test that extract_code_columns correctly extracts python and javascript code."""
        # Arrange
        mock_dataset = MagicMock(spec=Dataset)
        mock_dataset.__len__ = MagicMock(return_value=3)
        mock_dataset.column_names = ['python_code', 'javascript_code', 'other_field']
        mock_dataset.__getitem__ = MagicMock(side_effect=[
            {'python_code': 'print("hello")', 'javascript_code': 'console.log("hello");', 'other_field': 'data1'},
            {'python_code': 'x = 1', 'javascript_code': 'var x = 1;', 'other_field': 'data2'},
            {'python_code': 'def foo(): pass', 'javascript_code': 'function foo() {}', 'other_field': 'data3'}
        ])
        
        expected_pairs = [
            ('print("hello")', 'console.log("hello");'),
            ('x = 1', 'var x = 1;'),
            ('def foo(): pass', 'function foo() {}')
        ]
        
        # Act
        result = extract_code_columns(mock_dataset)
        
        # Assert
        assert len(result) == len(expected_pairs)
        for i, (python_code, js_code) in enumerate(result):
            assert python_code == expected_pairs[i][0]
            assert js_code == expected_pairs[i][1]

    def test_extract_code_columns_with_missing_columns(self):
        """Test that extract_code_columns handles datasets without required columns."""
        # Arrange
        mock_dataset = MagicMock(spec=Dataset)
        mock_dataset.__len__ = MagicMock(return_value=1)
        mock_dataset.column_names = ['other_field']
        mock_dataset.__getitem__ = MagicMock(return_value={'other_field': 'data'})
        
        # Act & Assert
        with pytest.raises(KeyError):
            extract_code_columns(mock_dataset)

    @patch('src.ingestion.download_datasets.fetch_dataset')
    @patch('src.ingestion.download_datasets.extract_code_columns')
    @patch('src.ingestion.download_datasets.ensure_dirs')
    def test_main_executes_full_pipeline(self, mock_ensure_dirs, mock_extract, mock_fetch, tmp_path, caplog):
        """Test that main() executes the full pipeline correctly."""
        # Arrange
        mock_ensure_dirs.return_value = True
        
        mock_dataset = MagicMock(spec=Dataset)
        mock_fetch.return_value = mock_dataset
        
        mock_pairs = [
            ('print("hello")', 'console.log("hello");'),
            ('x = 1', 'var x = 1;')
        ]
        mock_extract.return_value = mock_pairs
        
        # Act
        main()
        
        # Assert
        # Verify ensure_dirs was called
        assert mock_ensure_dirs.called
        
        # Verify fetch_dataset was called
        assert mock_fetch.called
        
        # Verify extract_code_columns was called
        assert mock_extract.called

    def test_extract_code_columns_empty_dataset(self):
        """Test that extract_code_columns handles empty datasets."""
        # Arrange
        mock_dataset = MagicMock(spec=Dataset)
        mock_dataset.__len__ = MagicMock(return_value=0)
        mock_dataset.column_names = ['python_code', 'javascript_code']
        
        # Act
        result = extract_code_columns(mock_dataset)
        
        # Assert
        assert len(result) == 0

    @patch('src.ingestion.download_datasets.load_dataset')
    def test_fetch_dataset_handles_large_dataset(self, mock_load_dataset, tmp_path):
        """Test that fetch_dataset can handle large datasets via streaming."""
        # Arrange
        mock_stream_dataset = MagicMock()
        mock_stream_dataset.__iter__ = MagicMock(return_value=iter([
            {'python_code': 'code1', 'javascript_code': 'js1'},
            {'python_code': 'code2', 'javascript_code': 'js2'}
        ]))
        mock_load_dataset.return_value = mock_stream_dataset
        
        data_raw_dir = tmp_path / "data" / "raw"
        data_raw_dir.mkdir(parents=True)
        
        # Act
        result = fetch_dataset(
            dataset_name="codeparrot/code-trans-py-js",
            cache_dir=str(data_raw_dir),
            streaming=True
        )
        
        # Assert
        assert result is not None
        # Verify streaming was enabled
        mock_load_dataset.assert_called_with(
            "codeparrot/code-trans-py-js",
            cache_dir=str(data_raw_dir),
            streaming=True
        )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
