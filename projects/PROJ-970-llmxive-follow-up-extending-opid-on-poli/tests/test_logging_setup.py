import logging
import os
import tempfile
import shutil
import pytest

from utils.logging_setup import setup_logging, get_experiment_logger, LOG_DIR

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for logging tests."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_setup_logging_console_only(temp_log_dir):
    """Test logging setup with only console output."""
    setup_logging(log_level=logging.DEBUG, log_file=None)
    
    logger = logging.getLogger()
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) >= 1  # At least console handler

def test_setup_logging_with_file(temp_log_dir):
    """Test logging setup with file output."""
    log_filename = "test_experiment.log"
    setup_logging(log_level=logging.INFO, log_file=log_filename)
    
    # Check if file was created
    expected_path = os.path.join(temp_log_dir, LOG_DIR, log_filename)
    assert os.path.exists(expected_path), f"Log file not created at {expected_path}"

def test_get_experiment_logger(temp_log_dir):
    """Test retrieving a named experiment logger."""
    setup_logging(log_level=logging.INFO)
    
    logger = get_experiment_logger("my_experiment")
    assert logger.name == "my_experiment"
    assert isinstance(logger, logging.Logger)
    
    # Verify it can log
    logger.info("Test message")
    
    # Verify logger is configured (not disabled)
    assert logger.isEnabledFor(logging.INFO)
