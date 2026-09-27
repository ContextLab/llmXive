"""
Unit tests for the pre-flight validation module.

These tests verify that the validation logic correctly identifies
missing and present dataset files.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
from validate_pre_flight import (
    validate_dataset_files,
    validate_all_datasets,
    abort_on_missing_datasets,
    run_pre_flight_check
)

# Import config for mocking
from config import DatasetNotFoundError


class TestValidateDatasetFiles:
    """Tests for the validate_dataset_files function."""

    def test_all_files_present(self, tmp_path):
        """Test validation when all required files exist."""
        # Create required files
        for i in range(3):
            (tmp_path / f"file_{i}.txt").touch()

        required_files = ["file_0.txt", "file_1.txt", "file_2.txt"]
        is_valid, missing = validate_dataset_files("test_dataset", required_files, tmp_path)

        assert is_valid is True
        assert len(missing) == 0

    def test_missing_files_detected(self, tmp_path):
        """Test validation when some files are missing."""
        # Create only one of three required files
        (tmp_path / "file_0.txt").touch()

        required_files = ["file_0.txt", "file_1.txt", "file_2.txt"]
        is_valid, missing = validate_dataset_files("test_dataset", required_files, tmp_path)

        assert is_valid is False
        assert len(missing) == 2
        assert any("file_1.txt" in m for m in missing)
        assert any("file_2.txt" in m for m in missing)

    def test_pattern_matching(self, tmp_path):
        """Test validation with wildcard patterns."""
        # Create files matching pattern
        (tmp_path / "data_001.txt").touch()
        (tmp_path / "data_002.txt").touch()
        (tmp_path / "other.txt").touch()

        required_files = ["data_*.txt"]
        is_valid, missing = validate_dataset_files("test_dataset", required_files, tmp_path)

        assert is_valid is True
        assert len(missing) == 0

    def test_pattern_no_matches(self, tmp_path):
        """Test validation when pattern matches no files."""
        (tmp_path / "data_001.txt").touch()

        required_files = ["video_*.mp4"]
        is_valid, missing = validate_dataset_files("test_dataset", required_files, tmp_path)

        assert is_valid is False
        assert len(missing) == 1
        assert "video_*.mp4" in missing


class TestValidateAllDatasets:
    """Tests for the validate_all_datasets function."""

    @patch('validate_pre_flight.get_dataset_paths')
    @patch('validate_pre_flight.get_required_files')
    def test_all_datasets_valid(self, mock_get_required, mock_get_paths, tmp_path):
        """Test when all datasets have required files."""
        # Setup mock paths
        mock_get_paths.return_value = {
            "NarrLV": tmp_path / "narrlv",
            "VBench": tmp_path / "vbench"
        }

        # Create directories and files
        for dataset_dir in mock_get_paths.return_value.values():
            dataset_dir.mkdir(parents=True, exist_ok=True)
            (dataset_dir / "required.txt").touch()

        # Setup mock required files
        mock_get_required.return_value = ["required.txt"]

        is_valid, missing = validate_all_datasets()

        assert is_valid is True
        assert len(missing) == 0

    @patch('validate_pre_flight.get_dataset_paths')
    @patch('validate_pre_flight.get_required_files')
    def test_missing_dataset_directory(self, mock_get_required, mock_get_paths):
        """Test when a dataset directory doesn't exist."""
        mock_get_paths.return_value = {
            "NarrLV": Path("/nonexistent/narrlv"),
            "VBench": Path("/nonexistent/vbench")
        }
        mock_get_required.return_value = ["required.txt"]

        is_valid, missing = validate_all_datasets()

        assert is_valid is False
        assert "NarrLV" in missing
        assert "VBench" in missing


class TestAbortOnMissingDatasets:
    """Tests for the abort_on_missing_datasets function."""

    def test_raises_dataset_not_found_error(self):
        """Test that the function raises DatasetNotFoundError."""
        missing_data = {
            "NarrLV": ["file1.txt", "file2.txt"],
            "VBench": ["file3.mp4"]
        }

        with pytest.raises(DatasetNotFoundError) as exc_info:
            abort_on_missing_datasets(missing_data)

        assert "PRE-FLIGHT VALIDATION FAILED" in str(exc_info.value)
        assert "NarrLV" in str(exc_info.value)
        assert "VBench" in str(exc_info.value)

    def test_error_message_contains_all_missing_files(self):
        """Test that error message includes all missing files."""
        missing_data = {
            "Dataset1": ["missing1.txt"],
            "Dataset2": ["missing2.txt", "missing3.txt"]
        }

        with pytest.raises(DatasetNotFoundError) as exc_info:
            abort_on_missing_datasets(missing_data)

        error_text = str(exc_info.value)
        assert "missing1.txt" in error_text
        assert "missing2.txt" in error_text
        assert "missing3.txt" in error_text


class TestRunPreFlightCheck:
    """Tests for the run_pre_flight_check function."""

    @patch('validate_pre_flight.validate_all_datasets')
    def test_returns_true_when_all_valid(self, mock_validate, caplog):
        """Test successful validation."""
        mock_validate.return_value = (True, {})

        result = run_pre_flight_check()

        assert result is True
        assert "PASSED" in caplog.text

    @patch('validate_pre_flight.validate_all_datasets')
    def test_raises_error_when_invalid(self, mock_validate):
        """Test that validation failure raises error."""
        mock_validate.return_value = (False, {"Dataset1": ["missing.txt"]})

        with pytest.raises(DatasetNotFoundError):
            run_pre_flight_check()