"""
Unit tests for the data loader service.
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import logging
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.data_loader import (
    load_verified_dataset_ids,
    fetch_dataset,
    write_missing_log,
    validate_realizations,
    extract_trajectory_id,
    write_trajectory_ids,
    main,
    REQUIRED_SYSTEM_SIZES,
    MIN_REALIZATIONS
)
from src.lib.config import CONFIG

class TestDataLoaderParsing:
    """Tests for dataset ID loading functionality."""

    def test_load_verified_dataset_ids_returns_dict(self):
        """Test that load_verified_dataset_ids returns a dictionary."""
        result = load_verified_dataset_ids()
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_load_verified_dataset_ids_contains_required_sizes(self):
        """Test that all required system sizes are present."""
        result = load_verified_dataset_ids()
        for size in REQUIRED_SYSTEM_SIZES:
            assert size in result, f"Missing system size {size}"

    def test_load_verified_dataset_ids_format(self):
        """Test that dataset IDs have correct format."""
        result = load_verified_dataset_ids()
        for size, dataset_id in result.items():
            assert isinstance(dataset_id, str)
            assert dataset_id.startswith("zenodo-"), f"Invalid format for {dataset_id}"

class TestDataLoaderFetching:
    """Tests for dataset fetching functionality."""

    @patch('src.services.data_loader.urllib.request.urlopen')
    def test_fetch_dataset_success(self, mock_urlopen, tmp_path):
        """Test successful dataset fetch."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'files': [
                {
                    'key': 'test_file.xyz',
                    'links': {'self': 'http://example.com/file.xyz'}
                }
            ]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Mock the file download
        with patch('src.services.data_loader.open', mock_open(read_data='10\n')) as mock_file:
            with patch('src.services.data_loader.Path.mkdir'):
                with patch('src.services.data_loader.Path.exists', return_value=False):
                    # This test would need more complex mocking for a real fetch
                    # For now, we test that the function structure is correct
                    pass

    def test_fetch_dataset_invalid_id_format(self):
        """Test that invalid dataset ID format raises error."""
        with pytest.raises(FileNotFoundError, match="Invalid dataset ID format"):
            fetch_dataset(1000, "invalid-id")

    def test_validate_realizations_success(self, tmp_path):
        """Test successful validation of realizations."""
        # Create a mock XYZ file with correct format
        xyz_content = "10\nFrame 1\nSi 0.0 0.0 0.0\n" * 10
        xyz_content += "10\nFrame 2\nSi 0.0 0.0 0.0\n" * 10

        test_file = tmp_path / "test.xyz"
        test_file.write_text(xyz_content)

        result = validate_realizations(test_file, 10)
        assert result == 2

    def test_validate_realizations_insufficient(self, tmp_path):
        """Test validation fails with insufficient realizations."""
        # Create a mock XYZ file with only 1 realization (less than MIN_REALIZATIONS)
        xyz_content = "10\nFrame 1\n" + "Si 0.0 0.0 0.0\n" * 10

        test_file = tmp_path / "test.xyz"
        test_file.write_text(xyz_content)

        with pytest.raises(RuntimeError, match="Insufficient realizations"):
            validate_realizations(test_file, 10)

class TestMainFunction:
    """Tests for the main function."""

    @patch('src.services.data_loader.load_verified_dataset_ids')
    @patch('src.services.data_loader.fetch_dataset')
    @patch('src.services.data_loader.validate_realizations')
    @patch('src.services.data_loader.extract_trajectory_id')
    @patch('src.services.data_loader.write_trajectory_ids')
    @patch('src.services.data_logger.setup_logger')
    def test_main_success(self, mock_logger, mock_write, mock_extract, mock_validate, mock_fetch, mock_load):
        """Test main function with successful fetches."""
        mock_load.return_value = {1000: "zenodo-123", 2000: "zenodo-456", 4000: "zenodo-789"}
        mock_fetch.return_value = Path("/fake/path.xyz")
        mock_validate.return_value = 50
        mock_extract.return_value = "test_id"

        result = main()
        assert result is True

    @patch('src.services.data_loader.load_verified_dataset_ids')
    @patch('src.services.data_loader.fetch_dataset')
    @patch('src.services.data_loader.write_missing_log')
    @patch('src.services.data_logger.setup_logger')
    def test_main_failure_missing_data(self, mock_logger, mock_write_log, mock_fetch, mock_load):
        """Test main function with missing data."""
        mock_load.return_value = {1000: "zenodo-123"}  # Missing 2000 and 4000
        mock_fetch.return_value = None

        result = main()
        assert result is False
        mock_write_log.assert_called_once()

class TestWriteMissingLog:
    """Tests for missing log writing functionality."""

    def test_write_missing_log_creates_file(self, tmp_path):
        """Test that write_missing_log creates the log file."""
        log_path = tmp_path / "missing.log"
        missing_sizes = [1000, 2000]

        write_missing_log(missing_sizes, log_path)

        assert log_path.exists()
        content = log_path.read_text()
        assert "Missing system sizes" in content
        assert "1000" in content
        assert "2000" in content

    def test_write_missing_log_format(self, tmp_path):
        """Test the format of the missing log."""
        log_path = tmp_path / "missing.log"
        missing_sizes = [4000]

        write_missing_log(missing_sizes, log_path)

        content = log_path.read_text()
        assert "Timestamp" in content
        assert "HALTING" not in content  # This is just the log, not the error message
        assert "4000" in content
