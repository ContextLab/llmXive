"""
Unit tests for the logging infrastructure in code/utils.py.
"""
import logging
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils import setup_logging, get_logger, log_stage, get_timestamp

class TestLoggingInfrastructure:
    """Tests for logging utilities."""

    def test_setup_logging_creates_handlers(self):
        """Test that setup_logging creates both console and file handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_pipeline.log")
            logger = setup_logging(log_level=logging.INFO, log_file=log_file)
            
            # Check that logger has handlers
            assert len(logger.handlers) >= 1
            
            # Verify file handler exists and file is created
            file_handler_exists = any(
                isinstance(h, logging.FileHandler) for h in logger.handlers
            )
            assert file_handler_exists
            assert os.path.exists(log_file)

    def test_get_logger_returns_instance(self):
        """Test that get_logger returns a valid logger instance."""
        # Ensure logging is set up first
        setup_logging(log_level=logging.WARNING)
        
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_log_stage_logs_start(self, caplog):
        """Test that log_stage logs the start of a stage."""
        setup_logging(log_level=logging.INFO)
        logger = get_logger("test_stage")
        
        with caplog.at_level(logging.INFO):
            log_stage("Data Download", logger=logger, status="Starting")
            
        assert "--- Starting Data Download ---" in caplog.text

    def test_log_stage_logs_completion(self, caplog):
        """Test that log_stage logs the completion of a stage."""
        setup_logging(log_level=logging.INFO)
        logger = get_logger("test_stage")
        
        with caplog.at_level(logging.INFO):
            log_stage("Model Fitting", logger=logger, status="Completed")
            
        assert "--- Completed Model Fitting ---" in caplog.text

    def test_log_stage_default_status(self, caplog):
        """Test that log_stage defaults to 'Starting' status."""
        setup_logging(log_level=logging.INFO)
        logger = get_logger("test_stage")
        
        with caplog.at_level(logging.INFO):
            log_stage("Preprocessing", logger=logger)
            
        assert "--- Starting Preprocessing ---" in caplog.text

    def test_get_timestamp_format(self):
        """Test that get_timestamp returns a properly formatted string."""
        timestamp = get_timestamp()
        # Format should be YYYYMMDD_HHMMSS
        assert len(timestamp) == 15
        assert timestamp[4] == '0'  # Month separator check (simplified)
        assert '_' in timestamp

    def test_logger_propagation(self):
        """Test that child loggers inherit configuration from parent."""
        root_logger = setup_logging(log_level=logging.ERROR)
        child_logger = get_logger("parent.child")
        
        # Child logger should inherit the level
        assert child_logger.level == 0  # 0 means NOTSET, inherits from parent
        assert child_logger.getEffectiveLevel() == logging.ERROR