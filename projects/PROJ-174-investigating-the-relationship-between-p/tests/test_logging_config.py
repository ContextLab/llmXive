"""
Unit tests for the logging configuration module (T005).
"""
import os
import csv
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
code_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(code_dir))

from logging_config import (
    setup_logging, 
    initialize_quality_report, 
    write_quality_entry, 
    get_logger,
    LOG_FILE_PATH,
    QUALITY_REPORT_PATH,
    LOGGER_NAME
)
import logging

@pytest.fixture(autouse=True)
def cleanup_logs_and_reports(tmp_path):
    """
    Fixture to clean up log files and quality reports before and after tests.
    Uses a temporary directory structure to avoid polluting the real project state during tests,
    but since the module uses absolute paths relative to project root, we must be careful.
    
    Note: In a real CI environment, we might want to mock the paths or use a temp project root.
    For this test suite, we assume the test runner can handle the side effects or we clean up manually.
    However, to be safe and strictly follow "no side effects on real data", we will:
    1. Not run the actual file creation in a way that overwrites real data if possible.
    2. Or, rely on the fact that tests are run in an isolated environment.
    
    Since the module uses `Path(__file__).resolve().parent.parent` which is the project root,
    and we cannot easily change that without refactoring the module to accept paths as args,
    we will proceed by ensuring the tests clean up after themselves if they create files,
    or assume the environment is clean.
    
    Actually, the task requires verifying file creation. We will run the functions and then clean up.
    """
    # Backup existing files if they exist
    backup_log = None
    backup_report = None
    
    if LOG_FILE_PATH.exists():
        backup_log = LOG_FILE_PATH.read_bytes()
        LOG_FILE_PATH.unlink()
    
    if QUALITY_REPORT_PATH.exists():
        backup_report = QUALITY_REPORT_PATH.read_text()
        QUALITY_REPORT_PATH.unlink()
    
    yield
    
    # Restore or clean up
    if backup_log:
        LOG_FILE_PATH.write_bytes(backup_log)
    else:
        if LOG_FILE_PATH.exists():
            LOG_FILE_PATH.unlink()
            
    if backup_report:
        QUALITY_REPORT_PATH.write_text(backup_report)
    else:
        if QUALITY_REPORT_PATH.exists():
            QUALITY_REPORT_PATH.unlink()

def test_setup_logging_creates_file():
    """Test that setup_logging creates the log file."""
    # Ensure file doesn't exist before
    if LOG_FILE_PATH.exists():
        LOG_FILE_PATH.unlink()
    
    logger = setup_logging("INFO")
    logger.info("Test message")
    
    assert LOG_FILE_PATH.exists(), "Log file was not created."
    content = LOG_FILE_PATH.read_text()
    assert "Test message" in content, "Log message not found in file."

def test_initialize_quality_report_creates_file_with_headers():
    """Test that initialize_quality_report creates the CSV with correct headers."""
    # Ensure file doesn't exist
    if QUALITY_REPORT_PATH.exists():
        QUALITY_REPORT_PATH.unlink()
    
    result = initialize_quality_report()
    
    assert result is True, "Initialization should return True."
    assert QUALITY_REPORT_PATH.exists(), "Quality report file was not created."
    
    with open(QUALITY_REPORT_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        assert header == ['exclusion_type', 'count'], f"Incorrect headers: {header}"

def test_write_quality_entry():
    """Test that write_quality_entry appends rows correctly."""
    # Initialize first
    initialize_quality_report()
    
    success = write_quality_entry("blink_exclusion", 5)
    assert success is True, "Write should return True."
    
    with open(QUALITY_REPORT_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) == 2, "Expected header + 1 data row."
        assert rows[1] == ['blink_exclusion', '5'], f"Row content incorrect: {rows[1]}"

def test_get_logger():
    """Test that get_logger returns a configured logger."""
    logger = get_logger()
    assert isinstance(logger, logging.Logger), "Should return a Logger instance."
    assert logger.name == LOGGER_NAME, "Logger name mismatch."
    
    child_logger = get_logger("submodule")
    assert child_logger.name == f"{LOGGER_NAME}.submodule", "Child logger name mismatch."

def test_full_verification_flow():
    """Simulate the full verification flow as described in T005."""
    # Reset state
    if LOG_FILE_PATH.exists():
        LOG_FILE_PATH.unlink()
    if QUALITY_REPORT_PATH.exists():
        QUALITY_REPORT_PATH.unlink()

    # 1. Setup logging
    logger = setup_logging("DEBUG")
    
    # 2. Initialize report
    assert initialize_quality_report() is True
    
    # 3. Verify file creation
    assert LOG_FILE_PATH.exists()
    assert QUALITY_REPORT_PATH.exists()
    
    # 4. Verify headers
    with open(QUALITY_REPORT_PATH, 'r') as f:
        header = f.readline().strip()
        assert header == "exclusion_type,count"
    
    # 5. Write entry
    write_quality_entry("noise_filter", 10)
    
    # 6. Verify entry
    with open(QUALITY_REPORT_PATH, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 2
        assert lines[1].strip() == "noise_filter,10"
    
    # 7. Log a message
    logger.info("Verification complete")
    assert "Verification complete" in LOG_FILE_PATH.read_text()