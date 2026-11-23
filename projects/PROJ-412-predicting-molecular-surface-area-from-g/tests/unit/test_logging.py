"""
Unit tests for the logging infrastructure.
"""

import os
import logging
import tempfile
import pytest
from pathlib import Path

# Ensure we can import the project modules
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.logging import setup_logging, get_logger
from code.utils.config import get_project_root

def test_setup_logging_console_only():
    """Test that setup_logging creates a console handler."""
    logger = setup_logging(log_level="DEBUG", log_file=None, console=True)
    assert logger is not None
    assert len(logger.handlers) >= 1
    
    # Verify at least one StreamHandler exists
    stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(stream_handlers) > 0

def test_setup_logging_with_file():
    """Test that setup_logging creates a file handler when log_file is provided."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_path = os.path.join(tmp_dir, "test.log")
        logger = setup_logging(log_level="INFO", log_file=log_path, console=False)
        
        assert len(logger.handlers) >= 1
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0
        
        # Verify file was created
        assert os.path.exists(log_path)

def test_get_logger_returns_configured_instance():
    """Test that get_logger returns the configured logger."""
    # Reset internal state for clean test
    import code.utils.logging as logging_module
    logging_module._logger = None
    
    logger = setup_logging(log_level="WARNING", console=True)
    child_logger = get_logger("test_module")
    
    assert child_logger is not None
    assert child_logger.name.startswith("llmXive")

def test_get_logger_with_name():
    """Test that get_logger creates a child logger with the correct name."""
    import code.utils.logging as logging_module
    logging_module._logger = None
    
    setup_logging(console=True)
    child_logger = get_logger("data.ingest")
    
    assert child_logger.name == "llmXive.data.ingest"

def test_log_output_format():
    """Test that log messages follow the expected format."""
    import io
    import sys
    
    # Capture stdout
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    
    test_logger = logging.getLogger("llmXive.test_format")
    test_logger.handlers.clear()
    test_logger.setLevel(logging.DEBUG)
    test_logger.addHandler(handler)
    
    test_logger.info("Test message")
    
    log_output = log_capture.getvalue()
    assert "llmXive.test_format" in log_output
    assert "INFO" in log_output
    assert "Test message" in log_output

def test_setup_logging_idempotent():
    """Test that calling setup_logging multiple times returns the same logger."""
    import code.utils.logging as logging_module
    logging_module._logger = None
    
    logger1 = setup_logging(log_level="DEBUG", console=True)
    logger2 = setup_logging(log_level="ERROR", console=True)
    
    # Should return the same instance
    assert logger1 is logger2
    # Level should remain the first set (due to singleton behavior)
    assert logger1.level == logging.DEBUG