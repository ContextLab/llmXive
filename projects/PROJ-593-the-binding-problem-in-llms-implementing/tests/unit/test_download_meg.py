"""
Unit tests for the MEG data download module.
"""
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from datasets import Dataset

from src.data.download_meg import download_meg_streamed


class TestDownloadMegStreamed:
    """Test cases for download_meg_streamed function."""

    def test_download_meg_streamed_creates_file(self, tmp_path):
        """Test that the function creates the output file."""
        output_path = str(tmp_path / "test_meg.parquet")

        # Mock the load_dataset to return a simple streaming dataset
        mock_data = {
            'subject_id': [1, 2, 3],
            'trial_id': [101, 102, 103],
            'signal_data': [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        }
        mock_dataset = Dataset.from_dict(mock_data)

        with patch('src.data.download_meg.load_dataset') as mock_load:
            # Create a mock streaming iterator
            mock_load.return_value = mock_dataset

            download_meg_streamed(output_path)

            # Verify file was created
            assert os.path.exists(output_path)

            # Verify file is valid parquet
            df = pd.read_parquet(output_path)
            assert len(df) == 3
            assert list(df.columns) == ['subject_id', 'trial_id', 'signal_data']

    def test_download_meg_streamed_empty_dataset(self, tmp_path):
        """Test that the function raises on empty dataset."""
        output_path = str(tmp_path / "test_meg_empty.parquet")

        # Mock empty dataset
        mock_dataset = Dataset.from_dict({
            'subject_id': [],
            'trial_id': [],
            'signal_data': []
        })

        with patch('src.data.download_meg.load_dataset') as mock_load:
            mock_load.return_value = mock_dataset

            with pytest.raises(RuntimeError, match="Final concatenated dataset is empty"):
                download_meg_streamed(output_path)

    def test_download_meg_streamed_no_batches(self, tmp_path):
        """Test that the function raises when no batches are returned."""
        output_path = str(tmp_path / "test_meg_no_batches.parquet")

        # Mock dataset that yields nothing
        def empty_iterator():
            return iter([])

        with patch('src.data.download_meg.load_dataset') as mock_load:
            mock_load.return_value = empty_iterator()

            with pytest.raises(RuntimeError, match="Dataset returned no data batches"):
                download_meg_streamed(output_path)

    def test_download_meg_streamed_handles_exception(self, tmp_path):
        """Test that the function raises when download fails."""
        output_path = str(tmp_path / "test_meg_error.parquet")

        with patch('src.data.download_meg.load_dataset') as mock_load:
            mock_load.side_effect = Exception("Network error")

            with pytest.raises(RuntimeError, match="Failed to download real MEG data"):
                download_meg_streamed(output_path)
