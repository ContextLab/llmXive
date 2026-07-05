"""
Unit tests for the download module.

These tests verify the structure and error handling of the download functions.
They do not perform actual network requests to avoid flakiness in CI.
"""
import pytest
from unittest.mock import patch, MagicMock
import os
from pathlib import Path

# Import the module under test
from code.data.download import (
    download_lsms,
    download_nasa_power,
    download_faostat,
    _ensure_directories,
    _save_metadata
)
from utils.config import ConfigError


class TestDownloadLSMS:
    """Tests for download_lsms function."""

    @patch('code.data.download.requests.get')
    @patch('code.data.download.Path')
    @patch('code.data.download._save_metadata')
    @patch('code.data.download.log_provenance_mapping')
    def test_download_lsms_success(self, mock_log, mock_save_meta, mock_path, mock_get):
        """Test successful LSMS download."""
        # Mock the directory structure
        mock_dir = MagicMock()
        mock_path.return_value = mock_dir
        mock_dir.mkdir.return_value = None

        # Mock the search API response
        mock_search_response = MagicMock()
        mock_search_response.json.return_value = {
            'data': [
                {
                    'id': 'survey_123',
                    'country_code': 'KEN',
                    'title': 'Kenya LSMS 2021',
                    'year': 2021
                }
            ]
        }
        mock_search_response.raise_for_status.return_value = None

        # Mock the download response
        mock_download_response = MagicMock()
        mock_download_response.content = b"dummy,csv,data"
        mock_download_response.raise_for_status.return_value = None

        # Chain the mocks
        mock_get.side_effect = [mock_search_response, mock_download_response]

        # Call the function
        result = download_lsms("KEN", 2021)

        # Assertions
        assert result.endswith("lsms_ken_2021.csv")
        assert mock_get.call_count == 2
        mock_save_meta.assert_called_once()
        mock_log.assert_called_once()

    @patch('code.data.download.requests.get')
    def test_download_lsms_not_found(self, mock_get):
        """Test LSMS download when dataset is not found."""
        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response

        with pytest.raises(ConfigError, match="not found"):
            download_lsms("XYZ", 2099)

    @patch('code.data.download.requests.get')
    def test_download_lsms_timeout(self, mock_get):
        """Test LSMS download timeout."""
        mock_get.side_effect = Exception("Timeout")

        with pytest.raises(Exception, match="Timeout"):
            download_lsms("KEN", 2021)


class TestDownloadNASAPOWER:
    """Tests for download_nasa_power function."""

    @patch('code.data.download.requests.get')
    @patch('code.data.download.Path')
    @patch('code.data.download._save_metadata')
    @patch('code.data.download.log_provenance_mapping')
    def test_download_nasa_power_success(self, mock_log, mock_save_meta, mock_path, mock_get):
        """Test successful NASA POWER download."""
        mock_dir = MagicMock()
        mock_path.return_value = mock_dir
        mock_dir.mkdir.return_value = None

        mock_response = MagicMock()
        mock_response.text = "DATE,T2M\n2021-01-01,25.5"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = download_nasa_power(-1.29, 36.82, "2021-01-01", "2021-01-31")

        assert result.endswith("nasa_power_-1.29_36.82_20210101_20210131.csv")
        mock_get.assert_called_once()
        mock_save_meta.assert_called_once()
        mock_log.assert_called_once()

    @patch('code.data.download.requests.get')
    def test_download_nasa_power_error_response(self, mock_get):
        """Test NASA POWER download with error in response."""
        mock_response = MagicMock()
        mock_response.text = "ERROR: Invalid coordinates"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with pytest.raises(Exception, match="error"):
            download_nasa_power(999, 999, "2021-01-01", "2021-01-31")


class TestDownloadFAOSTAT:
    """Tests for download_faostat function."""

    @patch('code.data.download.requests.get')
    @patch('code.data.download.Path')
    @patch('code.data.download._save_metadata')
    @patch('code.data.download.log_provenance_mapping')
    def test_download_faostat_success(self, mock_log, mock_save_meta, mock_path, mock_get):
        """Test successful FAOSTAT download."""
        mock_dir = MagicMock()
        mock_path.return_value = mock_dir
        mock_dir.mkdir.return_value = None

        # Mock search response
        mock_search = MagicMock()
        mock_search.status_code = 200
        mock_search.raise_for_status.return_value = None

        # Mock download response
        mock_download = MagicMock()
        mock_download.text = "Country,Item,Value\nKEN,Wheat,100"
        mock_download.raise_for_status.return_value = None

        mock_get.side_effect = [mock_search, mock_download]

        result = download_faostat("151")  # Example item code

        assert result.endswith("faostat_151.csv")
        assert mock_get.call_count == 2
        mock_save_meta.assert_called_once()
        mock_log.assert_called_once()

    @patch('code.data.download.requests.get')
    def test_download_faostat_not_found(self, mock_get):
        """Test FAOSTAT download when indicator is not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(ConfigError, match="not found"):
            download_faostat("INVALID_CODE")


class TestUtilityFunctions:
    """Tests for utility functions."""

    @patch('code.data.download.Path')
    def test_ensure_directories(self, mock_path):
        """Test directory creation."""
        mock_dir = MagicMock()
        mock_path.return_value = mock_dir

        _ensure_directories()

        assert mock_dir.mkdir.called

    @patch('code.data.download.Path')
    @patch('builtins.open')
    @patch('code.data.download.json')
    def test_save_metadata(self, mock_json, mock_open, mock_path):
        """Test metadata saving."""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        metadata = {"key": "value"}
        _save_metadata("test_file", metadata)

        mock_open.assert_called_once()
        mock_json.dump.assert_called_once()