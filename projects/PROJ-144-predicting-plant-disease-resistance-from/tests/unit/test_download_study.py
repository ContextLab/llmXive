import pytest
import os
import json
import zipfile
import io
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust import path for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.download_study import (
    get_study_download_url,
    verify_temporal_separation,
    load_phenotype_metadata,
    TemporalVerificationError,
    DataUnavailableError
)

class TestTemporalVerification:
    def test_passes_on_pre_challenge(self):
        """Test that verification passes when 'pre-challenge' is found."""
        data = {
            "headers": ["sample_id", "treatment", "time"],
            "rows": [
                {"sample_id": "S1", "treatment": "pre-challenge", "time": "0"},
                {"sample_id": "S2", "treatment": "post-challenge", "time": "24"}
            ]
        }
        # Should not raise
        assert verify_temporal_separation(data, "STUDY_001") is True

    def test_passes_on_baseline(self):
        """Test that verification passes when 'baseline' is found."""
        data = {
            "headers": ["sample_id", "status"],
            "rows": [
                {"sample_id": "S1", "status": "baseline"},
            ]
        }
        assert verify_temporal_separation(data, "STUDY_001") is True

    def test_fails_on_missing_headers(self):
        """Test that verification fails if no temporal headers exist."""
        data = {
            "headers": ["sample_id", "metabolite"],
            "rows": [
                {"sample_id": "S1", "metabolite": "M1"}
            ]
        }
        with pytest.raises(TemporalVerificationError):
            verify_temporal_separation(data, "STUDY_001")

    def test_fails_on_no_pre_challenge_values(self):
        """Test that verification fails if headers exist but no pre-challenge rows."""
        data = {
            "headers": ["sample_id", "treatment"],
            "rows": [
                {"sample_id": "S1", "treatment": "post-challenge"},
                {"sample_id": "S2", "treatment": "infected"}
            ]
        }
        with pytest.raises(TemporalVerificationError):
            verify_temporal_separation(data, "STUDY_001")

    def test_fails_on_empty_rows(self):
        """Test that verification fails if no rows are present."""
        data = {
            "headers": ["sample_id", "treatment"],
            "rows": []
        }
        with pytest.raises(TemporalVerificationError):
            verify_temporal_separation(data, "STUDY_001")

class TestLoadPhenotypeMetadata:
    def test_loads_from_mock_zip(self, tmp_path):
        """Test loading metadata from a mock zip file."""
        zip_path = tmp_path / "test.zip"
        content = "sample_id\ttreatment\nS1\tpre-challenge\nS2\tpost-challenge"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("phenotype.txt", content)
        
        result = load_phenotype_metadata(zip_path, tmp_path)
        
        assert "headers" in result
        assert "sample_id" in result["headers"]
        assert len(result["rows"]) == 2
        assert result["rows"][0]["treatment"] == "pre-challenge"

class TestGetStudyDownloadUrl:
    @patch('data.download_study.requests.get')
    def test_returns_url_on_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"STUDY_ID": "ST000001"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        url = get_study_download_url("ST000001")
        assert url is not None
        assert "ST000001" in url
    
    @patch('data.download_study.requests.get')
    def test_returns_none_on_failure(self, mock_get):
        mock_get.side_effect = Exception("Network Error")
        url = get_study_download_url("ST000001")
        assert url is None
