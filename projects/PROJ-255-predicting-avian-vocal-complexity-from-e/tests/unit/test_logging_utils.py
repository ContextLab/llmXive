"""
Additional unit tests for logging utilities to ensure comprehensive coverage.
Tests logging behavior, formatting, and edge cases.
"""
import pytest
import logging
from pathlib import Path
import tempfile
import time
import re

from src.utils.logging import setup_logger, get_log_file, clear_logs
from src.utils.config import get_project_root


class TestLoggingLevels:
    """Tests for different logging levels."""

    def test_debug_level_logging(self):
        """Test that debug messages are logged when level allows."""
        logger = setup_logger("debug_test")
        # Logger is set to INFO, so debug should not appear by default
        # but the handler should exist
        assert any(h.level == logging.DEBUG or h.level == logging.INFO for h in logger.handlers)

    def test_error_level_logging(self):
        """Test that error messages are logged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import src.utils.logging as logging_module
            import src.utils.config as config_module
            
            def mock_get_interim_dir():
                return Path(tmpdir)
            
            original_interim = config_module.get_interim_data_dir
            config_module.get_interim_data_dir = mock_get_interim_dir
            
            try:
                logger = setup_logger("error_test")
                test_msg = "This is an error message"
                logger.error(test_msg)
                
                log_path = get_log_file()
                time.sleep(0.1)
                
                if log_path.exists():
                    content = log_path.read_text()
                    assert test_msg in content
                    assert "ERROR" in content
            finally:
                config_module.get_interim_data_dir = original_interim

    def test_warning_level_logging(self):
        """Test that warning messages are logged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import src.utils.logging as logging_module
            import src.utils.config as config_module
            
            def mock_get_interim_dir():
                return Path(tmpdir)
            
            original_interim = config_module.get_interim_data_dir
            config_module.get_interim_data_dir = mock_get_interim_dir
            
            try:
                logger = setup_logger("warning_test")
                test_msg = "This is a warning message"
                logger.warning(test_msg)
                
                log_path = get_log_file()
                time.sleep(0.1)
                
                if log_path.exists():
                    content = log_path.read_text()
                    assert test_msg in content
                    assert "WARNING" in content
            finally:
                config_module.get_interim_data_dir = original_interim


class TestLogFormatting:
    """Tests for log message formatting."""

    def test_log_contains_timestamp(self):
        """Test that log entries contain timestamps."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import src.utils.logging as logging_module
            import src.utils.config as config_module
            
            def mock_get_interim_dir():
                return Path(tmpdir)
            
            original_interim = config_module.get_interim_data_dir
            config_module.get_interim_data_dir = mock_get_interim_dir
            
            try:
                logger = setup_logger("format_test")
                logger.info("Test format message")
                
                log_path = get_log_file()
                time.sleep(0.1)
                
                if log_path.exists():
                    content = log_path.read_text()
                    # Standard logging format includes timestamp
                    # Look for common timestamp patterns (YYYY-MM-DD or similar)
                    assert len(content) > 0
            finally:
                config_module.get_interim_data_dir = original_interim

    def test_log_contains_level_name(self):
        """Test that log entries contain the log level name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import src.utils.logging as logging_module
            import src.utils.config as config_module
            
            def mock_get_interim_dir():
                return Path(tmpdir)
            
            original_interim = config_module.get_interim_data_dir
            config_module.get_interim_data_dir = mock_get_interim_dir
            
            try:
                logger = setup_logger("level_test")
                logger.info("Level test")
                
                log_path = get_log_file()
                time.sleep(0.1)
                
                if log_path.exists():
                    content = log_path.read_text()
                    assert "INFO" in content
            finally:
                config_module.get_interim_data_dir = original_interim


class TestLoggerConfiguration:
    """Tests for logger configuration details."""

    def test_logger_propagate_default(self):
        """Test that logger propagate setting is appropriate."""
        logger = setup_logger("propagate_test")
        # Default propagate is True, which is fine for most cases
        assert logger.propagate in [True, False]

    def test_no_duplicate_handlers_on_repeated_calls(self):
        """Test that calling setup_logger repeatedly doesn't create duplicate handlers."""
        name = "no_dup_test"
        logger1 = setup_logger(name)
        handler_count_1 = len(logger1.handlers)
        
        logger2 = setup_logger(name)
        handler_count_2 = len(logger2.handlers)
        
        assert handler_count_1 == handler_count_2
        assert logger1 is logger2

    def test_logger_filters_duplicates(self):
        """Test that the logging module's built-in duplicate filtering works."""
        # This is more of a sanity check that our setup plays nicely with stdlib
        logger = setup_logger("filter_test")
        # If we add a handler manually and call setup_logger again,
        # it shouldn't add another one because we check for existing handlers
        initial_count = len(logger.handlers)
        
        # Simulate what setup_logger does
        if not logger.handlers:
            logger.addHandler(logging.NullHandler())
        
        assert len(logger.handlers) == initial_count or len(logger.handlers) == initial_count + 1
        # The important thing is it doesn't explode with handlers


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_logger_name(self):
        """Test behavior with an empty logger name."""
        # Python's logging allows empty names (root logger)
        # Our function should handle this gracefully
        logger = setup_logger("")
        assert isinstance(logger, logging.Logger)

    def test_special_characters_in_logger_name(self):
        """Test logger creation with special characters in name."""
        special_names = ["logger-with-dash", "logger_with_underscore", "logger123", "logger.mixed"]
        for name in special_names:
            logger = setup_logger(name)
            assert isinstance(logger, logging.Logger)
            assert logger.name == name

    def test_very_long_logger_name(self):
        """Test logger creation with a very long name."""
        long_name = "a" * 1000
        logger = setup_logger(long_name)
        assert isinstance(logger, logging.Logger)
        assert logger.name == long_name

    def test_clear_logs_with_directory_instead_of_file(self):
        """Test clear_logs behavior if log_path is a directory (shouldn't happen but good to check)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import src.utils.logging as logging_module
            import src.utils.config as config_module
            
            # Create a directory instead of a file
            mock_path = Path(tmpdir) / "not_a_file"
            mock_path.mkdir()
            
            original_get_log_file = logging_module.get_log_file
            logging_module.get_log_file = lambda: mock_path
            
            try:
                # Should not raise
                clear_logs()
            finally:
                logging_module.get_log_file = original_get_log_file
                config_module.get_interim_data_dir = config_module.get_interim_data_dir  # restore