import os
import csv
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# We need to mock the paths in logging_setup to use temp dirs for testing
# However, since the module uses global constants, we will test the behavior
# by temporarily changing the CWD or mocking the file paths.
# For simplicity in this unit test, we will verify the module can be imported
# and the functions exist, then run a specific test with mocked paths.

def test_imports():
    """Verify that logging_setup exports expected names."""
    from logging_setup import setup_logger, get_logger, ExclusionTracker, initialize_logging_and_tracking
    assert callable(setup_logger)
    assert callable(get_logger)
    assert callable(ExclusionTracker)
    assert callable(initialize_logging_and_tracking)

def test_exclusion_tracker_functionality(tmp_path):
    """Test ExclusionTracker creates file and logs exclusions correctly."""
    # Temporarily override the module's path constants
    import logging_setup
    original_path = logging_setup.EXCLUSIONS_FILE_PATH
    original_log_path = logging_setup.LOG_FILE_PATH

    # Set paths to temporary directory
    test_data_dir = tmp_path / "data"
    test_logs_dir = tmp_path / "logs"
    logging_setup.DATA_DIR = test_data_dir
    logging_setup.LOGS_DIR = test_logs_dir
    logging_setup.EXCLUSIONS_FILE_PATH = test_data_dir / "exclusions.csv"
    logging_setup.LOG_FILE_PATH = test_logs_dir / "processing.log"

    try:
        # Initialize
        logger, tracker = initialize_logging_and_tracking()

        # Verify file exists
        assert tracker.file_path.exists(), "Exclusions file should be created."

        # Log exclusions
        tracker.log_exclusion("sub-999", "test_reason")
        tracker.log_exclusion("sub-998", "test_reason_2")

        # Verify content
        excluded = tracker.get_excluded_subjects()
        assert len(excluded) == 2
        assert ("sub-999", "test_reason") in excluded
        assert ("sub-998", "test_reason_2") in excluded

        # Verify log file exists
        assert logging_setup.LOG_FILE_PATH.exists(), "Log file should be created."

    finally:
        # Restore original paths
        logging_setup.EXCLUSIONS_FILE_PATH = original_path
        logging_setup.LOG_FILE_PATH = original_log_path
        logging_setup.DATA_DIR = Path("data")
        logging_setup.LOGS_DIR = Path("logs")

def test_logger_output(tmp_path):
    """Test that logger writes to the specified file."""
    import logging_setup
    original_log_path = logging_setup.LOG_FILE_PATH

    test_logs_dir = tmp_path / "logs"
    logging_setup.LOGS_DIR = test_logs_dir
    logging_setup.LOG_FILE_PATH = test_logs_dir / "processing.log"

    try:
        logger = setup_logger("test_logger_unique")
        logger.info("Test message")

        assert logging_setup.LOG_FILE_PATH.exists()
        content = logging_setup.LOG_FILE_PATH.read_text()
        assert "Test message" in content
    finally:
        logging_setup.LOG_FILE_PATH = original_log_path
        logging_setup.LOGS_DIR = Path("logs")