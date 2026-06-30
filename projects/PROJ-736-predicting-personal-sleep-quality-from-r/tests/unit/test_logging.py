"""
Unit tests for the structured JSON logging module.
"""
import json
import logging
import os
import tempfile
from pathlib import Path

import pytest

# Import the module under test
# Note: Assuming the project root is in sys.path or installed
from code.utils import logging as logging_utils
from code.config import get_paths, ensure_dirs


@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def test_logger(temp_log_file):
    """Create a test logger with a temporary file."""
    logger = logging_utils.setup_logging(
        log_file=temp_log_file,
        level=logging.DEBUG,
        console_output=False,
    )
    return logger, temp_log_file


def test_json_formatter_format(test_logger):
    """Test that the JSON formatter produces valid JSON."""
    logger, log_file = test_logger
    logger.info("Test message")

    # Read and validate the log file
    with open(log_file, "r") as f:
        lines = f.readlines()

    assert len(lines) == 1
    log_entry = json.loads(lines[0])

    assert "timestamp" in log_entry
    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == "Test message"
    assert "logger" in log_entry


def test_log_event_with_data(test_logger):
    """Test logging an event with structured data."""
    logger, log_file = test_logger
    test_data = {"subject_id": 123, "status": "processed"}

    logging_utils.log_event(logger, "Subject processed", level="INFO", data=test_data)

    with open(log_file, "r") as f:
        lines = f.readlines()

    log_entry = json.loads(lines[0])
    assert log_entry["data"] == test_data


def test_log_stage_start(test_logger):
    """Test logging stage start."""
    logger, log_file = test_logger
    params = {"threshold": 0.5, "method": "PCA"}

    logging_utils.log_stage_start(logger, "preprocessing", parameters=params)

    with open(log_file, "r") as f:
        lines = f.readlines()

    log_entry = json.loads(lines[0])
    assert log_entry["message"] == "Stage 'preprocessing' started"
    assert log_entry["data"]["stage"] == "preprocessing"
    assert log_entry["data"]["parameters"] == params


def test_log_stage_complete(test_logger):
    """Test logging stage completion."""
    logger, log_file = test_logger
    metrics = {"accuracy": 0.85, "f1": 0.82}

    logging_utils.log_stage_complete(logger, "model_training", metrics=metrics)

    with open(log_file, "r") as f:
        lines = f.readlines()

    log_entry = json.loads(lines[0])
    assert log_entry["message"] == "Stage 'model_training' completed"
    assert log_entry["data"]["metrics"] == metrics


def test_log_stage_error(test_logger):
    """Test logging stage error."""
    logger, log_file = test_logger
    error = ValueError("Test error")

    logging_utils.log_stage_error(logger, "data_download", error)

    with open(log_file, "r") as f:
        lines = f.readlines()

    log_entry = json.loads(lines[0])
    assert log_entry["level"] == "ERROR"
    assert "data_download" in log_entry["message"]
    assert log_entry["data"]["error_type"] == "ValueError"


def test_multiple_log_entries(test_logger):
    """Test that multiple log entries are written correctly."""
    logger, log_file = test_logger

    logging_utils.log_stage_start(logger, "step1")
    logging_utils.log_event(logger, "intermediate", data={"step": 1})
    logging_utils.log_stage_complete(logger, "step1", metrics={"done": True})

    with open(log_file, "r") as f:
        lines = f.readlines()

    assert len(lines) == 3
    # Verify each line is valid JSON
    for line in lines:
        json.loads(line)