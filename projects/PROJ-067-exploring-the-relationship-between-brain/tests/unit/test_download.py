"""
Unit tests for the download module.
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from io import BytesIO
import tarfile

# Import the module under test
# Note: We assume the test runner is run from the project root
import sys
sys.path.insert(0, 'code')

from data.download import (
    load_valid_subjects,
    get_subject_urls,
    save_download_log,
    DATASET_ID,
    VALID_SUBJECTS_FILE,
    DOWNLOAD_LOG_FILE
)

class TestLoadValidSubjects:
    def test_load_valid_subjects_success(self, tmp_path):
        # Setup
        valid_file = tmp_path / "valid_subjects.json"
        test_data = {"subjects": ["001", "002", "003"]}
        valid_file.write_text(json.dumps(test_data))
        
        # Mock the path
        with patch('data.download.VALID_SUBJECTS_FILE', valid_file):
            result = load_valid_subjects()
            assert result == ["001", "002", "003"]

    def test_load_valid_subjects_list_format(self, tmp_path):
        # Setup
        valid_file = tmp_path / "valid_subjects.json"
        test_data = ["001", "002"]
        valid_file.write_text(json.dumps(test_data))
        
        with patch('data.download.VALID_SUBJECTS_FILE', valid_file):
            result = load_valid_subjects()
            assert result == ["001", "002"]

    def test_load_valid_subjects_not_found(self):
        with patch('data.download.VALID_SUBJECTS_FILE', Path("/nonexistent/path.json")):
            with pytest.raises(FileNotFoundError):
                load_valid_subjects()

    def test_load_valid_subjects_invalid_format(self, tmp_path):
        valid_file = tmp_path / "valid_subjects.json"
        valid_file.write_text(json.dumps({"invalid_key": ["001"]}))
        
        with patch('data.download.VALID_SUBJECTS_FILE', valid_file):
            with pytest.raises(ValueError):
                load_valid_subjects()

class TestSaveDownloadLog:
    def test_save_download_log_success(self, tmp_path):
        log_file = tmp_path / "download_log.json"
        
        with patch('data.download.DOWNLOAD_LOG_FILE', log_file):
            save_download_log(["001"], True)
            
            assert log_file.exists()
            with open(log_file, 'r') as f:
                data = json.load(f)
                assert data["success"] is True
                assert data["requested_subjects"] == ["001"]

    def test_save_download_log_error(self, tmp_path):
        log_file = tmp_path / "download_log.json"
        
        with patch('data.download.DOWNLOAD_LOG_FILE', log_file):
            save_download_log(["001"], False, error="Connection timeout")
            
            with open(log_file, 'r') as f:
                data = json.load(f)
                assert data["success"] is False
                assert data["error"] == "Connection timeout"

class TestGetSubjectUrls:
    @patch('data.download.requests.get')
    def test_get_subject_urls_success(self, mock_get, tmp_path):
        # Mock response for snapshots
        mock_snapshots = [
            {"id": "snapshot-1", "created": "2023-01-01", "tag": "1.0.0"},
            {"id": "snapshot-2", "created": "2023-01-02", "tag": "1.1.0"}
        ]
        mock_response = MagicMock()
        mock_response.json.return_value = mock_snapshots
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_subject_urls(["001", "002"])
        
        assert result["snapshot_id"] == "snapshot-2"
        assert result["version"] == "1.1.0"
        assert "1.1.0" in result["download_url"]
        assert result["subject_ids"] == ["001", "002"]

    @patch('data.download.requests.get')
    def test_get_subject_urls_empty_snapshots(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with pytest.raises(RuntimeError, match="No snapshots found"):
            get_subject_urls(["001"])

    @patch('data.download.requests.get')
    def test_get_subject_urls_request_error(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(RuntimeError, match="Failed to fetch"):
            get_subject_urls(["001"])