"""
Unit tests for the logging configuration module.
"""
import logging
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
# Note: We need to adjust the import path based on how tests are run
# Assuming tests are run from the project root with PYTHONPATH set appropriately
try:
    from code.utils.logging_config import (
        setup_logging,
        get_logger,
        log_pipeline_start,
        log_pipeline_end,
        log_error_occurrence,
    )
except ImportError:
    # Fallback for direct execution or different path setup
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
    from utils.logging_config import (
        setup_logging,
        get_logger,
        log_pipeline_start,
        log_pipeline_end,
        log_error_occurrence,
    )


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_setup_logging_creates_file(temp_log_dir):
    """Test that setup_logging creates the log file and directory."""
    log_file = temp_log_dir / "test_pipeline.log"
    
    setup_logging(log_file=log_file)
    
    assert log_file.exists(), "Log file should be created after setup_logging"
    
    # Clean up the global logger state for next test
    logging.getLogger().handlers.clear()


def test_get_logger_returns_logger():
    """Test that get_logger returns a valid logger instance."""
    # Ensure logging is set up first
    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logging(log_file=Path(tmpdir) / "test.log")
        
        logger = get_logger("test_module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
        
        # Clean up
        logging.getLogger().handlers.clear()


def test_log_pipeline_start(capsys, temp_log_dir):
    """Test that log_pipeline_start writes to the log."""
    log_file = temp_log_dir / "test_pipeline.log"
    setup_logging(log_file=log_file)
    
    log_pipeline_start("test_pipeline", {"key": "value"})
    
    # Read the log file content
    with open(log_file, "r") as f:
        content = f.read()
    
    assert "test_pipeline" in content
    assert "starting" in content
    assert "key" in content
    
    logging.getLogger().handlers.clear()


def test_log_pipeline_end(capsys, temp_log_dir):
    """Test that log_pipeline_end writes to the log."""
    log_file = temp_log_dir / "test_pipeline.log"
    setup_logging(log_file=log_file)
    
    log_pipeline_end("test_pipeline", "SUCCESS", "All done")
    
    with open(log_file, "r") as f:
        content = f.read()
    
    assert "test_pipeline" in content
    assert "SUCCESS" in content
    assert "All done" in content
    
    logging.getLogger().handlers.clear()


def test_log_error_occurrence(capsys, temp_log_dir):
    """Test that log_error_occurrence writes to the log."""
    log_file = temp_log_dir / "test_pipeline.log"
    setup_logging(log_file=log_file)
    
    log_error_occurrence(
        "ValueError",
        "Invalid value provided",
        {"input": "test"}
    )
    
    with open(log_file, "r") as f:
        content = f.read()
    
    assert "ValueError" in content
    assert "Invalid value provided" in content
    assert "input" in content
    
    logging.getLogger().handlers.clear()
