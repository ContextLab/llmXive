"""
Tests for the logger module (code/src/utils/logger.py).
"""
import os
import time
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure code/ is in the path for imports if running via pytest directly
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.utils import logger
from code.src.utils.timeout_wrapper import setup_timeout_logging


@pytest.fixture
def clean_logs():
    """Fixture to ensure logs directory exists and is clean for testing."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    # Remove existing log files to ensure fresh state
    for f in logs_dir.glob("*.log"):
        f.unlink()
    yield
    # Cleanup after test if desired, or leave for inspection


def test_get_logger_returns_valid_logger(clean_logs):
    """Test that get_logger returns a configured logger instance."""
    # Reset the internal state to force re-initialization
    logger._logger = None
    logger._start_time = None

    log_instance = logger.get_logger()
    assert isinstance(log_instance, logging.Logger)
    assert log_instance.level == logging.INFO

    # Check handlers
    assert len(log_instance.handlers) == 2  # File and Console

    # Check child logger
    child = logger.get_logger("test.child")
    assert child.name == "code.test.child" or child.name == "test.child" # Depends on root name


def test_start_runtime_tracking(clean_logs):
    """Test that start_runtime_tracking sets the start time."""
    logger._start_time = None
    logger._logger = None # Force re-init

    logger.start_runtime_tracking()
    assert logger._start_time is not None
    assert logger._start_time > 0


def test_stop_runtime_tracking_logs_duration(clean_logs, caplog):
    """Test that stop_runtime_tracking calculates and logs duration."""
    logger._logger = None
    logger.start_runtime_tracking()
    initial_start = logger._start_time

    # Mock time.time to control duration
    with patch('code.src.utils.logger.time') as mock_time:
        mock_time.time.side_effect = [initial_start + 10.0, initial_start + 10.0] # Start, End

        # Capture logs
        with caplog.at_level(logging.INFO):
            logger.stop_runtime_tracking()

        # Check that duration was logged
        assert "Total runtime" in caplog.text
        # Since we mocked time, we expect exactly 10 seconds
        assert "10.00" in caplog.text or "10 seconds" in caplog.text

    assert logger._start_time is None


def test_setup_pipeline_logging(clean_logs):
    """Test the full setup function."""
    logger._logger = None
    logger._start_time = None

    log_instance = logger.setup_pipeline_logging()

    assert log_instance is not None
    assert logger._start_time is not None
    # Check that timeout log file was created (side effect of setup_timeout_logging)
    assert Path("logs/timeout.log").exists()


def test_log_runtime_stats(clean_logs, caplog):
    """Test that log_runtime_stats reports elapsed time."""
    logger._logger = None
    logger.start_runtime_tracking()
    initial_start = logger._start_time

    with patch('code.src.utils.logger.time') as mock_time:
        mock_time.time.return_value = initial_start + 30.0

        with caplog.at_level(logging.INFO):
            logger.log_runtime_stats()

        assert "Current runtime checkpoint" in caplog.text
        assert "30.00" in caplog.text or "30 seconds" in caplog.text


def test_main_function(clean_logs, capsys):
    """Test the main entry point of the logger module."""
    logger._logger = None
    logger._start_time = None

    # Patch time to make the test fast
    with patch('code.src.utils.logger.time') as mock_time:
        mock_time.time.side_effect = [0, 1, 1] # Start, Sleep(1), End

        logger.main()

        captured = capsys.readouterr()
        assert "Logging test completed" in captured.out

        # Check log file content
        log_file = Path("logs/pipeline.log")
        assert log_file.exists()
        content = log_file.read_text()
        assert "Pipeline execution started" in content
        assert "Pipeline execution ended" in content
        assert "Total runtime" in content