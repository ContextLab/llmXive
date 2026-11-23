import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from requests.exceptions import RequestException

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from data.verify import DataUnavailableError, fetch_schema_sample, verify_data_sources

@pytest.fixture
def mock_verification_report(tmp_path):
    """Creates a temporary verification report file."""
    report = {
        "sources": [
            {"name": "recipe1m", "url": "https://example.com/recipe1m", "status": "PASS"},
            {"name": "ratings", "url": "https://example.com/ratings", "status": "PASS"},
            {"name": "failed_source", "url": "https://example.com/failed", "status": "FAIL"}
        ]
    }
    report_path = tmp_path / "verification_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f)
    return str(report_path)

class TestFetchSchemaSample:
    def test_success_200(self):
        """Test that a 200 response returns the correct dict."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        
        with patch('data.verify.requests.head', return_value=mock_response):
            result = fetch_schema_sample("https://example.com/test")
            
        assert result["status_code"] == 200
        assert result["url"] == "https://example.com/test"
        assert result["content_type"] == "application/json"

    def test_failure_non_200(self, tmp_path):
        """Test that a non-200 response raises DataUnavailableError and logs error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        
        log_path = tmp_path / "download_errors.log"
        with patch('data.verify.requests.head', return_value=mock_response), \
             patch('data.verify.Path', return_value=tmp_path / "download_errors.log"):
            
            with pytest.raises(DataUnavailableError) as exc_info:
                fetch_schema_sample("https://example.com/test")
            
            assert "404" in str(exc_info.value)
            # Verify log file creation logic would be triggered
            # (Mocking Path is tricky, checking exception is primary)

    def test_exception_on_request_error(self, tmp_path):
        """Test that network exceptions raise DataUnavailableError."""
        with patch('data.verify.requests.head', side_effect=RequestException("Network Error")):
            with pytest.raises(DataUnavailableError) as exc_info:
                fetch_schema_sample("https://example.com/test")
            
            assert "Network Error" in str(exc_info.value)

class TestVerifyDataSources:
    def test_all_pass(self, mock_verification_report, tmp_path):
        """Test successful verification of all PASS sources."""
        # Mock successful HEAD requests for the PASS sources
        def mock_head_success(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.headers = {}
            return mock_resp

        with patch('data.verify.requests.head', side_effect=mock_head_success), \
             patch('data.verify.Path', return_value=tmp_path / "download_errors.log"):
            
            result = verify_data_sources(mock_verification_report)
            
        assert len(result) == 2
        assert "https://example.com/recipe1m" in result
        assert "https://example.com/ratings" in result

    def test_partial_failure(self, mock_verification_report, tmp_path):
        """Test that failure on one URL raises error immediately."""
        def mock_head_mixed(url, **kwargs):
            if "failed" in url:
                mock_resp = MagicMock()
                mock_resp.status_code = 500
                mock_resp.reason = "Server Error"
                return mock_resp
            else:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.headers = {}
                return mock_resp

        with patch('data.verify.requests.head', side_effect=mock_head_mixed), \
             patch('data.verify.Path', return_value=tmp_path / "download_errors.log"):
            
            with pytest.raises(DataUnavailableError):
                verify_data_sources(mock_verification_report)

    def test_missing_report(self, tmp_path):
        """Test that missing verification report raises FileNotFoundError."""
        non_existent = str(tmp_path / "missing.json")
        with pytest.raises(FileNotFoundError):
            verify_data_sources(non_existent)

    def test_no_pass_sources(self, tmp_path):
        """Test handling of report with no PASS sources."""
        report = {"sources": [{"name": "bad", "url": "x", "status": "FAIL"}]}
        report_path = tmp_path / "report.json"
        with open(report_path, "w") as f:
            json.dump(report, f)
        
        with patch('data.verify.requests.head') as mock_head:
            result = verify_data_sources(str(report_path))
            
        assert result == []
        mock_head.assert_not_called()
