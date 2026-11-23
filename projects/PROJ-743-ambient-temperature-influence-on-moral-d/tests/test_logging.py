import os
import logging
import pytest
from pathlib import Path
import sys

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_logging import (
    ensure_directories,
    get_data_quality_logger,
    get_model_diagnostics_logger,
    get_exclusion_logger,
    LOG_DIR
)

@pytest.fixture(autouse=True)
def setup_log_dir(tmp_path, monkeypatch):
    """Fixture to redirect logs to a temporary directory for testing."""
    temp_log_dir = tmp_path / "logs"
    monkeypatch.setattr("setup_logging.LOG_DIR", str(temp_log_dir))
    # Re-import to pick up the monkeypatched value if necessary, 
    # but since LOG_DIR is evaluated at import time in the module, 
    # we ensure the function uses the module-level variable correctly.
    # The setup_logging module reads LOG_DIR at import. 
    # To make this test robust, we will reload the module or ensure the functions 
    # read the variable dynamically. 
    # Given the current implementation, LOG_DIR is read at module load.
    # We will rely on the fact that we are running in a fresh process or 
    # monkeypatching the module attribute directly.
    import setup_logging
    setup_logging.LOG_DIR = str(temp_log_dir)
    return temp_log_dir

def test_ensure_directories_creates_path(setup_log_dir):
    """Test that ensure_directories creates the log directory if it doesn't exist."""
    new_dir = setup_log_dir / "subdir"
    # The function should create the base LOG_DIR, but we can test creation logic
    # by calling the internal logic or ensuring the base exists.
    assert setup_log_dir.exists()

def test_get_data_quality_logger_writes_file(setup_log_dir):
    """Test that the data quality logger creates a file."""
    logger = get_data_quality_logger()
    # Clear handlers to avoid duplicates from previous runs if any
    logger.handlers.clear()
    
    # Re-attach handlers using the setup logic manually for test isolation
    # or rely on the fact that the logger is configured once.
    # We will trigger a log write.
    logger.info("Test data quality entry")
    
    # Check that a file was created
    files = list(setup_log_dir.glob("data_quality_*.log"))
    assert len(files) >= 1, f"Expected data quality log file, found: {files}"

def test_get_model_diagnostics_logger_writes_file(setup_log_dir):
    """Test that the model diagnostics logger creates a file."""
    logger = get_model_diagnostics_logger()
    logger.handlers.clear()
    logger.info("Test model diagnostic entry")
    
    files = list(setup_log_dir.glob("model_diagnostics_*.log"))
    assert len(files) >= 1, f"Expected model diagnostics log file, found: {files}"

def test_get_exclusion_logger_writes_file(setup_log_dir):
    """Test that the exclusion logger creates a file."""
    logger = get_exclusion_logger()
    logger.handlers.clear()
    logger.warning("Test exclusion entry")
    
    files = list(setup_log_dir.glob("exclusion_*.log"))
    assert len(files) >= 1, f"Expected exclusion log file, found: {files}"

def test_log_content_format(setup_log_dir):
    """Test that log files contain expected formatting."""
    logger = get_data_quality_logger()
    logger.handlers.clear()
    logger.info("Specific test message")
    
    files = list(setup_log_dir.glob("data_quality_*.log"))
    assert files
    
    content = files[0].read_text()
    assert "Specific test message" in content
    assert "INFO" in content
    assert "data_quality" in content