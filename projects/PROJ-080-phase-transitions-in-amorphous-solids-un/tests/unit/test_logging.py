"""
Unit tests for the logging infrastructure (T004).
"""
import os
import logging
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the module under test
from code.logging_config import (
    configure_logging,
    get_logger,
    log_indeterminate_warning,
    log_multi_yield_event,
    log_data_fetch_failure,
    log_synthetic_fallback_active
)


class TestLoggingInfrastructure:
    """Tests for logging configuration and specific warning functions."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory for log files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_configure_logging_creates_file(self, temp_log_dir):
        """Test that configure_logging creates the log file and directory."""
        log_file_name = "test_pipeline.log"
        logger = configure_logging(log_dir=temp_log_dir, log_file=log_file_name)
        
        log_path = Path(temp_log_dir) / log_file_name
        assert log_path.exists(), "Log file should be created after configuration"
        
        # Verify logger has handlers
        assert len(logger.handlers) >= 1, "Logger should have at least one handler"

    def test_get_logger_returns_configured_instance(self, temp_log_dir):
        """Test that get_logger returns the configured logger."""
        configure_logging(log_dir=temp_log_dir)
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "llmXive.pipeline"

    def test_get_child_logger(self, temp_log_dir):
        """Test that get_logger can return a child logger."""
        configure_logging(log_dir=temp_log_dir)
        child_logger = get_logger("preprocess")
        assert child_logger.name == "llmXive.pipeline.preprocess"
        assert child_logger.parent.name == "llmXive.pipeline"

    def test_log_indeterminate_warning(self, temp_log_dir, caplog):
        """Test that log_indeterminate_warning writes to the log file."""
        log_file_name = "test_indeterminate.log"
        configure_logging(log_dir=temp_log_dir, log_file=log_file_name)
        
        traj_id = "traj_001"
        reason = "No sharp stress peak detected"
        
        # Capture log output
        with caplog.at_level(logging.WARNING):
            log_indeterminate_warning(traj_id, reason)
        
        assert f"INDETERMINATE TRAJECTORY: ID={traj_id}" in caplog.text
        assert reason in caplog.text

        # Verify file content
        log_path = Path(temp_log_dir) / log_file_name
        assert log_path.exists()
        content = log_path.read_text()
        assert f"INDETERMINATE TRAJECTORY: ID={traj_id}" in content

    def test_log_multi_yield_event(self, temp_log_dir, caplog):
        """Test logging of multiple yield events."""
        log_file_name = "test_multi_yield.log"
        configure_logging(log_dir=temp_log_dir, log_file=log_file_name)
        
        traj_id = "traj_002"
        indices = [100, 500, 900]
        
        with caplog.at_level(logging.WARNING):
            log_multi_yield_event(traj_id, indices)
        
        assert f"MULTIPLE YIELD EVENTS: ID={traj_id}" in caplog.text
        assert str(indices) in caplog.text

    def test_log_data_fetch_failure(self, temp_log_dir, caplog):
        """Test logging of data fetch failures."""
        log_file_name = "test_fetch_fail.log"
        configure_logging(log_dir=temp_log_dir, log_file=log_file_name)
        
        source = "hf:materials-science/amorphous-silicon"
        error_msg = "Connection timeout"
        
        with caplog.at_level(logging.ERROR):
            log_data_fetch_failure(source, error_msg)
        
        assert f"DATA FETCH FAILURE: Source={source}" in caplog.text
        assert error_msg in caplog.text

    def test_log_synthetic_fallback_active(self, temp_log_dir, caplog):
        """Test logging of synthetic fallback activation."""
        log_file_name = "test_fallback.log"
        configure_logging(log_dir=temp_log_dir, log_file=log_file_name)
        
        with caplog.at_level(logging.WARNING):
            log_synthetic_fallback_active()
        
        assert "SYNTHETIC FALLBACK ACTIVE" in caplog.text

    def test_log_levels_are_respected(self, temp_log_dir):
        """Test that log levels are correctly set."""
        configure_logging(log_dir=temp_log_dir)
        logger = get_logger()
        
        # File handler should be DEBUG
        file_handler = None
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                file_handler = handler
                break
        
        assert file_handler is not None
        assert file_handler.level == logging.DEBUG
