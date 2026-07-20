import logging
import os
import tempfile
from pathlib import Path

import pytest

from code.utils.config import LOGS_DIR, LOG_FILE_NAME
from code.utils.logger import setup_logger


@pytest.fixture
def temp_logs_dir(monkeypatch):
    """Create a temporary directory for logs to avoid cluttering the real logs folder during tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("code.utils.logger.LOGS_DIR", tmpdir)
        yield Path(tmpdir)


def test_setup_logger_creates_file_handler(temp_logs_dir):
    logger = setup_logger("test_logger_1")
    assert logger is not None
    assert logger.level == logging.INFO

    # Check that a file handler exists
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) == 1

    file_path = file_handlers[0].baseFilename
    assert os.path.exists(file_path)
    assert "pipeline.log" in file_path


def test_setup_logger_creates_stream_handler():
    logger = setup_logger("test_logger_2")
    stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(stream_handlers) == 1


def test_logger_writes_to_file(temp_logs_dir):
    logger = setup_logger("test_logger_3")
    test_msg = "Test log message for file verification"
    logger.info(test_msg)

    log_file_path = Path(temp_logs_dir) / LOG_FILE_NAME
    assert log_file_path.exists()

    content = log_file_path.read_text()
    assert test_msg in content


def test_logger_format_includes_level():
    logger = setup_logger("test_logger_4")
    test_msg = "Level check"

    # Capture console output logic by checking handler formatter
    console_handler = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)][0]
    formatter = console_handler.formatter
    assert "%(levelname)s" in formatter._fmt


def test_logger_singleton_behavior():
    """Verify that calling setup_logger twice returns the same handler configuration."""
    logger1 = setup_logger("test_singleton")
    initial_count = len(logger1.handlers)

    logger2 = setup_logger("test_singleton")
    assert logger1 is logger2
    assert len(logger2.handlers) == initial_count