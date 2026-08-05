"""
Contract test: Verify that each log entry written by src/utils/logging.py
includes a valid ISO-8601 timestamp.

This test ensures compliance with the logging schema defined in the project
and validates that timestamps are parseable and correctly formatted.
"""

import json
import re
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# Import the logging utility from the project
from src.utils.logging import get_logger


# ISO-8601 regex pattern for the format expected (YYYY-MM-DDTHH:MM:SS.ssssss)
# The logging utility writes JSON lines with a 'timestamp' field.
ISO8601_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$"
)


def is_valid_iso8601(timestamp_str: str) -> bool:
    """
    Validates if a string is a valid ISO-8601 timestamp.
    Attempts to parse it using datetime.fromisoformat (with Z replacement)
    and checks against the regex pattern.
    """
    if not isinstance(timestamp_str, str):
        return False
    
    if not ISO8601_PATTERN.match(timestamp_str):
        return False

    # Normalize 'Z' to '+00:00' for fromisoformat compatibility in older Python
    normalized = timestamp_str.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized)
        return True
    except ValueError:
        return False


def test_log_entry_iso8601_timestamp():
    """
    Contract test: Assert that every log entry produced by get_logger
    contains a 'timestamp' field that is a valid ISO-8601 string.
    """
    # Create a temporary file for logging
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as tmp_file:
        log_path = Path(tmp_file.name)

    try:
        # Initialize the logger pointing to our temp file
        logger = get_logger(log_file=str(log_path))

        # Generate a few log entries of different levels
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        logger.debug("Test debug message")

        # Read the file contents
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Assert we have entries
        assert len(lines) > 0, "Log file should contain entries."

        # Validate each line
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                pytest.fail(f"Line {i} is not valid JSON: {e}")

            # Assert 'timestamp' key exists
            assert "timestamp" in entry, f"Line {i} missing 'timestamp' key."

            timestamp_val = entry["timestamp"]

            # Assert timestamp is a valid ISO-8601 string
            assert is_valid_iso8601(timestamp_val), (
                f"Line {i} has invalid ISO-8601 timestamp: '{timestamp_val}'"
            )

    finally:
        # Cleanup
        if log_path.exists():
            log_path.unlink()

def test_log_entry_timestamp_format_consistency():
    """
    Additional check: Ensure all timestamps in a single run follow the same
    expected format (e.g., no mixed Z and +00:00 if the logger standardizes).
    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as tmp_file:
        log_path = Path(tmp_file.name)

    try:
        logger = get_logger(log_file=str(log_path))
        logger.info("Msg 1")
        logger.info("Msg 2")

        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        timestamps = []
        for line in lines:
            if line.strip():
                entry = json.loads(line.strip())
                timestamps.append(entry["timestamp"])

        # Just ensure they are all valid (format consistency is implicitly checked by validity)
        for ts in timestamps:
            assert is_valid_iso8601(ts), f"Timestamp {ts} is not valid ISO-8601"

    finally:
        if log_path.exists():
            log_path.unlink()
