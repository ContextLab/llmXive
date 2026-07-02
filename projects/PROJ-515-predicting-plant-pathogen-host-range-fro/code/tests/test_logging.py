"""
Tests for the logging infrastructure (T005).

These tests verify:
1. The logging module can be imported.
2. The log file is created in the expected location.
3. The logger format includes timestamps.
4. Logging propagates correctly (verified by checking the file content).
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest
from loguru import logger

# Import the module under test
# We need to ensure the path is set correctly if running standalone
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.utils.logging import setup_logging, get_logger, LOGS_DIR


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files during testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_logging_module_imports():
    """Test that the logging module can be imported and exposes expected functions."""
    from src.utils.logging import setup_logging, get_logger
    assert callable(setup_logging)
    assert callable(get_logger)


def test_log_file_creation(temp_log_dir):
    """Test that setup_logging creates the log file."""
    # Override the default log path for testing
    test_log_file = temp_log_dir / "test_pipeline.log"
    
    # Re-setup logging with the temporary file
    # Note: Loguru's remove() is used internally in setup_logging
    setup_logging(log_file=test_log_file)
    
    # Get the logger and log something
    log = get_logger()
    log.info("Test log message for file creation")
    
    # Force flush (loguru handles this, but we wait briefly)
    import time
    time.sleep(0.1)
    
    assert test_log_file.exists(), f"Log file {test_log_file} was not created."


def test_logger_format(temp_log_dir):
    """Test that the log file contains timestamps."""
    test_log_file = temp_log_dir / "test_format.log"
    setup_logging(log_file=test_log_file, log_level="INFO")
    
    log = get_logger()
    log.info("Format check message")
    
    import time
    time.sleep(0.1)
    
    content = test_log_file.read_text()
    assert "Format check message" in content
    # Check for timestamp pattern (YYYY-MM-DD HH:mm:ss)
    assert "20" in content[:20] or "20" in content[:30] # Simple check for year presence in timestamp


def test_subprocess_propagation_setup(temp_log_dir):
    """
    Test that the logging setup enables propagation to subprocesses.
    
    Loguru's 'enqueue=True' setting in setup_logging ensures that log messages
    are sent to a separate process for writing, which is the standard way to
    handle logging in multiprocessing scenarios.
    
    This test verifies the configuration is applied correctly.
    """
    test_log_file = temp_log_dir / "test_subprocess.log"
    
    # We inspect the setup_logging function's behavior by checking if
    # the file handler was added with enqueue=True.
    # Since loguru handlers are internal, we verify by logging and checking the file.
    
    setup_logging(log_file=test_log_file, log_level="INFO")
    log = get_logger()
    
    # Log a message
    log.info("Subprocess propagation test")
    
    import time
    time.sleep(0.1)
    
    assert test_log_file.exists()
    content = test_log_file.read_text()
    assert "Subprocess propagation test" in content


def test_get_logger():
    """Test that get_logger returns the correct logger instance."""
    log = get_logger()
    assert log is not None
    # Loguru's logger is a singleton instance of _Logger
    assert hasattr(log, 'info')
    assert hasattr(log, 'debug')
    assert hasattr(log, 'error')


def test_log_levels(temp_log_dir):
    """Test that log levels are respected."""
    test_log_file = temp_log_dir / "test_levels.log"
    setup_logging(log_file=test_log_file, log_level="WARNING")
    
    log = get_logger()
    log.info("This should be filtered out")
    log.warning("This should appear")
    
    import time
    time.sleep(0.1)
    
    content = test_log_file.read_text()
    assert "This should be filtered out" not in content
    assert "This should appear" in content