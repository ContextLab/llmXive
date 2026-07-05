"""
Unit tests for logging infrastructure in code/utils.py.

Verifies that:
1. Logging can be configured with different levels and file paths
2. Stage logging works correctly
3. Logger instance is retrievable
"""
import os
import logging
import tempfile
from pathlib import Path
import pytest
import sys
import io

# Ensure we can import from code/
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from utils import setup_logging, get_logger, log_stage, PROJECT_ROOT

def test_setup_logging_console_only():
    """Test that setup_logging creates a console handler."""
    logger = setup_logging(log_level=logging.INFO)
    
    assert logger is not None
    assert logger.name == 'mond_pipeline'
    assert len(logger.handlers) >= 1
    
    # Verify console handler exists
    console_handler = None
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            console_handler = handler
            break
    
    assert console_handler is not None
    assert console_handler.level == logging.INFO

def test_setup_logging_with_file():
    """Test that setup_logging creates a file handler when log_file is provided."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test.log"
        
        logger = setup_logging(log_level=logging.DEBUG, log_file=str(log_path))
        
        assert log_path.exists()
        
        # Verify file handler exists
        file_handler = None
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                file_handler = handler
                break
        
        assert file_handler is not None
        assert file_handler.baseFilename == str(log_path)

def test_get_logger_returns_instance():
    """Test that get_logger returns the configured logger instance."""
    # First, ensure logging is set up
    setup_logging(log_level=logging.WARNING)
    
    logger = get_logger()
    assert logger is not None
    assert logger.name == 'mond_pipeline'

def test_log_stage_function():
    """Test that log_stage logs the correct format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "stage_test.log"
        logger = setup_logging(log_level=logging.INFO, log_file=str(log_path))
        
        # Capture the log output
        stage_name = "TEST_STAGE"
        message = "Test message"
        log_stage(stage_name, message)
        
        # Read the log file
        content = log_path.read_text()
        
        # Verify stage marker is present
        assert f"[STAGE: {stage_name}]" in content
        assert message in content

def test_log_stage_without_message():
    """Test that log_stage works without a message."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "stage_test2.log"
        logger = setup_logging(log_level=logging.INFO, log_file=str(log_path))
        
        stage_name = "NO_MSG_STAGE"
        log_stage(stage_name)
        
        content = log_path.read_text()
        assert f"[STAGE: {stage_name}]" in content

def test_logger_level_respected():
    """Test that logger respects the configured level."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "level_test.log"
        logger = setup_logging(log_level=logging.ERROR, log_file=str(log_path))
        
        # Try to log at INFO level (should be ignored)
        logger.info("This should not appear")
        
        # Log at ERROR level (should appear)
        logger.error("This should appear")
        
        content = log_path.read_text()
        assert "This should not appear" not in content
        assert "This should appear" in content

def test_logger_cleared_on_setup():
    """Test that setup_logging clears existing handlers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path1 = Path(tmpdir) / "test1.log"
        log_path2 = Path(tmpdir) / "test2.log"
        
        # First setup
        logger1 = setup_logging(log_file=str(log_path1))
        initial_count = len(logger1.handlers)
        
        # Second setup with different file
        logger2 = setup_logging(log_file=str(log_path2))
        
        # Should still have same number of handlers (console + new file)
        # Not doubled
        assert len(logger2.handlers) == initial_count

def test_project_root_constant():
    """Test that PROJECT_ROOT is defined correctly."""
    assert PROJECT_ROOT is not None
    assert isinstance(PROJECT_ROOT, Path)
    # Should be parent of code/ directory
    assert PROJECT_ROOT.name in ['code', 'PROJ-076-assessing-the-validity-of-modified-newto'] or PROJECT_ROOT.parent.name == 'code'