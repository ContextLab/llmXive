"""
Unit tests for the logging configuration (T010).
"""
import os
import logging
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to mock the path resolution to test in a temp directory
# However, since the module creates the directory on import, we will
# test the functionality by importing and checking the handler configuration.

def test_logger_configuration():
    """Test that the logger is configured with RotatingFileHandler."""
    # Import the module to trigger setup
    from code.src.lib import logging_config
    
    logger = logging_config.logger
    
    # Verify logger name
    assert logger.name == "bird_migration_pipeline"
    
    # Verify handlers exist
    assert len(logger.handlers) >= 1
    
    # Find the file handler
    file_handler = None
    for handler in logger.handlers:
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            file_handler = handler
            break
    
    assert file_handler is not None, "RotatingFileHandler not found"
    
    # Verify maxBytes (10MB)
    assert file_handler.maxBytes == 10 * 1024 * 1024
    
    # Verify backupCount (5)
    assert file_handler.backupCount == 5
    
    # Verify formatter
    formatter = file_handler.formatter
    assert formatter._fmt == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def test_log_insufficient_data(caplog):
    """Test the specific logging function for insufficient data."""
    from code.src.lib import logging_config
    
    # Use caplog to capture logs from the logger
    with caplog.at_level(logging.WARNING):
        logging_config.log_insufficient_data(
            species="Swainson's Thrush",
            grid_cell="45.5,-122.5",
            reason="Observation density below threshold"
        )
    
    assert any("Insufficient data" in record.message for record in caplog.records)
    assert any("Swainson's Thrush" in record.message for record in caplog.records)
    assert any("Observation density" in record.message for record in caplog.records)

def test_log_convergence_failure(caplog):
    """Test the specific logging function for convergence failures."""
    from code.src.lib import logging_config
    
    with caplog.at_level(logging.ERROR):
        logging_config.log_convergence_failure(
            model_name="GAMM_Spatial",
            species="Blackpoll Warbler",
            error_msg="Singular fit encountered"
        )
    
    assert any("Convergence failure" in record.message for record in caplog.records)
    assert any("GAMM_Spatial" in record.message for record in caplog.records)
    assert any("Singular fit" in record.message for record in caplog.records)

def test_file_creation():
    """Verify that the log file is created in the expected location."""
    from code.src.lib import logging_config
    
    # The module calculates path relative to code/src/lib
    # Project root = code/../
    # Logs dir = code/../logs/
    # We need to resolve the actual path used
    # Since we can't easily mock the import-time path resolution without reloading,
    # we rely on the fact that the module creates the directory on import.
    
    # Check if the logs directory exists in the project root
    # Assuming standard project structure: code/src/lib/logging_config.py
    current_file_dir = Path(__file__).resolve().parent.parent.parent.parent # code/src/lib -> project root
    logs_dir = current_file_dir / "logs"
    
    assert logs_dir.exists(), f"Logs directory {logs_dir} does not exist"
    
    log_file = logs_dir / "pipeline.log"
    # The file might not exist if no logs were written, but the handler should be configured
    # to write to it. We trigger a write to ensure it exists.
    logging_config.logger.info("Test initialization")
    
    assert log_file.exists(), f"Log file {log_file} was not created"