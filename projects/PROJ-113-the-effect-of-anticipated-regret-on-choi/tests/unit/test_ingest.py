"""
Unit tests for the HuggingFace dataset loader in code/ingest.py.

This test file implements the contract test for T015, verifying that
the dataset loader correctly fetches and saves HuggingFace datasets.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
from code.ingest import load_huggingface_dataset, _ensure_directories, RAW_DATA_DIR


class TestLoadHuggingfaceDataset:
    """Tests for the load_huggingface_dataset function."""
    
    @patch('code.ingest.load_dataset')
    @patch('code.ingest.Path.mkdir')
    @patch('code.ingest.Path.to_parquet')
    @patch('code.ingest._calculate_sha256')
    @patch('code.ingest._load_existing_checksums')
    @patch('code.ingest._save_checksums')
    def test_load_primary_dataset_success(
        self, mock_save_checksums, mock_load_checksums, mock_calculate_sha,
        mock_to_parquet, mock_mkdir, mock_load_dataset
    ):
        """Test successful loading of the primary HuggingFace dataset."""
        # Setup mocks
        mock_ds = MagicMock()
        mock_load_dataset.return_value = mock_ds
        mock_calculate_sha.return_value = "abc123def456"
        mock_load_checksums.return_value = {}
        
        # Execute
        result_path = load_huggingface_dataset(
            "zhehuderek/textual_decisionmaking_data",
            split="train",
            save_raw=True
        )
        
        # Assertions
        mock_load_dataset.assert_called_once_with(
            "zhehuderek/textual_decisionmaking_data",
            split="train"
        )
        mock_ds.to_parquet.assert_called_once()
        assert result_path is not None
        assert str(result_path).endswith(".parquet")
        mock_save_checksums.assert_called_once()
    
    def test_invalid_dataset_name(self):
        """Test that an invalid dataset name raises ValueError."""
        with pytest.raises(ValueError, match="not recognized"):
            load_huggingface_dataset("invalid/dataset_name")
    
    @patch('code.ingest.load_dataset')
    def test_load_dataset_failure(self, mock_load_dataset):
        """Test that dataset loading failure raises Exception."""
        mock_load_dataset.side_effect = Exception("Dataset not found")
        
        with pytest.raises(Exception, match="Failed to load dataset"):
            load_huggingface_dataset(
                "zhehuderek/textual_decisionmaking_data",
                split="train"
            )
    
    @patch('code.ingest.load_dataset')
    @patch('code.ingest.Path.mkdir')
    @patch('code.ingest.Path.to_parquet')
    @patch('code.ingest._calculate_sha256')
    @patch('code.ingest._load_existing_checksums')
    @patch('code.ingest._save_checksums')
    def test_load_secondary_dataset_success(
        self, mock_save_checksums, mock_load_checksums, mock_calculate_sha,
        mock_to_parquet, mock_mkdir, mock_load_dataset
    ):
        """Test successful loading of the secondary HuggingFace dataset."""
        # Setup mocks
        mock_ds = MagicMock()
        mock_load_dataset.return_value = mock_ds
        mock_calculate_sha.return_value = "xyz789abc123"
        mock_load_checksums.return_value = {}
        
        # Execute
        result_path = load_huggingface_dataset(
            "PhillyMac/Decision_Making_Content_1",
            split="train",
            save_raw=True
        )
        
        # Assertions
        mock_load_dataset.assert_called_once_with(
            "PhillyMac/Decision_Making_Content_1",
            split="train"
        )
        mock_ds.to_parquet.assert_called_once()
        assert result_path is not None
        assert str(result_path).endswith(".parquet")
    
    @patch('code.ingest.load_dataset')
    @patch('code.ingest.Path.mkdir')
    @patch('code.ingest.Path.to_parquet')
    def test_load_dataset_no_save(self, mock_to_parquet, mock_mkdir, mock_load_dataset):
        """Test loading dataset without saving to disk."""
        # Setup mocks
        mock_ds = MagicMock()
        mock_load_dataset.return_value = mock_ds
        
        # Execute
        result_path = load_huggingface_dataset(
            "zhehuderek/textual_decisionmaking_data",
            split="train",
            save_raw=False
        )
        
        # Assertions
        mock_ds.to_parquet.assert_not_called()
        assert str(result_path).startswith("<dataset:")
        assert "zhehuderek/textual_decisionmaking_data" in str(result_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])