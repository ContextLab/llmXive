"""
Unit tests for the logging configuration (T010).

These tests verify that:
1. The logger is configured correctly.
2. Specific events (insufficient data, convergence failure) are logged.
3. Log files are created in the expected location.
"""
import os
import logging
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to temporarily override the LOG_DIR to test in isolation
import src.lib.logging_config as logging_config_module

@pytest.fixture
def temp_logs_dir(tmp_path):
    """Fixture to create a temporary logs directory for testing."""
    original_log_dir = logging_config_module.LOG_DIR
    logging_config_module.LOG_DIR = tmp_path
    logging_config_module.LOG_FILE = tmp_path / "pipeline.log"
    
    # Re-configure logging with the new directory
    logging_config_module.configure_logging()
    
    yield tmp_path
    
    # Restore original
    logging_config_module.LOG_DIR = original_log_dir
    logging_config_module.LOG_FILE = original_log_dir / "pipeline.log"

def test_logger_configuration(temp_logs_dir):
    """Test that the logger is configured with the correct format and handlers."""
    logger = logging.getLogger(__name__)
    handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    
    # Should have a RotatingFileHandler
    assert len(handlers) > 0
    handler = handlers[0]
    assert isinstance(handler, logging.handlers.RotatingFileHandler)
    assert handler.maxBytes == 10 * 1024 * 1024
    assert handler.backupCount == 5

def test_log_insufficient_data(temp_logs_dir):
    """Test that log_insufficient_data writes the correct message."""
    from src.lib.logging_config import log_insufficient_data
    
    log_insufficient_data("Zonotrichia leucophrys", "45.0_-122.0", "count < 5")
    
    log_file = logging_config_module.LOG_FILE
    assert log_file.exists()
    
    content = log_file.read_text()
    assert "Insufficient data" in content
    assert "Zonotrichia leucophrys" in content
    assert "45.0_-122.0" in content
    assert "count < 5" in content
    assert "WARNING" in content

def test_log_convergence_failure(temp_logs_dir):
    """Test that log_convergence_failure writes the correct message."""
    from src.lib.logging_config import log_convergence_failure
    
    log_convergence_failure("gamm_species_A_2020", "singular fit")
    
    log_file = logging_config_module.LOG_FILE
    assert log_file.exists()
    
    content = log_file.read_text()
    assert "Convergence failure" in content
    assert "gamm_species_A_2020" in content
    assert "singular fit" in content
    assert "ERROR" in content

def test_file_creation(temp_logs_dir):
    """Test that the log file is created in the logs directory."""
    # Trigger a log write to ensure file creation
    from src.lib.logging_config import log_insufficient_data
    log_insufficient_data("TestSpecies", "0.0_0.0", "test")
    
    assert logging_config_module.LOG_FILE.exists()
    assert logging_config_module.LOG_DIR.exists()