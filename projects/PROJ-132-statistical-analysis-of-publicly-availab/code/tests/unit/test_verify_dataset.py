"""
Unit tests for the dataset verification functionality.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.verify_dataset import verify_dataset_existence, main


class TestVerifyDataset:
    """Tests for the verify_dataset module."""

    @patch('src.data.verify_dataset.load_dataset')
    def test_verify_dataset_exists(self, mock_load_dataset):
        """Test that verification succeeds when dataset exists."""
        # Mock a dataset iterator
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter([{"species": "test"}]))
        mock_load_dataset.return_value = mock_ds

        result = verify_dataset_existence("vvud/eb-data")
        
        assert result is True
        mock_load_dataset.assert_called_once_with(
            "vvud/eb-data",
            split="train",
            streaming=True,
            trust_remote_code=True
        )

    @patch('src.data.verify_dataset.load_dataset')
    def test_verify_dataset_not_found(self, mock_load_dataset):
        """Test that verification raises RuntimeError when dataset is missing."""
        mock_load_dataset.side_effect = Exception("Dataset not found")

        with pytest.raises(RuntimeError) as exc_info:
            verify_dataset_existence("vvud/eb-data")

        assert "vvud/eb-data" in str(exc_info.value)
        assert "Critical Data Scope Note" in str(exc_info.value)

    @patch('src.data.verify_dataset.load_dataset')
    def test_verify_dataset_access_error(self, mock_load_dataset):
        """Test that verification raises RuntimeError when dataset is inaccessible."""
        mock_load_dataset.side_effect = Exception("Access denied")

        with pytest.raises(RuntimeError) as exc_info:
            verify_dataset_existence("vvud/eb-data")

        assert "vvud/eb-data" in str(exc_info.value)

    def test_main_success(self, tmp_path, caplog):
        """Test that main() returns 0 on success and writes report."""
        with patch('src.data.verify_dataset.setup_logging'), \
             patch('src.data.verify_dataset.verify_dataset_existence', return_value=True), \
             patch('src.data.verify_dataset.Path') as mock_path:
            
            # Setup mock for directory creation
            mock_provenance_dir = MagicMock()
            mock_path.return_value = mock_provenance_dir
            
            result = main()
            
            assert result == 0
            # Verify that a report was written
            mock_path.assert_called()

    def test_main_failure(self, caplog):
        """Test that main() returns 1 on failure."""
        with patch('src.data.verify_dataset.setup_logging'), \
             patch('src.data.verify_dataset.verify_dataset_existence', 
                   side_effect=RuntimeError("Dataset not found")):
            
            result = main()
            
            assert result == 1
            assert "Verification failed" in caplog.text