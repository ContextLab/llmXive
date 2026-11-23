"""
Tests for the base logging infrastructure in code/__init__.py.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the project root to the path so we can import code
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code import (
    get_project_root,
    get_log_path,
    setup_logger,
    get_default_logger
)
import logging

def test_get_project_root():
    """Test that get_project_root returns the expected path."""
    root = get_project_root()
    assert root.exists(), "Project root directory should exist"
    # The project root should be the parent of the 'code' directory
    assert (root / "code").exists(), "Project root should contain 'code' directory"
    assert (root / "tests").exists(), "Project root should contain 'tests' directory"

def test_get_log_path_creates_directory():
    """Test that get_log_path creates the logs directory if it doesn't exist."""
    # Temporarily remove the logs directory to test creation
    log_dir = get_project_root() / "data" / "results" / "logs"
    if log_dir.exists():
        shutil.rmtree(log_dir)
    
    # Call get_log_path - should create the directory
    result_path = get_log_path()
    
    assert result_path == log_dir, "get_log_path should return the correct path"
    assert result_path.exists(), "get_log_path should create the logs directory"
    assert result_path.is_dir(), "The log path should be a directory"

def test_setup_logger_console_only():
    """Test logger setup with console output only."""
    logger = setup_logger("test_console_only", log_file=None, level=logging.INFO)
    
    assert logger.name == "test_console_only"
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1  # Only console handler
    
    # Check that the handler is a StreamHandler
    assert isinstance(logger.handlers[0], logging.StreamHandler)

def test_setup_logger_with_file():
    """Test logger setup with both console and file output."""
    log_file = "test_logger.log"
    logger = setup_logger("test_with_file", log_file=log_file, level=logging.DEBUG)
    
    assert logger.name == "test_with_file"
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 2  # Console + file handler
    
    # Check handlers
    handlers = logger.handlers
    console_handler = next(h for h in handlers if isinstance(h, logging.StreamHandler))
    file_handler = next(h for h in handlers if isinstance(h, logging.FileHandler))
    
    assert console_handler.level == logging.DEBUG
    assert file_handler.level == logging.DEBUG
    
    # Verify file was created
    log_dir = get_log_path()
    file_path = log_dir / log_file
    assert file_path.exists(), "Log file should be created"
    
    # Cleanup
    file_path.unlink()

def test_get_default_logger():
    """Test the convenience function for getting a default logger."""
    logger = get_default_logger()
    
    assert logger.name == "llmXive"
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 2  # Console + file handler (pipeline.log)
    
    # Verify pipeline.log was created
    log_dir = get_log_path()
    pipeline_log = log_dir / "pipeline.log"
    assert pipeline_log.exists(), "pipeline.log should be created"

def test_logger_handler_idempotency():
    """Test that calling setup_logger multiple times doesn't duplicate handlers."""
    logger_name = "test_idempotency"
    logger1 = setup_logger(logger_name, log_file="idempotency_test.log", level=logging.INFO)
    initial_handler_count = len(logger1.handlers)
    
    # Call again with same name
    logger2 = setup_logger(logger_name, log_file="idempotency_test.log", level=logging.INFO)
    
    assert len(logger2.handlers) == initial_handler_count, "Handler count should not increase on re-call"
    
    # Cleanup
    log_dir = get_log_path()
    (log_dir / "idempotency_test.log").unlink()

if __name__ == "__main__":
    test_get_project_root()
    print("✓ test_get_project_root passed")
    
    test_get_log_path_creates_directory()
    print("✓ test_get_log_path_creates_directory passed")
    
    test_setup_logger_console_only()
    print("✓ test_setup_logger_console_only passed")
    
    test_setup_logger_with_file()
    print("✓ test_setup_logger_with_file passed")
    
    test_get_default_logger()
    print("✓ test_get_default_logger passed")
    
    test_logger_handler_idempotency()
    print("✓ test_logger_handler_idempotency passed")
    
    print("\nAll logging infrastructure tests passed!")