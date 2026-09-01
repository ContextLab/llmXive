import pytest
import logging
import tempfile
import os
from pathlib import Path
from code.utils.logger import setup_logging, log, log_experiment_entry

def test_setup_logging_console_only():
    """Test logging setup with console only."""
    logger = setup_logging()
    assert logger.level == logging.INFO
    assert len(logger.handlers) >= 1

def test_setup_logging_with_file(tmp_path):
    """Test logging setup with file output."""
    log_file = tmp_path / "test.log"
    logger = setup_logging(log_file)
    
    assert len(logger.handlers) == 2  # Console + File
    assert log_file.exists()

def test_log_function():
    """Test the log helper function."""
    logger = setup_logging()
    
    # Should not raise
    log("Test message", "INFO", logger)
    log("Warning message", "WARNING", logger)
    log("Error message", "ERROR", logger)

def test_log_experiment_entry(tmp_path):
    """Test experiment entry logging."""
    log_file = tmp_path / "experiment.log"
    logger = setup_logging(log_file)
    
    params = {"param1": "value1", "param2": 42}
    log_experiment_entry("exp-001", params, logger)
    
    assert log_file.exists()
    content = log_file.read_text()
    assert "exp-001" in content
    assert "param1" in content