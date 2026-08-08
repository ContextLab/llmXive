"""Unit tests for the logging configuration in src/config.py."""
import logging
import os
import re
import tempfile
import shutil
from pathlib import Path
import pytest

from src.config import setup_logging


@pytest.fixture
def temp_logs_dir():
    """Create a temporary directory for log files and clean up after."""
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    shutil.rmtree(tmp_dir)


def test_logging_format(temp_logs_dir):
    """
    Verify that the logging format complies with the specification:
    Format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    Assert that a written log line matches the regex:
    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
    """
    log_file_path = os.path.join(temp_logs_dir, "test_config.log")
    
    # Setup logging using the project's configuration function
    logger = setup_logging(
        log_file=log_file_path,
        level=logging.DEBUG,
        max_bytes=10 * 1024 * 1024,  # 10MB
        backup_count=3
    )

    # Write a test log entry
    test_message = "Test logging format compliance for T010c"
    logger.info(test_message)

    # Read the log file content
    assert os.path.exists(log_file_path), f"Log file was not created at {log_file_path}"
    
    with open(log_file_path, 'r', encoding='utf-8') as f:
        log_content = f.read()

    # Ensure the message was written
    assert test_message in log_content, "Test message not found in log file"

    # Regex to match the timestamp format at the start of the log line
    # Expected format: YYYY-MM-DDTHH:MM:SS, followed by rest of the log line
    timestamp_regex = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'

    # Split by newlines to check individual log lines
    log_lines = log_content.strip().split('\n')
    
    found_valid_line = False
    for line in log_lines:
        if test_message in line:
            found_valid_line = True
            # Assert the line starts with the correct timestamp format
            assert re.match(timestamp_regex, line), (
                f"Log line format does not match specification. "
                f"Expected to start with YYYY-MM-DDTHH:MM:SS, but got: {line}"
            )
            break
    
    assert found_valid_line, f"Could not find log line containing '{test_message}' to validate format."