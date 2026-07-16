import os
import logging
from pathlib import Path
import pytest
from setup_logging import setup_logging, get_data_quality_logger, get_model_diagnostics_logger, LOG_DIR

@pytest.fixture(autouse=True)
def ensure_log_dir():
    """Ensure the log directory exists before each test."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup: Remove generated log files after test to keep results clean
    for file in LOG_DIR.glob("*.log"):
        file.unlink()

def test_setup_logging_creates_directory():
    """Verify that setup_logging ensures the results/logs directory exists."""
    setup_logging()
    assert LOG_DIR.exists(), "Log directory should be created by setup_logging"
    assert LOG_DIR.is_dir(), "Log path should be a directory"

def test_get_data_quality_logger_creates_file():
    """Verify that the data quality logger creates a log file upon first use."""
    logger = get_data_quality_logger("test_dq")
    logger.info("Test message for data quality logger")
    
    # Check that at least one log file exists
    log_files = list(LOG_DIR.glob("data_quality_*.log"))
    assert len(log_files) > 0, "Data quality log file should be created"
    
    # Verify the file is not empty
    log_file = log_files[0]
    assert log_file.stat().st_size > 0, "Log file should contain the test message"

def test_get_model_diagnostics_logger_creates_file():
    """Verify that the model diagnostics logger creates a log file upon first use."""
    logger = get_model_diagnostics_logger("test_md")
    logger.info("Test message for model diagnostics logger")
    
    # Check that at least one log file exists
    log_files = list(LOG_DIR.glob("model_diagnostics_*.log"))
    assert len(log_files) > 0, "Model diagnostics log file should be created"
    
    # Verify the file is not empty
    log_file = log_files[0]
    assert log_file.stat().st_size > 0, "Log file should contain the test message"

def test_loggers_write_correct_format():
    """Verify that log entries contain expected timestamp and level."""
    dq_logger = get_data_quality_logger("test_format")
    msg = "Format test message"
    dq_logger.warning(msg)
    
    log_files = list(LOG_DIR.glob("data_quality_*.log"))
    assert len(log_files) > 0
    
    with open(log_files[0], 'r') as f:
        content = f.read()
    
    assert "WARNING" in content, "Log should contain the level"
    assert msg in content, "Log should contain the message"
    # Basic check for timestamp format (YYYY-MM-DD)
    assert len(content) > 20, "Log entry should include a timestamp"