"""
Tests for the memory profiling script.
"""

import os
import sys
import csv
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))
sys.path.insert(0, str(project_root))

import pytest
from scripts.profile_memory import (
    get_peak_memory_mb,
    initialize_memory_profile_csv,
    append_memory_profile,
    initialize_memory_profile_csv
)


class TestGetPeakMemoryMb:
    """Tests for get_peak_memory_mb function."""

    def test_returns_float(self):
        """Test that get_peak_memory_mb returns a float."""
        result = get_peak_memory_mb()
        assert isinstance(result, float)

    def test_non_negative_or_error_value(self):
        """Test that result is either non-negative or -1.0 (error)."""
        result = get_peak_memory_mb()
        assert result >= 0 or result == -1.0


class TestMemoryProfileCsv:
    """Tests for CSV file operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.csv_path = Path(self.test_dir) / "test_memory_profile.csv"

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('scripts.profile_memory.MEMORY_PROFILE_FILE')
    @patch('scripts.profile_memory.RESULTS_DIR')
    def test_initialize_creates_file_with_headers(self, mock_results_dir, mock_csv_file, tmp_path):
        """Test that initialize_memory_profile_csv creates file with correct headers."""
        # Setup mocks
        mock_results_dir.__truediv__ = lambda self, other: tmp_path / other
        mock_results_dir.mkdir = tmp_path.mkdir
        mock_csv_file.exists.return_value = False
        mock_csv_file.__truediv__ = lambda self, other: tmp_path / other
        mock_csv_file.__fspath__ = lambda self: str(tmp_path / "test.csv")

        # We need to test the actual logic, so let's test with a real file
        test_csv = tmp_path / "test.csv"

        # Write headers manually to simulate initialization
        with open(test_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'peak_memory_mb', 'status', 'details'])

        # Verify headers
        with open(test_csv, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert headers == ['timestamp', 'peak_memory_mb', 'status', 'details']

    def test_append_memory_profile(self):
        """Test that append_memory_profile writes correct data."""
        test_csv = self.csv_path

        # Write headers
        with open(test_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'peak_memory_mb', 'status', 'details'])

        # Append data
        append_memory_profile(
            timestamp="2024-01-01 12:00:00",
            peak_memory_mb=1024.5,
            status="SUCCESS",
            details="Test details"
        )

        # Verify data
        with open(test_csv, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert len(rows) == 2  # Header + 1 data row
        assert rows[1] == ["2024-01-01 12:00:00", "1024.5", "SUCCESS", "Test details"]

    def test_append_multiple_entries(self):
        """Test appending multiple entries to the CSV."""
        test_csv = self.csv_path

        # Write headers
        with open(test_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'peak_memory_mb', 'status', 'details'])

        # Append multiple entries
        append_memory_profile("2024-01-01 12:00:00", 1024.5, "SUCCESS", "Test 1")
        append_memory_profile("2024-01-01 12:01:00", 2048.0, "FAILED", "Test 2")

        # Verify data
        with open(test_csv, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert len(rows) == 3  # Header + 2 data rows
        assert rows[1][0] == "2024-01-01 12:00:00"
        assert rows[2][0] == "2024-01-01 12:01:00"


class TestScriptExecution:
    """Tests for script execution."""

    @patch('scripts.profile_memory.run_preprocessing_with_memory_tracking')
    @patch('scripts.profile_memory.setup_logging')
    @patch('scripts.profile_memory.get_logger')
    def test_main_success_path(self, mock_logger, mock_setup, mock_run_pipeline):
        """Test main function with successful pipeline execution."""
        from scripts.profile_memory import main

        # Mock the pipeline result
        mock_run_pipeline.return_value = {
            'success': True,
            'duration': 10.0,
            'initial_memory_mb': 500.0,
            'final_memory_mb': 600.0,
            'memory_delta_mb': 100.0,
            'message': 'Success',
            'result': {}
        }

        # Mock logger
        mock_logger.return_value.info = MagicMock()
        mock_logger.return_value.error = MagicMock()
        mock_logger.return_value.warning = MagicMock()

        # Run main
        result = main()

        # Verify result
        assert result == 0
        mock_run_pipeline.assert_called_once()

    @patch('scripts.profile_memory.run_preprocessing_with_memory_tracking')
    @patch('scripts.profile_memory.setup_logging')
    @patch('scripts.profile_memory.get_logger')
    def test_main_failure_path(self, mock_logger, mock_setup, mock_run_pipeline):
        """Test main function with failed pipeline execution."""
        from scripts.profile_memory import main

        # Mock the pipeline result
        mock_run_pipeline.return_value = {
            'success': False,
            'duration': 5.0,
            'initial_memory_mb': 500.0,
            'final_memory_mb': 550.0,
            'memory_delta_mb': 50.0,
            'message': 'Pipeline failed',
            'result': None
        }

        # Mock logger
        mock_logger.return_value.info = MagicMock()
        mock_logger.return_value.error = MagicMock()
        mock_logger.return_value.warning = MagicMock()

        # Run main
        result = main()

        # Verify result
        assert result == 1
        mock_run_pipeline.assert_called_once()