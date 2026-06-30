"""
Unit tests for dataset_loader module.
"""
import os
import tempfile
import pandas as pd
from unittest.mock import patch, MagicMock
import pytest

from src.data.dataset_loader import (
    fetch_open_x_embodiment,
    save_to_parquet,
    load_open_x_embodiment_single_platform
)
from src.models.entities import DatasetSubset

class TestDatasetLoader:
    """Test cases for dataset loader functions."""

    @patch('src.data.dataset_loader.load_dataset')
    def test_fetch_open_x_embodiment_single_platform(self, mock_load_dataset):
        """Test fetching dataset with single platform filter."""
        # Mock the dataset
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {'robot_platform': 'franka', 'data': 'value1'},
            {'robot_platform': 'ur5', 'data': 'value2'},
            {'robot_platform': 'franka', 'data': 'value3'},
        ]))
        mock_load_dataset.return_value = mock_dataset

        # Fetch with filter
        df = fetch_open_x_embodiment(
            platform_filter=['franka'],
            streaming=True,
            max_rows=10
        )

        # Verify results
        assert len(df) == 2
        assert all(df['robot_platform'] == 'franka')

    @patch('src.data.dataset_loader.load_dataset')
    def test_fetch_open_x_embodiment_no_filter(self, mock_load_dataset):
        """Test fetching dataset without platform filter."""
        # Mock the dataset
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {'robot_platform': 'franka', 'data': 'value1'},
            {'robot_platform': 'ur5', 'data': 'value2'},
        ]))
        mock_load_dataset.return_value = mock_dataset

        # Fetch without filter
        df = fetch_open_x_embodiment(
            platform_filter=None,
            streaming=True,
            max_rows=10
        )

        # Verify results
        assert len(df) == 2

    def test_save_to_parquet(self):
        """Test saving DataFrame to Parquet."""
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test.parquet')
            save_to_parquet(df, output_path)

            # Verify file exists
            assert os.path.exists(output_path)

            # Verify content
            loaded_df = pd.read_parquet(output_path)
            assert len(loaded_df) == 3
            assert list(loaded_df.columns) == ['col1', 'col2']

    @patch('src.data.dataset_loader.fetch_open_x_embodiment')
    @patch('src.data.dataset_loader.save_to_parquet')
    @patch('src.data.dataset_loader.log_dataset_subset')
    def test_load_open_x_embodiment_single_platform(
        self, mock_log, mock_save, mock_fetch
    ):
        """Test loading single-platform dataset."""
        # Mock the fetched DataFrame
        mock_df = pd.DataFrame({
            'robot_platform': ['franka'] * 5,
            'data': ['value'] * 5
        })
        mock_fetch.return_value = mock_df

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_single.parquet')

            # Call the function
            result = load_open_x_embodiment_single_platform(
                output_path=output_path,
                platform_id='franka',
                max_rows=5
            )

            # Verify results
            assert isinstance(result, DatasetSubset)
            assert result.platform_id == 'franka'
            assert result.row_count == 5
            assert result.output_path == output_path

            # Verify save was called
            mock_save.assert_called_once()

            # Verify logging was called
            mock_log.assert_called_once()