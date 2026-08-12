import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.download import (
    _get_study_ids,
    _fetch_study_metadata,
    _download_study_files,
    download_metabolomics_data,
    DataUnavailableError
)
from code.utils.constants import PROJECT_ROOT

class TestDownloadUtils:
    def test_fallback_study_ids_missing_research(self):
        """Test that fallback IDs are returned if research.md is missing."""
        with patch('code.data.download.PROJECT_ROOT', Path(tempfile.gettempdir())):
            # Ensure no research.md in temp dir
            temp_md = Path(tempfile.gettempdir()) / "research.md"
            if temp_md.exists():
                temp_md.unlink()
            
            ids = _get_study_ids()
            assert len(ids) > 0
            # Fallback IDs should start with ST (Metabolomics Workbench format)
            assert all(id.startswith("ST") for id in ids)

    @patch('code.data.download.requests.get')
    def test_fetch_study_metadata_success(self, mock_get):
        """Test successful metadata fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "SUCCESS",
            "result": {
                "study_title": "Test Study",
                "data_files": [
                    {"file_type": "raw_intensity", "file_name": "test.csv"},
                    {"file_type": "phenotype", "file_name": "pheno.csv"}
                ]
            }
        }
        mock_get.return_value = mock_response

        result = _fetch_study_metadata("ST000000")
        assert result is not None
        assert result["study_title"] == "Test Study"
        mock_get.assert_called_once()

    @patch('code.data.download.requests.get')
    def test_fetch_study_metadata_failure(self, mock_get):
        """Test handling of failed metadata fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("Not Found")
        mock_get.return_value = mock_response

        result = _fetch_study_metadata("ST_INVALID")
        assert result is None

    @patch('code.data.download.requests.get')
    def test_download_study_files_success(self, mock_get):
        """Test successful file download and storage."""
        # Mock metadata response
        mock_meta = MagicMock()
        mock_meta.status_code = 200
        mock_meta.json.return_value = {
            "status": "SUCCESS",
            "result": {
                "study_title": "Test Study",
                "data_files": [
                    {"file_type": "raw_intensity", "file_name": "test.csv", "download_url": "http://example.com/test.csv"}
                ]
            }
        }

        # Mock file download response
        mock_file = MagicMock()
        mock_file.status_code = 200
        mock_file.content = b"sample_id,metabolite1\nS1,10.5\n"
        mock_file.headers = {"Content-Type": "text/csv"}
        
        # Sequence: first call returns metadata, second returns file
        mock_get.side_effect = [mock_meta, mock_file]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "ST000000"
            success = _download_study_files("ST000000", output_dir)
            
            assert success is True
            assert output_dir.exists()
            assert (output_dir / "test.csv").exists()
            
            # Verify content was written
            with open(output_dir / "test.csv", 'r') as f:
                content = f.read()
            assert "sample_id" in content

    @patch('code.data.download.requests.get')
    def test_download_study_files_failure(self, mock_get):
        """Test handling of failed file download."""
        mock_meta = MagicMock()
        mock_meta.status_code = 200
        mock_meta.json.return_value = {
            "status": "SUCCESS",
            "result": {
                "study_title": "Test Study",
                "data_files": [
                    {"file_type": "raw_intensity", "file_name": "test.csv", "download_url": "http://example.com/test.csv"}
                ]
            }
        }

        mock_file = MagicMock()
        mock_file.status_code = 404
        mock_get.side_effect = [mock_meta, mock_file]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "ST000000"
            success = _download_study_files("ST000000", output_dir)
            
            assert success is False

    def test_download_metabolomics_data_no_studies(self):
        """Test that DataUnavailableError is raised when no studies are found."""
        with patch('code.data.download._get_study_ids', return_value=[]):
            with tempfile.TemporaryDirectory() as tmpdir:
                with pytest.raises(DataUnavailableError):
                    download_metabolomics_data(Path(tmpdir))

    @patch('code.data.download._get_study_ids')
    @patch('code.data.download._fetch_study_metadata')
    @patch('code.data.download._download_study_files')
    def test_download_metabolomics_data_success(self, mock_download, mock_fetch, mock_ids):
        """Test successful download of multiple studies."""
        mock_ids.return_value = ["ST000001", "ST000002"]
        mock_fetch.side_effect = [
            {"status": "SUCCESS", "result": {"study_title": "Study 1"}},
            {"status": "SUCCESS", "result": {"study_title": "Study 2"}}
        ]
        mock_download.side_effect = [True, True]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = download_metabolomics_data(output_dir)
            
            assert result is True
            assert mock_ids.call_count == 1
            assert mock_fetch.call_count == 2
            assert mock_download.call_count == 2

    def test_data_unavailable_error(self):
        """Test DataUnavailableError custom exception."""
        with pytest.raises(DataUnavailableError) as exc_info:
            raise DataUnavailableError("No studies found")
        
        assert "No studies found" in str(exc_info.value)