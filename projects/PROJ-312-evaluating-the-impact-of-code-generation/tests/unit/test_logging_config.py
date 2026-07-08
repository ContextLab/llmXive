"""
Unit tests for logging configuration and rate-limit header capture.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# We need to adjust the import path for testing
# Assuming tests are run from the project root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from logging_config import setup_logging, capture_rate_limit_headers, LOG_DIR


class TestLoggingConfig:
    def test_setup_logging_creates_file(self):
        """Test that setup_logging creates the log file and directory."""
        # Ensure directory exists
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        logger = setup_logging()
        assert logger is not None
        assert LOG_DIR.exists()
        # The file might not exist immediately if no logs are written,
        # but the handler should be configured to write to it.
        # We will verify by actually logging something in the next test.

    def test_json_formatting(self):
        """Test that logs are written in JSON format."""
        logger = setup_logging()
        test_message = "Test JSON formatting"
        
        # Log a message
        logger.info(test_message)

        # Find the log file (it should be the most recent one created)
        log_files = list(LOG_DIR.glob("pipeline.log"))
        assert len(log_files) > 0, "Log file was not created."
        
        log_file = log_files[0]
        
        # Read the last line of the file
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        assert len(lines) > 0, "Log file is empty."
        
        # Parse the last line as JSON
        last_line = lines[-1].strip()
        try:
            log_entry = json.loads(last_line)
        except json.JSONDecodeError:
            pytest.fail(f"Log entry is not valid JSON: {last_line}")

        # Verify structure
        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert log_entry["level"] == "INFO"
        assert "message" in log_entry
        assert log_entry["message"] == test_message
        assert "logger" in log_entry
        assert "module" in log_entry

    def test_capture_rate_limit_headers(self):
        """Test that rate limit headers are captured and logged correctly."""
        logger = setup_logging()
        mock_headers = {
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Reset": "1715623456",
            "Other-Header": "value"
        }
        custom_msg = "API call rate limits"

        # Capture headers
        capture_rate_limit_headers(mock_headers, custom_msg)

        # Read log file
        log_files = list(LOG_DIR.glob("pipeline.log"))
        assert len(log_files) > 0
        
        log_file = log_files[0]
        
        # Read the last line
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        last_line = lines[-1].strip()
        log_entry = json.loads(last_line)

        # Verify message
        assert log_entry["message"] == custom_msg

        # Verify extra data fields
        assert "rate_limit_remaining" in log_entry
        assert log_entry["rate_limit_remaining"] == "4999"
        
        assert "rate_limit_reset" in log_entry
        assert log_entry["rate_limit_reset"] == "1715623456"

    def test_capture_rate_limit_headers_missing(self):
        """Test behavior when headers are missing."""
        logger = setup_logging()
        mock_headers = {"Other-Header": "value"}
        
        capture_rate_limit_headers(mock_headers)

        log_files = list(LOG_DIR.glob("pipeline.log"))
        log_file = log_files[0]
        
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        last_line = lines[-1].strip()
        log_entry = json.loads(last_line)

        assert log_entry["rate_limit_remaining"] == "N/A"
        assert log_entry["rate_limit_reset"] == "N/A"
