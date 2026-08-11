"""
Unit tests for the data_fetcher module.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_fetcher import fetch_ukbiobank_data, check_local_fallback
from config import INPUT_PATHS

class TestDataFetcher:
    """Test cases for data fetching functionality."""

    @patch('data_fetcher.load_dataset')
    def test_fetch_success(self, mock_load_dataset, tmp_path):
        """Test that fetch succeeds when remote source is available."""
        # Mock the dataset iterator
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([{"id": 1, "value": 10}]))
        mock_load_dataset.return_value = mock_dataset

        output_dir = tmp_path / "raw"
        output_dir.mkdir()

        result = fetch_ukbiobank_data(output_dir)

        assert result == output_dir
        assert (output_dir / ".source_verified").exists()
        mock_load_dataset.assert_called_once()

    def test_fetch_fails_loudly(self, tmp_path):
        """Test that fetch raises FileNotFoundError when remote source is unavailable."""
        # Mock load_dataset to raise an exception
        with patch('data_fetcher.load_dataset') as mock_load_dataset:
            mock_load_dataset.side_effect = Exception("Dataset not found")
            
            output_dir = tmp_path / "raw"
            output_dir.mkdir()

            with pytest.raises(FileNotFoundError) as excinfo:
                fetch_ukbiobank_data(output_dir)
            
            assert "CRITICAL FAILURE" in str(excinfo.value)
            assert "ukbiobank/microbiome-cognitive" in str(excinfo.value)

    def test_local_fallback_found(self, tmp_path):
        """Test that local fallback is detected when files exist."""
        output_dir = tmp_path / "raw"
        output_dir.mkdir()
        
        # Create a mock local file
        (output_dir / "microbiome_data.csv").touch()
        
        assert check_local_fallback(output_dir) is True

    def test_local_fallback_not_found(self, tmp_path):
        """Test that local fallback returns False when no files exist."""
        output_dir = tmp_path / "raw"
        output_dir.mkdir()
        
        assert check_local_fallback(output_dir) is False