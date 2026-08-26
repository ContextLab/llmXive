"""
Unit tests for the data validator module (T055).

Tests verify that the validator correctly checks for file existence,
size > 0, and raises appropriate exceptions for missing or invalid files.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.validator import verify_raw_datasets, DataValidationError
from src.utils.config import get_path


class TestValidator:
    """Tests for the data validator module."""

    def test_verify_raw_datasets_missing_directory(self):
        """Test that verify_raw_datasets raises FileNotFoundError if raw dir is missing."""
        with patch('src.data.validator.get_path') as mock_get_path:
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_get_path.return_value = mock_path

            with pytest.raises(FileNotFoundError) as exc_info:
                verify_raw_datasets()

            assert "Raw data directory does not exist" in str(exc_info.value)

    def test_verify_raw_datasets_missing_file(self, tmp_path):
        """Test that verify_raw_datasets raises DataValidationError for missing files."""
        # Create a temporary directory structure
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)

        # Mock get_path to return our temp directory
        with patch('src.data.validator.get_path') as mock_get_path, \
             patch('src.data.validator.get_all_source_names') as mock_get_all, \
             patch('src.data.validator.get_source_info') as mock_get_info:

            mock_get_path.return_value = raw_dir
            mock_get_all.return_value = ["test_dataset"]
            mock_get_info.return_value = {"expected_filename": "test_dataset.csv"}

            with pytest.raises(DataValidationError) as exc_info:
                verify_raw_datasets()

            assert "Missing files" in str(exc_info.value)
            assert "test_dataset" in str(exc_info.value)

    def test_verify_raw_datasets_empty_file(self, tmp_path):
        """Test that verify_raw_datasets raises DataValidationError for empty files."""
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)

        # Create an empty file
        empty_file = raw_dir / "test_dataset.csv"
        empty_file.touch()

        with patch('src.data.validator.get_path') as mock_get_path, \
             patch('src.data.validator.get_all_source_names') as mock_get_all, \
             patch('src.data.validator.get_source_info') as mock_get_info:

            mock_get_path.return_value = raw_dir
            mock_get_all.return_value = ["test_dataset"]
            mock_get_info.return_value = {"expected_filename": "test_dataset.csv"}

            with pytest.raises(DataValidationError) as exc_info:
                verify_raw_datasets()

            assert "Invalid files" in str(exc_info.value)
            assert "size=0" in str(exc_info.value)

    def test_verify_raw_datasets_success(self, tmp_path):
        """Test that verify_raw_datasets returns True for valid files."""
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)

        # Create a valid file with content
        valid_file = raw_dir / "test_dataset.csv"
        valid_file.write_text("col1,col2\n1,2\n3,4")

        with patch('src.data.validator.get_path') as mock_get_path, \
             patch('src.data.validator.get_all_source_names') as mock_get_all, \
             patch('src.data.validator.get_source_info') as mock_get_info:

            mock_get_path.return_value = raw_dir
            mock_get_all.return_value = ["test_dataset"]
            mock_get_info.return_value = {"expected_filename": "test_dataset.csv"}

            result = verify_raw_datasets()

            assert result is True

    def test_verify_raw_datasets_specific_dataset(self, tmp_path):
        """Test that verify_raw_datasets can verify a specific dataset."""
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)

        # Create a valid file
        valid_file = raw_dir / "specific_dataset.csv"
        valid_file.write_text("data")

        with patch('src.data.validator.get_path') as mock_get_path, \
             patch('src.data.validator.get_source_info') as mock_get_info:

            mock_get_path.return_value = raw_dir
            mock_get_info.return_value = {"expected_filename": "specific_dataset.csv"}

            # Verify only the specific dataset
            result = verify_raw_datasets(required_datasets=["specific_dataset"])

            assert result is True