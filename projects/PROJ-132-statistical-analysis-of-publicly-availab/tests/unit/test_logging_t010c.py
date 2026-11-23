"""
Test task T010c: Test Logging.
Verifies that the logging configuration produces entries in the expected format.
"""
import logging
import os
import re
import tempfile
import shutil
from pathlib import Path
import pytest

from src.config import setup_logging


def test_logging_format_compliance():
    """
    Write a test log entry and parse it to ensure format compliance.
    
    The expected format is defined in src/config.py as:
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    This test:
    1. Creates a temporary directory for logs.
    2. Configures logging using the project's setup_logging function.
    3. Writes a test log entry.
    4. Reads the log file and parses the entry to verify format compliance.
    """
    # Create a temporary directory for logs
    temp_logs_dir = tempfile.mkdtemp()
    log_file_path = os.path.join(temp_logs_dir, "test_logging.log")
    
    try:
        # Configure logging
        logger = setup_logging(log_file_path)
        
        # Write a test log entry
        test_message = "Test log entry for format compliance"
        logger.info(test_message)
        
        # Read the log file
        with open(log_file_path, "r") as f:
            log_content = f.read()
        
        # Parse the log entry
        log_line = log_content.strip()
        
        # Define the expected format regex
        # Format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        # Example: '2023-10-01 12:34:56,789 - src.config - INFO - Test log entry for format compliance'
        log_pattern = (
            r'^(?P<asctime>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - '
            r'(?P<name>[^\s]+) - '
            r'(?P<levelname>\w+) - '
            r'(?P<message>.+)$'
        )
        
        match = re.match(log_pattern, log_line)
        
        assert match is not None, f"Log entry does not match expected format: {log_line}"
        
        # Extract parsed components
        parsed = match.groupdict()
        
        # Verify components
        assert parsed["asctime"], "Timestamp is missing"
        assert parsed["name"], "Logger name is missing"
        assert parsed["levelname"], "Log level is missing"
        assert parsed["message"], "Message is missing"
        
        # Verify specific values
        assert parsed["levelname"] == "INFO", f"Expected INFO level, got {parsed['levelname']}"
        assert parsed["message"] == test_message, f"Expected message '{test_message}', got '{parsed['message']}'"
        
        print(f"Log format verified successfully: {log_line}")
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_logs_dir, ignore_errors=True)
