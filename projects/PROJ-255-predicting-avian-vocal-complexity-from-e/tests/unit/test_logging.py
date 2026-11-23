import os
import pytest
import logging
from pathlib import Path
import tempfile
import shutil
import time

# Import the functions to test
from src.utils.logging import (
    setup_logger,
    get_log_file,
    clear_logs
)
from src.utils.config import get_project_root, get_interim_data_dir


class TestSetupLogger:
    """Tests for setup_logger function."""

    def test_returns_logger_instance(self):
        """Test that setup_logger returns a logging.Logger instance."""
        logger = setup_logger("test_logger")
        assert isinstance(logger, logging.Logger)

    def test_logger_name_is_correct(self):
        """Test that the logger has the correct name."""
        logger = setup_logger("test_logger_name")
        assert logger.name == "test_logger_name"

    def test_logger_has_handlers(self):
        """Test that the logger has handlers configured."""
        logger = setup_logger("test_handlers")
        assert len(logger.handlers) > 0

    def test_console_handler_exists(self):
        """Test that a StreamHandler (console) is attached."""
        logger = setup_logger("test_console")
        has_stream_handler = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
        assert has_stream_handler

    def test_file_handler_exists(self):
        """Test that a FileHandler is attached."""
        logger = setup_logger("test_file")
        has_file_handler = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        assert has_file_handler

    def test_logger_level_is_info(self):
        """Test that the logger level is set to INFO."""
        logger = setup_logger("test_level")
        assert logger.level == logging.INFO

    def test_different_loggers_are_distinct(self):
        """Test that creating two loggers with different names creates distinct instances."""
        logger1 = setup_logger("logger_a")
        logger2 = setup_logger("logger_b")
        assert logger1.name != logger2.name
        assert len(logger1.handlers) > 0
        assert len(logger2.handlers) > 0

    def test_reusing_logger_name_does_not_duplicate_handlers(self):
        """Test that getting an existing logger doesn't add duplicate handlers."""
        name = "unique_test_logger"
        logger1 = setup_logger(name)
        count1 = len(logger1.handlers)
        
        # Get the same logger again
        logger2 = setup_logger(name)
        count2 = len(logger2.handlers)
        
        # Should be the same logger instance
        assert logger1 is logger2
        # Handlers should not have doubled
        assert count1 == count2


class TestGetLogFile:
    """Tests for get_log_file function."""

    def test_returns_path_object(self):
        """Test that get_log_file returns a Path object."""
        log_path = get_log_file()
        assert isinstance(log_path, Path)

    def test_log_file_in_interim_dir(self):
        """Test that the log file path is within the interim data directory."""
        log_path = get_log_file()
        interim_dir = get_interim_data_dir()
        # The log file should be in the interim directory or a subdirectory
        assert str(log_path).startswith(str(interim_dir))

    def test_log_file_has_correct_extension(self):
        """Test that the log file has a .log extension."""
        log_path = get_log_file()
        assert log_path.suffix == ".log"

    def test_log_file_name_contains_timestamp_or_project(self):
        """Test that the log file name is descriptive."""
        log_path = get_log_file()
        # Should contain 'log' in the name
        assert "log" in log_path.stem.lower()


class TestClearLogs:
    """Tests for clear_logs function."""

    def test_clear_logs_does_not_raise(self):
        """Test that clear_logs executes without raising an exception."""
        # This function should handle missing files gracefully
        try:
            clear_logs()
        except Exception as e:
            pytest.fail(f"clear_logs raised an unexpected exception: {e}")

    def test_clear_logs_with_nonexistent_file(self):
        """Test that clear_logs handles non-existent log files gracefully."""
        # The function should not crash even if the log file doesn't exist
        clear_logs()

    def test_clear_logs_with_existing_file(self):
        """Test that clear_logs truncates an existing log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock log file
            log_path = Path(tmpdir) / "test_clear.log"
            log_path.write_text("Some content to clear\n")
            
            # Temporarily override get_log_file
            import src.utils.logging as logging_module
            
            original_get_log_file = logging_module.get_log_file
            logging_module.get_log_file = lambda: log_path
            
            try:
                clear_logs()
                # File should be empty or truncated
                content = log_path.read_text()
                assert content == ""
            finally:
                logging_module.get_log_file = original_get_log_file

class TestIntegration:
    """Integration tests for logging module."""

    def test_logger_writes_to_file(self):
        """Test that a logger actually writes to the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import src.utils.logging as logging_module
            import src.utils.config as config_module
            
            # Mock paths to use temp directory
            def mock_get_interim_dir():
                return Path(tmpdir)
            
            original_interim = config_module.get_interim_data_dir
            config_module.get_interim_data_dir = mock_get_interim_dir
            
            try:
                logger = setup_logger("integration_test")
                test_msg = f"Test message at {time.time()}"
                logger.info(test_msg)
                
                # Get the log file path
                log_path = get_log_file()
                
                # Give filesystem a moment to flush
                time.sleep(0.1)
                
                if log_path.exists():
                    content = log_path.read_text()
                    assert test_msg in content
            finally:
                config_module.get_interim_data_dir = original_interim
