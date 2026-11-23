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
    """Create a temporary directory for log files."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)

class TestLoggerConfiguration:
    """Test suite for logging configuration compliance (Task T010c)."""

    def test_logging_format_compliance(self, temp_logs_dir):
        """
        Verify that the logging format matches the specification:
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        and that the timestamp is ISO8601 compliant.
        """
        log_file = Path(temp_logs_dir) / "test_config.log"

        # Setup logging to file using the project's config function
        logger = setup_logging(
            name="test_logger",
            log_file=str(log_file),
            level=logging.DEBUG
        )

        # Write a test log entry
        test_message = "Test logging format compliance"
        logger.info(test_message)

        # Ensure the file is flushed and closed
        for handler in logger.handlers:
            handler.flush()
            handler.close()
            logger.removeHandler(handler)

        # Read the log file contents
        assert log_file.exists(), "Log file was not created."
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()

        assert len(log_content.strip()) > 0, "Log file is empty."

        # Parse the log line
        # Expected format: 2023-10-27 10:00:00,000 - test_logger - INFO - Test message
        # Regex breakdown:
        # ^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ISO8601-like timestamp
        # - (\w+) - Logger name
        # - (\w+) - Log level
        # - (.*) - Message
        log_pattern = re.compile(
            r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (\w+) - (.*)$"
        )

        match = log_pattern.match(log_content.strip())
        assert match, f"Log line does not match expected format. Content: {log_content}"

        timestamp_str, name, level, message = match.groups()

        # Assert components
        assert name == "test_logger", f"Logger name mismatch: {name}"
        assert level == "INFO", f"Log level mismatch: {level}"
        assert message == test_message, f"Message mismatch: {message}"

        # Assert ISO8601 timestamp format (YYYY-MM-DD HH:MM:SS,mmm)
        # We verify the structure strictly; full datetime parsing is optional but recommended
        timestamp_pattern = re.compile(
            r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}$"
        )
        assert timestamp_pattern.match(timestamp_str), \
            f"Timestamp is not ISO8601 compliant: {timestamp_str}"

        # Optional: Validate that the timestamp is actually a valid datetime
        from datetime import datetime
        try:
            datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
        except ValueError:
            pytest.fail(f"Timestamp string '{timestamp_str}' is not a valid datetime.")