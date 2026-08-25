import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.fetch_apt_zenodo import resolve_doi, download_file, fetch_apt_data
from code.errors import ExperimentalDataError

class TestResolveDoi:
    def test_resolve_doi_success(self):
        """Test successful DOI resolution."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "hits": {
                "hits": [
                    {"id": "1234567"}
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch('code.data.fetch_apt_zenodo.requests.get', return_value=mock_response):
            result = resolve_doi("10.5281/zenodo.1234567")
            assert result == "1234567"

    def test_resolve_doi_not_found(self):
        """Test DOI resolution when no record is found."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"hits": {"hits": []}}
        mock_response.raise_for_status = MagicMock()

        with patch('code.data.fetch_apt_zenodo.requests.get', return_value=mock_response):
            result = resolve_doi("10.5281/zenodo.9999999")
            assert result is None

    def test_resolve_doi_request_error(self):
        """Test DOI resolution when request fails."""
        with patch('code.data.fetch_apt_zenodo.requests.get', side_effect=Exception("Network error")):
            result = resolve_doi("10.5281/zenodo.1234567")
            assert result is None

class TestDownloadFile:
    def test_download_file_success(self, tmp_path):
        """Test successful file download."""
        mock_response = MagicMock()
        mock_response.content = b"fake file content"
        mock_response.raise_for_status = MagicMock()

        output_path = tmp_path / "test_file.csv"

        with patch('code.data.fetch_apt_zenodo.requests.get', return_value=mock_response):
            result = download_file("1234567", "test_file.csv", output_path)
            assert result is True
            assert output_path.exists()
            assert output_path.read_bytes() == b"fake file content"

    def test_download_file_failure(self, tmp_path):
        """Test file download when request fails."""
        with patch('code.data.fetch_apt_zenodo.requests.get', side_effect=Exception("Network error")):
            output_path = tmp_path / "test_file.csv"
            result = download_file("1234567", "test_file.csv", output_path)
            assert result is False

class TestFetchAptData:
    def test_fetch_apt_data_success(self, tmp_path):
        """Test successful fetch of multiple DOIs."""
        # Mock resolve_doi to return a record ID
        with patch('code.data.fetch_apt_zenodo.resolve_doi', return_value="1234567"):
            # Mock files listing
            mock_files_response = MagicMock()
            mock_files_response.json.return_value = {
                "files": [
                    {"key": "apt_data_fe_cr_mo.csv"}
                ]
            }
            mock_files_response.raise_for_status = MagicMock()

            # Mock file download
            mock_download_response = MagicMock()
            mock_download_response.content = b"test data"
            mock_download_response.raise_for_status = MagicMock()

            with patch('code.data.fetch_apt_zenodo.requests.get') as mock_get:
                # First call: list files
                mock_get.side_effect = [mock_files_response, mock_download_response]

                dois = ["10.5281/zenodo.1111111"]
                results = fetch_apt_data(dois)

                assert len(results["successful_downloads"]) == 1
                assert results["total_attempted"] == 1
                assert len(results["failed_downloads"]) == 0

    def test_fetch_apt_data_all_failures_raises_error(self):
        """Test that fetch_apt_data raises ExperimentalDataError when all downloads fail."""
        # Mock resolve_doi to return None (DOI not found)
        with patch('code.data.fetch_apt_zenodo.resolve_doi', return_value=None):
            dois = ["10.5281/zenodo.1111111", "10.5281/zenodo.2222222"]
            
            with pytest.raises(ExperimentalDataError) as exc_info:
                fetch_apt_data(dois)
            
            assert "CRITICAL" in str(exc_info.value)
            assert "Failed to fetch ANY ternary APT data" in str(exc_info.value)

    def test_fetch_apt_data_empty_dois(self):
        """Test fetch with empty DOI list."""
        results = fetch_apt_data([])
        assert results["total_attempted"] == 0
        assert len(results["successful_downloads"]) == 0
        assert len(results["failed_downloads"]) == 0