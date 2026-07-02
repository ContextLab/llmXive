"""
Unit tests for code/data/download.py

These tests verify:
1. Source ID validation logic (missing, invalid format, non-existent).
2. Interaction with the config module.
3. Basic logic flow without requiring actual network calls (mocked).
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from data.download import validate_source_id, get_dataset_metadata, run_download
from config import Config


class TestValidateSourceId:
    """Tests for the validate_source_id function."""

    def test_missing_id_raises_system_exit(self):
        """Test that missing ID raises SystemExit."""
        with pytest.raises(SystemExit, match="FATAL: No verified dataset source provided."):
            validate_source_id(None)

        with pytest.raises(SystemExit, match="FATAL: No verified dataset source provided."):
            validate_source_id("")

    def test_invalid_format_raises_system_exit(self):
        """Test that ID not starting with 'ds' raises SystemExit."""
        with pytest.raises(SystemExit, match="FATAL: Invalid dataset ID format."):
            validate_source_id("invalid_id")
        
        with pytest.raises(SystemExit, match="FATAL: Invalid dataset ID format."):
            validate_source_id("12345")

    @patch('data.download.get_dataset_metadata')
    def test_non_existent_id_raises_system_exit(self, mock_get_meta):
        """Test that ID not found on API raises SystemExit."""
        mock_get_meta.return_value = None
        
        with pytest.raises(SystemExit, match="FATAL: Verified dataset source not found on OpenNeuro."):
            validate_source_id("ds000001")

    @patch('data.download.get_dataset_metadata')
    def test_valid_id_returns_id(self, mock_get_meta):
        """Test that valid ID returns the ID string."""
        mock_get_meta.return_value = {"id": "ds000001", "name": "Test Dataset"}
        
        result = validate_source_id("ds000001")
        assert result == "ds000001"
        mock_get_meta.assert_called_once_with("ds000001")


class TestGetDatasetMetadata:
    """Tests for get_dataset_metadata function."""

    @patch('data.download.urllib.request.urlopen')
    def test_successful_fetch(self, mock_urlopen):
        """Test successful metadata fetch."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"id": "ds000001", "name": "Test"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = get_dataset_metadata("ds000001")
        
        assert result == {"id": "ds000001", "name": "Test"}
        mock_urlopen.assert_called_once()

    @patch('data.download.urllib.request.urlopen')
    def test_api_error_returns_none(self, mock_urlopen):
        """Test that API error returns None."""
        mock_response = MagicMock()
        mock_response.status = 404
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = get_dataset_metadata("ds000001")
        assert result is None

    @patch('data.download.urllib.request.urlopen')
    def test_network_error_returns_none(self, mock_urlopen):
        """Test that network error returns None."""
        mock_urlopen.side_effect = Exception("Network Error")

        result = get_dataset_metadata("ds000001")
        assert result is None


class TestRunDownload:
    """Tests for the run_download function."""

    @patch('data.download.validate_source_id')
    @patch('data.download.download_dataset_files')
    def test_run_download_success(self, mock_download, mock_validate):
        """Test successful download flow."""
        mock_validate.return_value = "ds000001"
        mock_download.return_value = [Path("data/raw/ds000001/sub-01.nii.gz")]
        
        # Create a minimal config mock
        config = MagicMock(spec=Config)
        config.OPENNEURO_DATASET_ID = "ds000001"
        config.DATA_RAW_DIR = Path("data/raw")

        files = run_download(config)

        mock_validate.assert_called_once_with("ds000001")
        mock_download.assert_called_once()
        assert len(files) == 1

    @patch('data.download.validate_source_id')
    def test_run_download_no_files(self, mock_validate):
        """Test that run_download fails if no files are downloaded."""
        mock_validate.return_value = "ds000001"
        
        with patch('data.download.download_dataset_files', return_value=[]):
            config = MagicMock(spec=Config)
            config.OPENNEURO_DATASET_ID = "ds000001"
            config.DATA_RAW_DIR = Path("data/raw")

            with pytest.raises(SystemExit, match="FATAL: Download produced no valid files."):
                run_download(config)

    @patch('data.download.validate_source_id')
    def test_run_download_validation_fail(self, mock_validate):
        """Test that run_download fails if validation fails."""
        mock_validate.side_effect = SystemExit("FATAL: No verified dataset source provided.")
        
        config = MagicMock(spec=Config)
        config.OPENNEURO_DATASET_ID = None

        with pytest.raises(SystemExit):
            run_download(config)
