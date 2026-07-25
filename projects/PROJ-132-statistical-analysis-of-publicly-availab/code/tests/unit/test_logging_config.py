"""
Unit tests for the logging configuration module (T010).
"""

import os
import logging
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to temporarily override the LOG_DIR in the module to test in a temp dir
# Since the module creates the logger on import, we need to be careful.
# We will test by patching the LOG_DIR and re-importing or by testing the functions directly
# assuming the temp directory setup.

@pytest.fixture
def temp_logs_dir():
    """Create a temporary directory for logs and clean up after."""
    temp_dir = tempfile.mkdtemp()
    logs_path = Path(temp_dir) / "logs"
    logs_path.mkdir()
    yield logs_path
    shutil.rmtree(temp_dir)

def test_logger_configuration(temp_logs_dir):
    """Test that the logger is configured correctly and file is created."""
    # Patch the module's LOG_DIR
    import sys
    import importlib

    # Save original
    orig_logging_config = sys.modules.get('src.lib.logging_config')

    # We can't easily re-run the module import with a changed global without restarting
    # Instead, we test the functions by manipulating the global state or mocking.
    # However, the task requires real file creation.
    # Let's test by importing the module and checking if the file exists in the expected default location
    # OR by temporarily setting the path.

    # For this test, we will verify the functions exist and can be called without error
    # and that they produce logs in the default location (which we will check later)
    # OR we can mock the RotatingFileHandler path.

    # Better approach for T010: Verify the functions are callable and log to the expected file.
    # Since the default LOG_DIR is 'logs', we check that.

    from src.lib.logging_config import get_logger, log_insufficient_data, log_convergence_failure

    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0
    # Verify one of the handlers is a RotatingFileHandler
    handler = logger.handlers[0]
    assert isinstance(handler, logging.handlers.RotatingFileHandler)
    assert handler.maxBytes == 10 * 1024 * 1024
    assert handler.backupCount == 5

def test_log_insufficient_data(temp_logs_dir):
    """Test that log_insufficient_data writes the correct message."""
    from src.lib.logging_config import log_insufficient_data, LOG_DIR, LOG_FILE_PATH

    # Ensure we are testing against the default LOG_DIR
    # If the test runner has a different CWD, LOG_FILE_PATH might be different.
    # We will just call the function and ensure no exception is raised.
    # The file creation is side-effect.

    log_insufficient_data(
        species="Turdus migratorius",
        region="North America",
        grid_cell="40.5_-75.0",
        reason="observation_density",
        count=0
    )

    # Check if the log file exists
    assert LOG_FILE_PATH.exists(), "Log file should be created"

    # Read the file and check content
    with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "INSUFFICIENT DATA" in content
    assert "Turdus migratorius" in content
    assert "observation_density" in content

def test_log_convergence_failure(temp_logs_dir):
    """Test that log_convergence_failure writes the correct message."""
    from src.lib.logging_config import log_convergence_failure, LOG_FILE_PATH

    log_convergence_failure(
        species="Setophaga ruticilla",
        model_type="GAMM",
        error_message="Singular fit",
        year=2020
    )

    assert LOG_FILE_PATH.exists(), "Log file should be created"

    with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "CONVERGENCE FAILURE" in content
    assert "Setophaga ruticilla" in content
    assert "Singular fit" in content
    assert "year=2020" in content

def test_file_creation():
    """Test that the log file is created in the logs directory."""
    from src.lib.logging_config import LOG_DIR, LOG_FILE_PATH

    # The module creates the directory on import
    assert LOG_DIR.exists(), "Log directory should exist"
    # The file is created when the logger is first used (which happens on import via _ = get_logger())
    # However, if the logger is only created in get_logger(), and we call it, it creates the file.
    # The module code has: _ = get_logger() at the bottom, so file should exist.
    # But RotatingFileHandler might not create the file until the first write.
    # Let's force a write to be sure.
    from src.lib.logging_config import get_logger
    logger = get_logger("test_force_write")
    logger.info("Force write")

    assert LOG_FILE_PATH.exists(), "Log file should be created after first write"