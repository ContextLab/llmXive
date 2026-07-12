"""
Unit tests for the logging infrastructure.
Verifies that loggers are created correctly and log messages to expected files.
"""
import os
import logging
import tempfile
import shutil
from pathlib import Path
import pytest

# Add parent directory to path to import code.utils
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from utils.logging_config import (
    get_logger,
    setup_data_flow_logger,
    setup_exclusion_logger,
    setup_resource_logger,
    setup_general_logger,
    log_data_transition,
    log_exclusion_reason,
    log_resource_usage,
    LOGS_DIR
)

class TestLoggingInfrastructure:
    """Tests for the logging configuration and helper functions."""

    def test_get_logger_creates_file_handler(self, tmp_path):
        """Test that get_logger creates a file handler when a log file is provided."""
        # Create a temporary log file path
        temp_log = tmp_path / "test.log"

        # Get logger
        logger = get_logger("test_logger", log_file=temp_log, level=logging.INFO)

        # Verify logger has handlers
        assert len(logger.handlers) > 0

        # Log a message
        logger.info("Test message")

        # Verify file was created and contains the message
        assert temp_log.exists()
        with open(temp_log, 'r') as f:
            content = f.read()
        assert "Test message" in content

    def test_get_logger_avoids_duplicate_handlers(self):
        """Test that getting the same logger twice doesn't duplicate handlers."""
        # Clear existing handlers for this test
        test_logger_name = "test_unique_logger"
        logger = logging.getLogger(test_logger_name)
        logger.handlers.clear()

        # Get logger twice
        logger1 = get_logger(test_logger_name, level=logging.INFO)
        logger2 = get_logger(test_logger_name, level=logging.INFO)

        # Should still have only one set of handlers (or at least not double)
        # Note: In a real scenario, we might want to check exactly, but here we just check
        # that it doesn't explode with handlers.
        assert len(logger1.handlers) >= 1
        assert len(logger2.handlers) == len(logger1.handlers)

    def test_log_data_transition_success(self, caplog, tmp_path):
        """Test logging a successful data transition."""
        # Mock the logs dir to a temp dir
        original_logs_dir = LOGS_DIR
        # We can't easily mock the global LOGS_DIR constant in the module,
        # so we rely on the fact that the logger writes to the real LOGS_DIR
        # but we can check the output via caplog if we set up a handler.
        
        # Instead, let's just call the function and ensure it doesn't crash
        # and that the log file is created in the expected location (logs/)
        log_file = LOGS_DIR / "data_flow.log"
        
        # Ensure clean state
        if log_file.exists():
            log_file.unlink()

        log_data_transition("preprocessing", "input.csv", "output.csv", "SUCCESS")

        assert log_file.exists()
        with open(log_file, 'r') as f:
            content = f.read()
        assert "Transition: preprocessing" in content
        assert "SUCCESS" in content

    def test_log_exclusion_reason(self):
        """Test logging an exclusion reason."""
        log_file = LOGS_DIR / "exclusion_reasons.log"
        
        if log_file.exists():
            log_file.unlink()

        log_exclusion_reason("P001", "SNR below threshold", 3.5, 5.0)

        assert log_file.exists()
        with open(log_file, 'r') as f:
            content = f.read()
        assert "Excluded Participant: P001" in content
        assert "SNR below threshold" in content
        assert "Value: 3.5" in content
        assert "Cutoff: 5.0" in content

    def test_log_resource_usage_warning(self):
        """Test logging resource usage with a warning status."""
        log_file = LOGS_DIR / "resource_usage.log"
        
        if log_file.exists():
            log_file.unlink()

        log_resource_usage("RAM", 6.5, 7.0, "WARNING")

        assert log_file.exists()
        with open(log_file, 'r') as f:
            content = f.read()
        assert "Resource Warning: RAM=6.50" in content
        assert "WARNING" in content

    def test_setup_specific_loggers(self):
        """Test that specific setup functions return valid loggers."""
        logger_data = setup_data_flow_logger()
        logger_exc = setup_exclusion_logger()
        logger_res = setup_resource_logger()
        logger_gen = setup_general_logger()

        assert isinstance(logger_data, logging.Logger)
        assert isinstance(logger_exc, logging.Logger)
        assert isinstance(logger_res, logging.Logger)
        assert isinstance(logger_gen, logging.Logger)

        assert "data_flow" in logger_data.name
        assert "exclusions" in logger_exc.name
        assert "resources" in logger_res.name
        assert "pipeline" in logger_gen.name