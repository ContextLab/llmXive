import os
import logging
import tempfile
import shutil
from pathlib import Path
import pytest

import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.config import setup_logging, LOG_FORMAT, LOG_MAX_BYTES, LOG_BACKUP_COUNT

@pytest.fixture
def temp_logs_dir():
    """Create a temporary directory for logs."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_logger_configuration(temp_logs_dir):
    """Test that the logger is configured correctly with rotation."""
    log_file = temp_logs_dir / "test_pipeline.log"

    # Setup logging with temporary directory
    logger = setup_logging(log_file=log_file)

    # Verify handlers are present
    assert len(logger.handlers) == 2  # File and console handlers

    # Verify file handler exists and is a RotatingFileHandler
    file_handler = None
    for handler in logger.handlers:
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            file_handler = handler
            break

    assert file_handler is not None, "RotatingFileHandler not found"
    assert file_handler.maxBytes == LOG_MAX_BYTES
    assert file_handler.backupCount == LOG_BACKUP_COUNT

    # Verify formatter
    formatter = file_handler.formatter
    assert formatter._fmt == LOG_FORMAT

    # Verify log file is created
    assert log_file.exists()

def test_log_insufficient_data(temp_logs_dir):
    """Test logging of insufficient data messages."""
    log_file = temp_logs_dir / "test_pipeline.log"
    logger = setup_logging(log_file=log_file)

    # Log a message
    logger.warning("Insufficient data for species: TestSpecies in grid cell: 1.0, 2.0")

    # Verify log file contains the message
    with open(log_file, 'r') as f:
        content = f.read()
        assert "Insufficient data" in content
        assert "TestSpecies" in content

def test_log_convergence_failure(temp_logs_dir):
    """Test logging of convergence failure messages."""
    log_file = temp_logs_dir / "test_pipeline.log"
    logger = setup_logging(log_file=log_file)

    # Log a convergence failure message
    logger.error("Convergence failed for species: TestSpecies: Error message")

    # Verify log file contains the message
    with open(log_file, 'r') as f:
        content = f.read()
        assert "Convergence failed" in content
        assert "TestSpecies" in content
        assert "ERROR" in content

def test_log_convergence_failure_no_year(temp_logs_dir):
    """Test logging of convergence failure without year."""
    log_file = temp_logs_dir / "test_pipeline.log"
    logger = setup_logging(log_file=log_file)

    # Log a convergence failure message without year
    logger.error("Convergence failed for species: TestSpecies: Error message")

    # Verify log file contains the message
    with open(log_file, 'r') as f:
        content = f.read()
        assert "Convergence failed" in content

def test_log_data_quality_flag(temp_logs_dir):
    """Test logging of data quality flags."""
    log_file = temp_logs_dir / "test_pipeline.log"
    logger = setup_logging(log_file=log_file)

    # Log a data quality message
    logger.info("Data quality flagged: insufficient observations")

    # Verify log file contains the message
    with open(log_file, 'r') as f:
        content = f.read()
        assert "Data quality flagged" in content

def test_file_creation(temp_logs_dir):
    """Test that log file is created and has content."""
    log_file = temp_logs_dir / "test_pipeline.log"
    logger = setup_logging(log_file=log_file)

    # Log a message
    logger.info("Test log message")

    # Verify log file exists and has content
    assert log_file.exists()
    assert log_file.stat().st_size > 0

def test_get_log_file_path(temp_logs_dir):
    """Test that the log file path is correctly set."""
    log_file = temp_logs_dir / "test_pipeline.log"
    logger = setup_logging(log_file=log_file)

    # Verify the log file path
    file_handler = None
    for handler in logger.handlers:
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            file_handler = handler
            break

    assert file_handler is not None
    assert file_handler.baseFilename == str(log_file)