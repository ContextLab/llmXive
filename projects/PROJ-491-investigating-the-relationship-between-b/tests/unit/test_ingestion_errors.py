import os
import sys
import logging
import pytest
from pathlib import Path
import shutil

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion_errors import (
    setup_error_logger,
    get_error_log_path,
    log_insufficient_subjects,
    fail_fast_if_insufficient_subjects,
    main
)

@pytest.fixture(autouse=True)
def clean_logs():
    """Clean up log files before and after each test."""
    log_path = Path("data/processed/ingestion_errors.log")
    if log_path.exists():
        log_path.unlink()
    yield
    if log_path.exists():
        log_path.unlink()

def test_setup_error_logger_creates_file():
    """Test that setup_error_logger creates the log file and returns a logger."""
    logger = setup_error_logger()
    log_path = get_error_log_path()
    
    assert isinstance(logger, logging.Logger)
    assert logger.name == "ingestion_errors"
    assert log_path.exists()
    assert log_path.is_file()

def test_log_insufficient_subjects_writes_message():
    """Test that log_insufficient_subjects writes the correct message to the log file."""
    setup_error_logger()
    count = 10
    required = 50
    
    log_insufficient_subjects(count, required)
    
    log_path = get_error_log_path()
    assert log_path.exists()
    
    with open(log_path, 'r') as f:
        content = f.read()
    
    assert f"Error: Insufficient valid subjects ({count} found, {required} required)." in content

def test_fail_fast_if_insufficient_subjects_raises_systemexit():
    """Test that fail_fast_if_insufficient_subjects raises SystemExit when count < required."""
    setup_error_logger()
    count = 10
    required = 50
    
    with pytest.raises(SystemExit) as excinfo:
        fail_fast_if_insufficient_subjects(count, required)
    
    assert excinfo.value.code == 1
    
    # Verify log was written
    log_path = get_error_log_path()
    with open(log_path, 'r') as f:
        content = f.read()
    assert f"Error: Insufficient valid subjects ({count} found, {required} required)." in content

def test_fail_fast_if_sufficient_subjects_does_not_raise():
    """Test that fail_fast_if_insufficient_subjects does not raise when count >= required."""
    setup_error_logger()
    count = 60
    required = 50
    
    # Should not raise
    try:
        fail_fast_if_insufficient_subjects(count, required)
    except SystemExit:
        pytest.fail("fail_fast_if_insufficient_subjects raised SystemExit unexpectedly")

def test_main_function():
    """Test the main function which demonstrates the error handling."""
    # This is more of an integration test for the main entry point
    # It should run without errors (though it will exit)
    # We capture the exit to prevent pytest from failing the whole test suite
    with pytest.raises(SystemExit):
        main()