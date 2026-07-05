"""
Unit tests for the logging utilities in code/utils/logging.py.
"""

import os
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# We need to mock the config module to avoid dependency on the full project setup
# during unit tests, or we can test the file writing logic directly.
# Here we test the logic by mocking the path resolution.

import pytest

# Import the module under test
from code.utils import logging as logging_module


@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary directory structure for logs."""
    logs_dir = tmp_path / "data" / "logs"
    errors_dir = tmp_path / "data" / "errors"
    logs_dir.mkdir(parents=True)
    errors_dir.mkdir(parents=True)
    return tmp_path


@pytest.fixture
def mock_config(temp_log_dir):
    """Mock the config functions to point to temp directories."""
    def mock_ensure_directories(paths):
        for p in paths:
            p.mkdir(parents=True, exist_ok=True)

    def mock_get_project_root():
        return temp_log_dir

    with patch.object(logging_module, 'ensure_directories', mock_ensure_directories):
        with patch.object(logging_module, 'get_project_root', mock_get_project_root):
            # Reset logger state to avoid cross-test contamination
            logging_module._logger = None
            logging_module._log_handler = None
            logging_module._exclusion_handler = None
            logging_module._error_handler = None
            yield temp_log_dir


def test_setup_logging(mock_config):
    """Test that setup_logging returns a logger and creates log files."""
    logger = logging_module.setup_logging()
    assert logger is not None
    assert logger.name == "llmXive.research"

    # Check if log directory was created (ensure_directories is mocked, but logic runs)
    # The actual file creation happens when a log is emitted, but the handler is set up.
    log_file = mock_config / "data" / "logs" / "pipeline.log"
    # The file might not exist yet if no log was emitted, but the handler should be configured.
    # We rely on the fact that the handler is added to the logger.
    assert len(logger.handlers) >= 1


def test_log_exclusion(mock_config):
    """Test that exclusions are logged to the CSV file."""
    logging_module.setup_logging()
    logging_module.log_exclusion(row_id=123, reason_code="MISSING_CONCENTRATION", details={"col": "val"})

    log_file = mock_config / "data" / "logs" / "exclusions.log"
    assert log_file.exists()

    with open(log_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]['row_id'] == '123'
    assert rows[0]['reason_code'] == 'MISSING_CONCENTRATION'
    assert rows[0]['details'] == "{'col': 'val'}"


def test_log_error(mock_config):
    """Test that errors are logged to the specific CSV file."""
    logging_module.setup_logging()
    logging_module.log_error(error_type="MISSING_RADIUS", message="Element X not found", row_id=456)

    error_file = mock_config / "data" / "errors" / "missing_atomic_data.csv"
    assert error_file.exists()

    with open(error_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]['error_type'] == 'MISSING_RADIUS'
    assert rows[0]['message'] == 'Element X not found'
    assert rows[0]['row_id'] == '456'


def test_log_warning(mock_config, caplog):
    """Test that warnings are logged to the main log."""
    logging_module.setup_logging()
    # Use caplog to capture the output of the logger
    with caplog.at_level(logging_module.logging.WARNING):
        logging_module.log_warning("Test warning message")

    assert "Test warning message" in caplog.text