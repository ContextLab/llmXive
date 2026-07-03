"""
Tests for logging_config.py (Task T005).

Verifies:
1. Log file is created at code/logs/preprocess.log
2. Quality report is created at results/quality_report.csv
3. Quality report contains correct headers
4. Logger instance is functional
"""
import os
import csv
import logging
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from logging_config import (
    setup_logging,
    initialize_quality_report,
    get_quality_report_path,
    get_log_file_path,
    LOG_FILE,
    QUALITY_REPORT_FILE
)

class TestLoggingConfig:
    """Test suite for logging infrastructure."""

    def test_log_file_creation(self):
        """Test that log file is created."""
        # Ensure directory exists
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize logger
        logger = setup_logging(logging.INFO)
        
        # Log a message to ensure file is written
        logger.info("Test log message")
        
        # Assert file exists
        assert LOG_FILE.exists(), f"Log file {LOG_FILE} was not created."

    def test_quality_report_creation(self):
        """Test that quality report file is created."""
        # Ensure directory exists
        QUALITY_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize report
        initialize_quality_report()
        
        # Assert file exists
        assert QUALITY_REPORT_FILE.exists(), f"Quality report {QUALITY_REPORT_FILE} was not created."

    def test_quality_report_headers(self):
        """Test that quality report has correct headers."""
        initialize_quality_report()
        
        with open(QUALITY_REPORT_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            
        expected_headers = ["exclusion_type", "count"]
        assert headers == expected_headers, f"Expected {expected_headers}, got {headers}"

    def test_logger_functionality(self):
        """Test that logger can write messages."""
        logger = setup_logging(logging.DEBUG)
        
        # Clear handlers to avoid duplicates in test runs
        logger.handlers.clear()
        logger.setLevel(logging.DEBUG)
        
        file_handler = logging.FileHandler(LOG_FILE, mode='a')
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(file_handler)
        
        test_message = "Test functionality message"
        logger.info(test_message)
        
        # Read file and verify message
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        assert test_message in content, f"Message '{test_message}' not found in log file."

    def test_get_paths(self):
        """Test path getter functions."""
        assert get_log_file_path() == LOG_FILE
        assert get_quality_report_path() == QUALITY_REPORT_FILE

    def test_module_side_effects(self):
        """Test that importing the module initializes the quality report."""
        # The module initializes on import, so the file should exist
        assert QUALITY_REPORT_FILE.exists(), "Quality report should exist after import."

    def test_append_to_quality_report(self):
        """Test appending data to quality report."""
        import logging_config
        
        # Reset the file to ensure clean state
        if QUALITY_REPORT_FILE.exists():
            QUALITY_REPORT_FILE.unlink()
        
        logging_config.initialize_quality_report()
        
        # Append a test entry
        with open(QUALITY_REPORT_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["blink_exclusion", "15"])
        
        # Verify entry
        with open(QUALITY_REPORT_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        assert len(rows) == 2, "Expected 2 rows (header + 1 entry)"
        assert rows[1] == ["blink_exclusion", "15"], f"Unexpected row: {rows[1]}"