"""
Tests for logging infrastructure (T005).

These tests verify that:
1. The log file is created at code/logs/preprocess.log
2. The quality report is created at results/quality_report.csv
3. The quality report has the correct headers
"""
import os
import csv
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from logging_config import (
    setup_logging,
    initialize_quality_report,
    write_quality_entry,
    LOG_FILE_PATH,
    QUALITY_REPORT_PATH,
    PROJECT_ROOT
)


class TestLoggingInfrastructure:
    """Test suite for logging infrastructure."""

    def setup_method(self):
        """Setup before each test."""
        # Ensure directories exist
        (PROJECT_ROOT / "logs").mkdir(parents=True, exist_ok=True)
        (PROJECT_ROOT / "results").mkdir(parents=True, exist_ok=True)
        
        # Remove existing files for clean test
        if LOG_FILE_PATH.exists():
            LOG_FILE_PATH.unlink()
        if QUALITY_REPORT_PATH.exists():
            QUALITY_REPORT_PATH.unlink()

    def teardown_method(self):
        """Cleanup after each test."""
        # Optional: clean up test artifacts
        pass

    def test_log_file_creation(self):
        """Test that setup_logging creates the log file."""
        # Call setup_logging
        logger = setup_logging("DEBUG")
        
        # Verify log file exists
        assert LOG_FILE_PATH.exists(), f"Log file not created at {LOG_FILE_PATH}"
        
        # Verify log file is not empty after logging
        logger.debug("Test message")
        assert LOG_FILE_PATH.stat().st_size > 0, "Log file is empty"

    def test_quality_report_creation(self):
        """Test that initialize_quality_report creates the CSV with headers."""
        # Initialize quality report
        initialize_quality_report()
        
        # Verify file exists
        assert QUALITY_REPORT_PATH.exists(), f"Quality report not created at {QUALITY_REPORT_PATH}"
        
        # Verify headers
        with open(QUALITY_REPORT_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            
            assert headers is not None, "Quality report is empty"
            assert headers == ["exclusion_type", "count"], f"Unexpected headers: {headers}"

    def test_quality_report_headers_persistence(self):
        """Test that existing quality report headers are preserved or corrected."""
        # Create a file with wrong headers
        QUALITY_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(QUALITY_REPORT_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["wrong_header", "another_wrong"])
        
        # Initialize should fix headers
        initialize_quality_report()
        
        # Verify headers are correct
        with open(QUALITY_REPORT_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            assert headers == ["exclusion_type", "count"], f"Headers not corrected: {headers}"

    def test_write_quality_entry(self):
        """Test that write_quality_entry appends entries correctly."""
        # Initialize report
        initialize_quality_report()
        
        # Write entries
        write_quality_entry("blink", 5)
        write_quality_entry("missing_data", 3)
        
        # Verify content
        with open(QUALITY_REPORT_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            assert len(rows) == 3, f"Expected 3 rows, got {len(rows)}"  # header + 2 entries
            assert rows[0] == ["exclusion_type", "count"]
            assert rows[1] == ["blink", "5"]
            assert rows[2] == ["missing_data", "3"]

    def test_log_file_path_is_absolute(self):
        """Test that LOG_FILE_PATH is an absolute path under project root."""
        assert LOG_FILE_PATH.is_absolute(), "Log file path should be absolute"
        assert str(LOG_FILE_PATH).startswith(str(PROJECT_ROOT)), \
            f"Log file path should be under project root: {PROJECT_ROOT}"

    def test_quality_report_path_is_absolute(self):
        """Test that QUALITY_REPORT_PATH is an absolute path under project root."""
        assert QUALITY_REPORT_PATH.is_absolute(), "Quality report path should be absolute"
        assert str(QUALITY_REPORT_PATH).startswith(str(PROJECT_ROOT)), \
            f"Quality report path should be under project root: {PROJECT_ROOT}"

    def test_get_logger(self):
        """Test that get_logger returns a configured logger."""
        from logging_config import get_logger
        
        logger = get_logger("test_logger")
        
        assert logger.name == "test_logger"
        assert len(logger.handlers) > 0, "Logger should have handlers"

    def test_logging_to_file(self):
        """Test that log messages are written to the file."""
        # Setup logging
        logger = setup_logging("DEBUG")
        test_logger = get_logger("test_module")
        
        # Write test messages
        test_logger.debug("Debug message")
        test_logger.info("Info message")
        test_logger.warning("Warning message")
        
        # Read file and verify content
        assert LOG_FILE_PATH.exists()
        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            
        assert "Debug message" in content
        assert "Info message" in content
        assert "Warning message" in content