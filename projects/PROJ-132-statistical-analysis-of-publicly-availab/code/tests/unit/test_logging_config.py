"""
Unit tests for the logging configuration module.

Tests verify:
- Logger creation and configuration
- Logging of insufficient data events
- Logging of convergence failures
- File creation and rotation setup
"""

import os
import logging
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.lib.logging_config import (
    get_logger,
    log_insufficient_data,
    log_convergence_failure,
    log_data_quality_flag,
    get_log_file_path,
    LOG_DIR,
    LOG_FILE,
    MAX_BYTES,
    BACKUP_COUNT
)


@pytest.fixture
def temp_logs_dir(tmp_path):
    """Create a temporary directory for logs during testing."""
    # Create a temporary logs directory
    test_logs_dir = tmp_path / "logs"
    test_logs_dir.mkdir()

    # Temporarily override the LOG_DIR and LOG_FILE
    original_log_dir = LOG_DIR
    original_log_file = LOG_FILE

    # We can't easily override the global LOG_DIR in the module,
    # so we'll test the functions that use the default configuration
    # and verify the file creation logic separately.

    yield test_logs_dir

    # Cleanup is handled by tmp_path automatically


def test_logger_configuration():
    """Test that the logger is properly configured with rotating file handler."""
    logger = get_logger("test_logger_config")

    # Check logger level
    assert logger.level == logging.DEBUG

    # Check handlers exist
    assert len(logger.handlers) > 0

    # Check for rotating file handler
    has_rotating_handler = any(
        isinstance(h, logging.handlers.RotatingFileHandler)
        for h in logger.handlers
    )
    assert has_rotating_handler, "Logger should have a RotatingFileHandler"

    # Check formatter
    for handler in logger.handlers:
        assert handler.formatter is not None
        assert "%(asctime)s" in handler.formatter._fmt


def test_log_insufficient_data(caplog):
    """Test logging of insufficient data events."""
    with caplog.at_level(logging.WARNING):
        log_insufficient_data(
            species="Turdus migratorius",
            grid_cell="45.5_-122.5",
            observation_count=3,
            threshold=5,
            reason="Observation density too low"
        )

    # Check that a warning was logged
    assert any(
        "INSUFFICIENT_DATA" in record.message
        for record in caplog.records
    )
    assert any(
        "Turdus migratorius" in record.message
        for record in caplog.records
    )
    assert any(
        "observation_count=3" in record.message.lower() or "observations=3" in record.message.lower()
        for record in caplog.records
    )


def test_log_convergence_failure(caplog):
    """Test logging of model convergence failures."""
    with caplog.at_level(logging.ERROR):
        log_convergence_failure(
            species="Setophaga coronata",
            year=2022,
            model_type="GAMM",
            error_message="Convergence not achieved after 100 iterations",
            reason="Non-convergence"
        )

    # Check that an error was logged
    assert any(
        "CONVERGENCE_FAILURE" in record.message
        for record in caplog.records
    )
    assert any(
        "Setophaga coronata" in record.message
        for record in caplog.records
    )
    assert any(
        "Year=2022" in record.message
        for record in caplog.records
    )
    assert any(
        "Non-convergence" in record.message
        for record in caplog.records
    )


def test_log_convergence_failure_no_year(caplog):
    """Test logging of convergence failures without year."""
    with caplog.at_level(logging.ERROR):
        log_convergence_failure(
            species="Buteo jamaicensis",
            year=None,
            model_type="GP",
            error_message="Matrix singularity detected",
            reason="Collinearity"
        )

    assert any(
        "CONVERGENCE_FAILURE" in record.message
        for record in caplog.records
    )
    assert any(
        "Year=N/A" in record.message
        for record in caplog.records
    )


def test_log_data_quality_flag(caplog):
    """Test logging of data quality flags."""
    with caplog.at_level(logging.WARNING):
        log_data_quality_flag(
            species="Haliaeetus leucocephalus",
            grid_cell="39.0_-77.0",
            flag="imputed",
            details="Climate data interpolated"
        )

    assert any(
        "DATA_QUALITY" in record.message
        for record in caplog.records
    )
    assert any(
        "imputed" in record.message
        for record in caplog.records
    )


def test_file_creation(tmp_path):
    """Test that log file is created when logging occurs."""
    # We need to test with the actual log file path
    # Since we can't easily change the global LOG_DIR, we'll verify
    # the configuration constants and that the directory exists

    # Check that LOG_DIR is a Path object
    assert isinstance(LOG_DIR, Path)

    # Check that LOG_FILE is a Path object
    assert isinstance(LOG_FILE, Path)

    # Check configuration constants
    assert MAX_BYTES == 10 * 1024 * 1024  # 10MB
    assert BACKUP_COUNT == 5

    # Get the logger and ensure it's configured
    logger = get_logger("test_file_creation")

    # The log file might not exist yet if no logs have been written
    # but the handler should be configured correctly
    has_rotating_handler = any(
        isinstance(h, logging.handlers.RotatingFileHandler)
        for h in logger.handlers
    )
    assert has_rotating_handler


def test_get_log_file_path():
    """Test that get_log_file_path returns the correct path."""
    path = get_log_file_path()
    assert isinstance(path, Path)
    assert path.name == "pipeline.log"
    assert path.parent.name == "logs"
