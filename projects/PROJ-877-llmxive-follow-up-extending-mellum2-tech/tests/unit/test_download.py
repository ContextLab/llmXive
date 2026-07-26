"""
Unit tests for code/data/download.py
Specifically testing error handling for network timeouts and empty datasets.
"""
import pytest
import time
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data import download
from code.utils.logging import NetworkError
from datasets import Dataset


class TestDownloadNetworkTimeout:
    """Tests for handling network timeouts during dataset fetching."""

    @patch('code.data.download.datasets')
    def test_download_handles_network_timeout(self, mock_datasets):
        """
        Verify that download.py handles network timeouts gracefully.
        
        When the dataset fetch times out, the function should:
        1. Raise a specific NetworkError (or let the underlying exception propagate)
        2. NOT fall back to synthetic data
        3. Log the error appropriately
        """
        # Mock the load_dataset to raise a timeout exception
        mock_datasets.load_dataset.side_effect = Exception("Timeout: The read operation timed out")
        
        # Mock config to avoid needing real config setup
        with patch('code.data.download.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                data_dir=Path("data"),
                max_chunks=10,
                languages=["python"]
            )
            
            # Mock logging to capture output
            with patch('code.data.download.get_logger') as mock_logger:
                mock_logger.return_value = MagicMock()
                
                # Verify that the function raises an error and doesn't proceed
                with pytest.raises(Exception, match="Timeout"):
                    # We expect the download function to fail loudly
                    # The actual implementation should not catch and swallow this
                    download.fetch_dataset_sample(
                        dataset_name="codeparrot/github-code",
                        languages=["python"],
                        max_samples=10
                    )

    @patch('code.data.download.datasets')
    def test_download_retry_logic_on_timeout(self, mock_datasets):
        """
        Verify that the download function attempts retries on transient network errors.
        """
        # First two calls fail with timeout, third succeeds
        mock_datasets.load_dataset.side_effect = [
            Exception("Timeout: The read operation timed out"),
            Exception("Timeout: The read operation timed out"),
            MagicMock(return_value=Dataset.from_dict({"code": ["sample"], "lang": ["python"]}))
        ]
        
        with patch('code.data.download.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                data_dir=Path("data"),
                max_chunks=10,
                languages=["python"]
            )
            
            with patch('code.data.download.get_logger') as mock_logger:
                mock_logger.return_value = MagicMock()
                
                # Should succeed on third attempt
                result = download.fetch_dataset_sample(
                    dataset_name="codeparrot/github-code",
                    languages=["python"],
                    max_samples=10
                )
                
                # Verify load_dataset was called 3 times
                assert mock_datasets.load_dataset.call_count == 3
                assert result is not None


class TestDownloadEmptyDataset:
    """Tests for handling empty datasets."""

    @patch('code.data.download.datasets')
    def test_download_handles_empty_dataset(self, mock_datasets):
        """
        Verify that download.py handles empty datasets (no matching chunks) gracefully.
        
        When the dataset returns no results:
        1. The function should raise a clear error
        2. It should NOT generate synthetic data as fallback
        3. It should log the specific error
        """
        # Mock an empty dataset
        mock_datasets.load_dataset.return_value = Dataset.from_dict({
            "code": [],
            "lang": []
        })
        
        with patch('code.data.download.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                data_dir=Path("data"),
                max_chunks=10,
                languages=["python"]
            )
            
            with patch('code.data.download.get_logger') as mock_logger:
                mock_logger.return_value = MagicMock()
                
                # Verify that the function raises an error for empty dataset
                with pytest.raises(ValueError, match="No chunks found"):
                    download.fetch_dataset_sample(
                        dataset_name="codeparrot/github-code",
                        languages=["python"],
                        max_samples=10
                    )

    @patch('code.data.download.datasets')
    def test_download_handles_empty_filtered_result(self, mock_datasets):
        """
        Verify handling when filtering by language results in empty dataset.
        """
        # Mock dataset with data but none matching the requested language
        mock_datasets.load_dataset.return_value = Dataset.from_dict({
            "code": ["sample1", "sample2"],
            "lang": ["java", "javascript"]  # No "python"
        })
        
        with patch('code.data.download.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                data_dir=Path("data"),
                max_chunks=10,
                languages=["python"]
            )
            
            with patch('code.data.download.get_logger') as mock_logger:
                mock_logger.return_value = MagicMock()
                
                # Should raise error because no python chunks found
                with pytest.raises(ValueError, match="No chunks found"):
                    download.fetch_dataset_sample(
                        dataset_name="codeparrot/github-code",
                        languages=["python"],
                        max_samples=10
                    )

    @patch('code.data.download.datasets')
    def test_download_success_with_data(self, mock_datasets):
        """
        Verify normal operation when data is available.
        """
        # Mock a dataset with valid data
        mock_datasets.load_dataset.return_value = Dataset.from_dict({
            "code": ["print('hello')", "def foo(): pass"],
            "lang": ["python", "python"]
        })
        
        with patch('code.data.download.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                data_dir=Path("data"),
                max_chunks=10,
                languages=["python"]
            )
            
            with patch('code.data.download.get_logger') as mock_logger:
                mock_logger.return_value = MagicMock()
                
                result = download.fetch_dataset_sample(
                    dataset_name="codeparrot/github-code",
                    languages=["python"],
                    max_samples=10
                )
                
                assert result is not None
                assert len(result) > 0