import os
import logging
from pathlib import Path
import pytest

from logging_setup import setup_logger, get_logger, ExclusionTracker, initialize_logging_and_tracking, LOG_FILE, EXCLUSIONS_FILE

class TestLoggingSetup:
    def test_setup_logger_creates_file(self):
        """Test that the logger creates the log file."""
        logger = setup_logger()
        assert LOG_FILE.exists()

    def test_logger_writes_messages(self):
        """Test that the logger writes to the file."""
        logger = get_logger()
        test_msg = "Test message for T018b verification"
        logger.info(test_msg)
        
        # Force flush
        for handler in logger.handlers:
            handler.flush()
        
        with open(LOG_FILE, 'r') as f:
            content = f.read()
        
        assert test_msg in content

    def test_exclusion_tracker_creates_file(self):
        """Test that ExclusionTracker creates the CSV file."""
        ExclusionTracker.ensure_exclusions_file_exists()
        assert EXCLUSIONS_FILE.exists()

    def test_exclusion_tracker_logs_entry(self):
        """Test that ExclusionTracker logs an exclusion."""
        ExclusionTracker.log_exclusion("SUBJ_TEST", "test_reason")
        
        with open(EXCLUSIONS_FILE, 'r') as f:
            content = f.read()
        
        assert "SUBJ_TEST" in content
        assert "test_reason" in content

    def test_initialize_logging_and_tracking(self):
        """Test the initialization function."""
        initialize_logging_and_tracking()
        assert LOG_FILE.exists()
        assert EXCLUSIONS_FILE.exists()
