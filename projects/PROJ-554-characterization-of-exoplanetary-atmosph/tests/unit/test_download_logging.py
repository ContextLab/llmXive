import pytest
import logging
import tempfile
import os
from pathlib import Path
import sys

# Add project root to path if needed, assuming standard structure
# In real execution, this is handled by the runner
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.download import setup_download_logging, fetch_spectrum_data
from code.api_config import QUERY_PARAMS

class TestDownloadLogging:
    """
    Unit tests for T014: Logging for download progress and API response handling.
    """

    def test_setup_download_logging_creates_file(self):
        """Verifies that setup_download_logging creates the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_download.log"
            logger = setup_download_logging(log_path)
            
            assert log_path.exists(), "Log file should be created"
            assert logger.name != "", "Logger should be configured"
            
            # Check if handlers are added
            assert len(logger.handlers) >= 1, "Logger should have at least one handler"

    def test_setup_download_logging_writes_info(self):
        """Verifies that logging writes to the file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_download.log"
            logger = setup_download_logging(log_path)
            
            test_msg = "Test log message for T014"
            logger.info(test_msg)
            
            # Force flush
            for handler in logger.handlers:
                handler.flush()
            
            content = log_path.read_text()
            assert test_msg in content, f"Log message '{test_msg}' should be in file"
            assert "INFO" in content, "Log level INFO should be present"

    def test_fetch_spectrum_data_logs_request(self, mocker):
        """Verifies that fetch_spectrum_data logs the request details."""
        # Mock requests.get to avoid real network call
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.text = "mock,data"
        mock_response.headers = {"Content-Type": "text/csv"}
        
        mocker.patch('code.download.requests.get', return_value=mock_response)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_fetch.log"
            logger = setup_download_logging(log_path)
            
            # Call the function
            result = fetch_spectrum_data("test_planet")
            
            # Check logs
            for handler in logger.handlers:
                handler.flush()
            
            content = log_path.read_text()
            assert "API Request" in content, "Should log API request completion"
            assert "Status Code" in content, "Should log status code"
            assert "200" in content, "Should log 200 status"

    def test_fetch_spectrum_data_logs_error(self, mocker):
        """Verifies that fetch_spectrum_data logs errors correctly."""
        mock_response = mocker.Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        
        mocker.patch('code.download.requests.get', return_value=mock_response)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_error.log"
            logger = setup_download_logging(log_path)
            
            with pytest.raises(Exception): # DataFetchError or similar
                fetch_spectrum_data("test_planet")
            
            for handler in logger.handlers:
                handler.flush()
            
            content = log_path.read_text()
            assert "error" in content.lower(), "Should log error message"
            assert "404" in content, "Should log 404 status"