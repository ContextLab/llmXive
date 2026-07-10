"""
Unit tests for the logging infrastructure in code/utils/logging.py.
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
import pytest

# Add the project root to the path to allow imports
# Assuming tests are run from the root or with PYTHONPATH set
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils import logging as log_utils


class TestLoggingSetup:
    """Tests for the setup_logging function."""

    def test_setup_logging_creates_handlers(self, tmp_path):
        """Verify that setup_logging creates console and file handlers."""
        # Mock the get_data_path to use tmp_path
        original_get_data_path = log_utils.get_data_path
        
        def mock_get_data_path():
            return tmp_path

        log_utils.get_data_path = mock_get_data_path

        try:
            # Reset state to ensure clean test
            log_utils.reset_logging()
            
            logger = log_utils.setup_logging(
                level=logging.DEBUG,
                log_file="test.log",
                enable_console=True,
                enable_file=True
            )

            # Check logger level
            assert logger.level == logging.DEBUG

            # Check handlers
            assert len(logger.handlers) == 2  # Console + File

            # Check for StreamHandler (Console)
            stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
            assert len(stream_handlers) >= 1

            # Check for FileHandler
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) == 1
            
            # Verify file exists
            assert file_handlers[0].baseFilename.endswith("test.log")
            assert os.path.exists(file_handlers[0].baseFilename)

        finally:
            log_utils.get_data_path = original_get_data_path
            log_utils.reset_logging()

    def test_setup_logging_file_only(self, tmp_path):
        """Verify setup_logging with only file handler."""
        original_get_data_path = log_utils.get_data_path
        
        def mock_get_data_path():
            return tmp_path

        log_utils.get_data_path = mock_get_data_path

        try:
            log_utils.reset_logging()
            
            logger = log_utils.setup_logging(
                level=logging.WARNING,
                log_file="warn_only.log",
                enable_console=False,
                enable_file=True
            )

            assert len(logger.handlers) == 1
            assert isinstance(logger.handlers[0], logging.FileHandler)
            assert logger.level == logging.WARNING

        finally:
            log_utils.get_data_path = original_get_data_path
            log_utils.reset_logging()

    def test_setup_logging_console_only(self, tmp_path):
        """Verify setup_logging with only console handler."""
        original_get_data_path = log_utils.get_data_path
        
        def mock_get_data_path():
            return tmp_path

        log_utils.get_data_path = mock_get_data_path

        try:
            log_utils.reset_logging()
            
            logger = log_utils.setup_logging(
                level=logging.INFO,
                enable_console=True,
                enable_file=False
            )

            assert len(logger.handlers) == 1
            assert isinstance(logger.handlers[0], logging.StreamHandler)
            assert logger.level == logging.INFO

        finally:
            log_utils.get_data_path = original_get_data_path
            log_utils.reset_logging()

    def test_get_logger_initializes_automatically(self, tmp_path):
        """Verify that get_logger triggers setup if not initialized."""
        original_get_data_path = log_utils.get_data_path
        
        def mock_get_data_path():
            return tmp_path

        log_utils.get_data_path = mock_get_data_path

        try:
            log_utils.reset_logging()
            assert not log_utils._initialized

            child_logger = log_utils.get_logger("test_module")
            
            assert log_utils._initialized
            assert child_logger is not None
            assert "llmXive_pipeline.test_module" in child_logger.name

        finally:
            log_utils.get_data_path = original_get_data_path
            log_utils.reset_logging()

    def test_reset_logging_clears_handlers(self, tmp_path):
        """Verify that reset_logging clears all handlers."""
        original_get_data_path = log_utils.get_data_path
        
        def mock_get_data_path():
            return tmp_path

        log_utils.get_data_path = mock_get_data_path

        try:
            log_utils.reset_logging()
            log_utils.setup_logging(enable_console=True, enable_file=True)
            
            assert len(log_utils._logger.handlers) > 0
            
            log_utils.reset_logging()
            
            # Handlers should be closed and removed
            # Note: _logger might still exist but handlers list should be empty
            # or _initialized should be False
            assert not log_utils._initialized

        finally:
            log_utils.get_data_path = original_get_data_path

    def test_log_directory_creation(self, tmp_path):
        """Verify that the log directory is created if it doesn't exist."""
        # We use tmp_path as the base, so logs should be in tmp_path.parent / "logs"
        # But our mock forces logs into tmp_path itself if we adjust the logic
        # The function _ensure_log_dir uses get_data_path().parent / "logs"
        # So if get_data_path returns tmp_path, logs go to tmp_path.parent/logs
        
        original_get_data_path = log_utils.get_data_path
        
        def mock_get_data_path():
            return tmp_path

        log_utils.get_data_path = mock_get_data_path

        try:
            log_utils.reset_logging()
            
            # The directory should be created during setup
            log_utils.setup_logging(log_file="dir_test.log")
            
            expected_log_dir = tmp_path.parent / "logs"
            assert expected_log_dir.exists()

        finally:
            log_utils.get_data_path = original_get_data_path
            log_utils.reset_logging()
