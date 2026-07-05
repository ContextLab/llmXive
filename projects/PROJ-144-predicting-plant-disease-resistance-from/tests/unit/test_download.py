import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.download import _get_study_ids, _fetch_study_metadata
from code.utils.constants import PROJECT_ROOT

class TestDownloadUtils:
    def test_fallback_study_ids(self):
        """Test that fallback IDs are returned if research.md is missing."""
        with patch('code.data.download.PROJECT_ROOT', Path(tempfile.gettempdir())):
            # Ensure no research.md in temp dir
            temp_md = Path(tempfile.gettempdir()) / "research.md"
            if temp_md.exists():
                temp_md.unlink()
            
            ids = _get_study_ids()
            assert len(ids) > 0
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
                "data_files": []
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
