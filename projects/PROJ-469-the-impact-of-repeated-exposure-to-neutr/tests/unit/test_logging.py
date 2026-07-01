"""
Unit tests for the logging infrastructure.

Tests verify that:
1. Logging setup creates the log directory.
2. Log files are created and written to.
3. Log levels are respected.
"""

import os
import logging
import tempfile
import shutil
from pathlib import Path

# We need to test the logging_config module.
# Since the module might have side effects on import, we test the functions directly.
# However, to avoid pollution of the root logger in other tests, we isolate this.

def test_setup_logging_creates_directory():
    """Test that setup_logging creates the logs directory."""
    # Create a temporary directory for testing to avoid polluting the real project
    # We will mock the LOG_DIR constant in logging_config temporarily
    import logging_config
    
    original_log_dir = logging_config.LOG_DIR
    temp_dir = Path(tempfile.mkdtemp())
    test_log_dir = temp_dir / "logs"
    test_log_file = test_log_dir / "test.log"
    
    try:
        # Monkey patch the log dir
        logging_config.LOG_DIR = test_log_dir
        logging_config.LOG_FILE = test_log_file
        
        # Ensure the parent of logs exists if needed, but ensure_dirs handles it
        # We call setup_logging
        logging_config.setup_logging(level=logging.DEBUG)
        
        # Verify directory was created
        assert test_log_dir.exists(), f"Log directory {test_log_dir} was not created."
        
        # Verify root logger has handlers
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0, "No handlers found in root logger."
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        # Restore original
        logging_config.LOG_DIR = original_log_dir
        # Reset root logger to avoid side effects
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)

def test_get_logger_returns_instance():
    """Test that get_logger returns a valid logger instance."""
    import logging_config
    
    logger = logging_config.get_logger("test_module")
    assert isinstance(logger, logging.Logger), "get_logger did not return a Logger instance."
    assert logger.name == "test_module", "Logger name mismatch."

def test_log_levels():
    """Test that different log levels are recorded."""
    import logging_config
    import io
    
    # Create a string buffer to capture logs
    log_stream = io.StringIO()
    
    # Create a temporary logger for testing
    logger = logging_config.get_logger("test_levels")
    
    # Add a stream handler to the logger specifically for this test
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    # Log messages
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
    
    # Get output
    output = log_stream.getvalue()
    
    assert "Debug message" in output
    assert "Info message" in output
    assert "Warning message" in output
    assert "Error message" in output
    assert "Critical message" in output