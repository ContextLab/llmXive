"""
Tests for the logging configuration and quality report initialization.
"""
import os
import csv
import tempfile
import shutil
import pytest
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from logging_config import (
    setup_logging,
    init_quality_report,
    append_quality_report,
    get_logger,
    QUALITY_REPORT_HEADERS,
    LOGS_DIR,
    RESULTS_DIR
)


class TestLoggingConfig:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Create temporary directories for testing to avoid polluting the real project."""
        # We will test against the actual paths in the project, but we ensure
        # directories exist. The main script clears the log file, which is fine.
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        yield
        # Cleanup is optional in CI, but we don't delete the actual log files 
        # to allow manual inspection if needed.
    
    def test_setup_logging_creates_file(self):
        """Verify that setup_logging creates the log file."""
        # Clear existing handlers to ensure clean test
        import logging
        root_logger = logging.getLogger()
        if root_logger.handlers:
            root_logger.handlers.clear()
        
        log_path = LOGS_DIR / "test_preprocess.log"
        logger = setup_logging(log_file=log_path, level=logging.DEBUG)
        
        assert log_path.exists(), "Log file was not created."
        
        # Check content
        with open(log_path, 'r') as f:
            content = f.read()
            assert "INFO" in content or "DEBUG" in content, "Log file is empty or missing expected levels."
    
    def test_init_quality_report_creates_headers(self):
        """Verify that init_quality_report creates the CSV with correct headers."""
        report_path = RESULTS_DIR / "test_quality_report.csv"
        
        # Remove if exists to ensure fresh creation
        if report_path.exists():
            report_path.unlink()
        
        result_path = init_quality_report(report_path)
        
        assert result_path.exists(), "Quality report file was not created."
        
        with open(result_path, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert headers == QUALITY_REPORT_HEADERS, f"Headers mismatch. Expected {QUALITY_REPORT_HEADERS}, got {headers}"
    
    def test_append_quality_report(self):
        """Verify that append_quality_report adds rows correctly."""
        report_path = RESULTS_DIR / "test_append_report.csv"
        
        # Initialize first
        init_quality_report(report_path)
        
        # Append a record
        append_quality_report("blink_exclusion", 15, report_path)
        append_quality_report("missing_data", 3, report_path)
        
        with open(report_path, 'r') as f:
            reader = list(csv.reader(f))
            # Check header
            assert reader[0] == QUALITY_REPORT_HEADERS
            # Check rows
            assert len(reader) == 3, f"Expected 3 rows (header + 2 data), got {len(reader)}"
            assert reader[1] == ["blink_exclusion", "15"]
            assert reader[2] == ["missing_data", "3"]
    
    def test_get_logger(self):
        """Verify that get_logger returns a valid logger."""
        logger = get_logger("test_module")
        assert logger is not None
        assert logger.name == "test_module"
        # Should be able to log without error
        logger.info("Test message")

    def test_t005_verification_script_simulation(self):
        """
        Simulate the verification logic described in T005:
        'verify by asserting file creation and column presence'.
        """
        test_log = LOGS_DIR / "verify_test.log"
        test_report = RESULTS_DIR / "verify_report.csv"
        
        # Run setup
        setup_logging(test_log)
        init_quality_report(test_report)
        
        # Assert file creation
        assert test_log.exists(), "Log file missing"
        assert test_report.exists(), "Report file missing"
        
        # Assert column presence
        with open(test_report, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert headers == QUALITY_REPORT_HEADERS, "Columns missing or incorrect"