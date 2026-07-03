"""
Tests for the logging utility module.
"""
import logging
import os
import tempfile
from pathlib import Path

import pytest

# Add code directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.logging import (
    init_logging,
    get_logger,
    log_error,
    log_warning,
    log_info,
    log_progress,
    LoggingConfig,
)


@pytest.fixture
def temp_log_dir(tmp_path):
    """Provide a temporary directory for log files."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


@pytest.fixture
def temp_log_file(temp_log_dir):
    """Provide a temporary log file path."""
    return temp_log_dir / "test_pipeline.log"


def test_init_logging_creates_file(temp_log_dir, temp_log_file, monkeypatch):
    """Test that init_logging creates the log file and configures handlers."""
    # Override defaults to use temp paths
    config = LoggingConfig()
    config.log_dir = temp_log_dir
    config.log_file = temp_log_file
    config.console_enabled = False  # Silence console during test
    config.file_enabled = True

    # Clear root handlers first
    root = logging.getLogger()
    if root.handlers:
        root.handlers.clear()

    init_logging(config)

    assert temp_log_file.exists()
    # Check that root has handlers
    assert len(root.handlers) > 0


def test_get_logger_returns_named_logger():
    """Test that get_logger returns a logger with the correct name."""
    # Ensure init is called once
    if not logging.getLogger().handlers:
        config = LoggingConfig()
        config.console_enabled = False
        config.file_enabled = False
        init_logging(config)

    logger_name = "test.module.name"
    logger = get_logger(logger_name)

    assert isinstance(logger, logging.Logger)
    assert logger.name == logger_name
    assert logger.parent.name == "root"


def test_log_functions_write_to_logger(caplog):
    """Test that convenience log functions write messages."""
    logger_name = "test.funcs"
    if not logging.getLogger().handlers:
        config = LoggingConfig()
        config.console_enabled = False
        config.file_enabled = False
        init_logging(config)

    # Set level to INFO for this test
    logger = get_logger(logger_name)
    logger.setLevel(logging.INFO)

    with caplog.at_level(logging.INFO):
        log_info("Info message", logger_name)
        log_warning("Warning message", logger_name)
        log_error("Error message", logger_name)
        log_progress("Progress message", logger_name)

    assert "Info message" in caplog.text
    assert "Warning message" in caplog.text
    assert "Error message" in caplog.text
    assert "Progress message" in caplog.text


def test_logging_config_defaults():
    """Test that LoggingConfig has expected defaults."""
    config = LoggingConfig()
    assert config.level == logging.INFO
    assert config.console_enabled is True
    assert config.file_enabled is True
    assert "asctime" in config.format_string
    assert "levelname" in config.format_string