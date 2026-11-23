"""
Tests for dataset downloader.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.data.download import (
    ensure_data_dirs,
    download_dataset,
    download_all_datasets,
)


class TestDownload:
    """Test suite for dataset download functionality."""

    def test_ensure_data_dirs_creates_directories(self, tmp_path):
        """Test that ensure_data_dirs creates required directories."""
        dirs = ensure_data_dirs(tmp_path)

        assert "raw" in dirs
        assert "processed" in dirs
        assert "results" in dirs

        for dir_path in dirs.values():
            assert dir_path.exists()
            assert dir_path.is_dir()

    @patch("src.data.download.load_dataset")
    def test_download_dataset_gsm8k(self, mock_load_dataset, tmp_path):
        """Test downloading GSM8K dataset."""
        # Mock the dataset
        mock_dataset = MagicMock()
        mock_dataset.__len__ = MagicMock(return_value=100)
        mock_load_dataset.return_value = mock_dataset

        dataset = download_dataset(
            "gsm8k",
            split="train",
            subset="main",
            output_dir=tmp_path,
        )

        # Verify load_dataset was called with correct parameters
        mock_load_dataset.assert_called_once_with(
            "gsm8k",
            "main",
            split="train",
            trust_remote_code=True,
        )

        assert dataset == mock_dataset

    @patch("src.data.download.load_dataset")
    def test_download_dataset_math(self, mock_load_dataset, tmp_path):
        """Test downloading MATH dataset."""
        mock_dataset = MagicMock()
        mock_dataset.__len__ = MagicMock(return_value=50)
        mock_load_dataset.return_value = mock_dataset

        dataset = download_dataset(
            "math",
            split="train",
            subset="train",
            output_dir=tmp_path,
        )

        mock_load_dataset.assert_called_once_with(
            "competition_math",
            "train",
            split="train",
            trust_remote_code=True,
        )

        assert dataset == mock_dataset

    def test_download_dataset_invalid_name(self, tmp_path):
        """Test that invalid dataset name raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported dataset"):
            download_dataset("invalid_dataset", output_dir=tmp_path)

    @patch("src.data.download.load_dataset")
    def test_download_dataset_save_to_disk(self, mock_load_dataset, tmp_path):
        """Test that dataset is saved to disk when output_dir is provided."""
        mock_dataset = MagicMock()
        mock_load_dataset.return_value = mock_dataset

        download_dataset(
            "gsm8k",
            split="train",
            output_dir=tmp_path,
        )

        # Verify save_to_disk was called
        mock_dataset.save_to_disk.assert_called_once()

    @patch("src.data.download.download_dataset")
    def test_download_all_datasets(self, mock_download_dataset, tmp_path):
        """Test downloading all datasets."""
        mock_dataset = MagicMock()
        mock_dataset.__len__ = MagicMock(return_value=100)
        mock_download_dataset.return_value = mock_dataset

        datasets = download_all_datasets(output_dir=tmp_path)

        # Check that GSM8K and MATH were attempted
        assert any("gsm8k" in key for key in datasets.keys())
        assert any("math" in key for key in datasets.keys())

        # Verify download_dataset was called multiple times
        assert mock_download_dataset.call_count >= 4  # 2 datasets x 2 splits