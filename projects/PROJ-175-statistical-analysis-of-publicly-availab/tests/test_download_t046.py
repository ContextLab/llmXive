import pytest
import os
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data.download import (
    DataUnavailableError, 
    verify_url_status, 
    load_verification_report,
    download_datasets
)

class TestT046HeadChecks:
    """Tests for T046: Pre-flight HEAD checks."""

    @patch('data.download.requests.head')
    def test_verify_url_status_success(self, mock_head):
        """Test that a 200 OK response returns True."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        result = verify_url_status("https://example.com/dataset")
        assert result is True
        mock_head.assert_called_once_with("https://example.com/dataset", timeout=10, allow_redirects=True)

    @patch('data.download.requests.head')
    def test_verify_url_status_failure(self, mock_head):
        """Test that a non-200 response raises DataUnavailableError."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response

        with pytest.raises(DataUnavailableError) as exc_info:
            verify_url_status("https://example.com/dataset")
        
        assert "404" in str(exc_info.value)

    @patch('data.download.requests.head')
    def test_verify_url_status_network_error(self, mock_head):
        """Test that a network exception raises DataUnavailableError."""
        mock_head.side_effect = Exception("Network Error")

        with pytest.raises(DataUnavailableError) as exc_info:
            verify_url_status("https://example.com/dataset")
        
        assert "Network" in str(exc_info.value)

    def test_verify_url_status_invalid_url(self):
        """Test that invalid URL format raises DataUnavailableError."""
        with pytest.raises(DataUnavailableError) as exc_info:
            verify_url_status("ftp://invalid.com")
        
        assert "Invalid URL" in str(exc_info.value)

    @patch('data.download.requests.head')
    def test_download_datasets_uses_head_checks(self, mock_head):
        """Test that download_datasets performs HEAD checks before proceeding."""
        # Mock the verification report
        mock_report = {
            "status": "PASS",
            "datasets": [
                {"name": "recipe1m", "url": "https://huggingface.co/datasets/recipe1m"}
            ]
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        # Create a temporary verification report for the test
        report_path = Path("data/verification_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(mock_report, f)

        try:
            # This should run the HEAD checks
            download_datasets()
            
            # Verify HEAD was called
            assert mock_head.called
            # Verify the log file was created
            assert Path("data/t046_head_check_log.json").exists()
        finally:
            # Cleanup
            if report_path.exists():
                report_path.unlink()
            log_path = Path("data/t046_head_check_log.json")
            if log_path.exists():
                log_path.unlink()

    @patch('data.download.requests.head')
    def test_download_datasets_fails_on_bad_head(self, mock_head):
        """Test that download_datasets fails if HEAD check returns non-200."""
        mock_report = {
            "status": "PASS",
            "datasets": [
                {"name": "recipe1m", "url": "https://huggingface.co/datasets/recipe1m"}
            ]
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_head.return_value = mock_response

        # Create a temporary verification report
        report_path = Path("data/verification_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(mock_report, f)

        try:
            with pytest.raises(DataUnavailableError):
                download_datasets()
        finally:
            if report_path.exists():
                report_path.unlink()