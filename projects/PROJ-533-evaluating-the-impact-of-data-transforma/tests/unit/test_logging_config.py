import os
import json
import tempfile
import logging
import pytest
from pathlib import Path

from code.utils.logging_config import (
    setup_pipeline_logger,
    JSONFormatter,
    AtomicFileHandler
)


def test_json_formatter_output():
    """Test that the JSON formatter produces valid JSON."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    record.extra_data = {"key": "value"}

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["level"] == "INFO"
    assert parsed["message"] == "Test message"
    assert parsed["data"]["key"] == "value"
    assert "timestamp" in parsed


def test_setup_pipeline_logger_creates_file(tmp_path):
    """Test that setup_pipeline_logger creates the log file."""
    log_file = tmp_path / "test.log"
    logger = setup_pipeline_logger("test_logger", str(log_file))

    # Log a message
    logger.info("Test message")

    assert log_file.exists()
    with open(log_file, 'r') as f:
        content = f.read()
        assert "Test message" in content
        # Verify it's valid JSON
        json.loads(content.strip())


def test_atomic_write(tmp_path):
    """Test that atomic writes work correctly."""
    log_file = tmp_path / "atomic.log"
    logger = setup_pipeline_logger("atomic_test", str(log_file))

    # Log multiple messages
    for i in range(5):
        logger.info(f"Message {i}")

    with open(log_file, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 5

        for line in lines:
            json.loads(line)  # Verify each line is valid JSON


def test_log_exclusion_helper(tmp_path):
    """Test the log_exclusion helper function."""
    from code.utils.logging_config import log_exclusion

    log_file = tmp_path / "exclusion.log"
    logger = setup_pipeline_logger("exclusion_test", str(log_file))

    log_exclusion(logger, "dataset_1", "missing_rate", "Details here")

    with open(log_file, 'r') as f:
        content = f.read()
        parsed = json.loads(content.strip())
        assert parsed["message"] == "Dataset Excluded"
        assert parsed["data"]["dataset_id"] == "dataset_1"
        assert parsed["data"]["reason"] == "missing_rate"