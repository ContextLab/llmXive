import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.download_study import get_study_download_url, download_study, DataUnavailableError

class TestDownloadStudy:
    def test_get_study_download_url_missing_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "missing.json"
            with pytest.raises(DataUnavailableError):
                get_study_download_url(manifest_path)

    def test_get_study_download_url_empty_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "empty.json"
            with open(manifest_path, 'w') as f:
                json.dump([], f)
            with pytest.raises(DataUnavailableError):
                get_study_download_url(manifest_path)

    @patch('data.download_study.requests.get')
    @patch('data.download_study.zipfile.ZipFile')
    def test_download_study_data_zip(self, mock_zip, mock_get):
        # Mock response
        mock_response = MagicMock()
        mock_response.content = b"fake zip content"
        mock_response.headers = {'Content-Type': 'application/zip'}
        mock_get.return_value = mock_response
        
        # Mock zip file content
        mock_zip_instance = MagicMock()
        mock_zip_instance.__enter__ = MagicMock(return_value=mock_zip_instance)
        mock_zip_instance.__exit__ = MagicMock(return_value=False)
        mock_zip_instance.namelist.return_value = ['intensity.csv', 'phenotype.csv']
        
        # Mock file reads
        mock_zip_instance.open.side_effect = [
            MagicMock(read=MagicMock(return_value=b"intensity data")),
            MagicMock(read=MagicMock(return_value=b"phenotype data"))
        ]
        mock_zip.return_value = mock_zip_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            study_id = "STUDY001"
            
            intensity_path, phenotype_path = download_study_data(
                "http://example.com/study.zip", output_dir, study_id
            )
            
            assert os.path.exists(intensity_path)
            assert os.path.exists(phenotype_path)
            assert os.path.getsize(intensity_path) > 0
            assert os.path.getsize(phenotype_path) > 0

    def test_download_study_entry_error(self):
        # Test with invalid entry
        entry = {"study_id": "X"} # Missing URL
        with tempfile.TemporaryDirectory() as tmpdir:
            result = download_study(entry, Path(tmpdir))
            assert result["status"] == "error"
            assert "Missing study_id or download_url" in result["reason"]