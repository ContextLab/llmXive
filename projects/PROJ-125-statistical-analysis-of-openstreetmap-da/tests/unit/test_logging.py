"""
Unit tests for logging infrastructure.
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
import pytest

# Ensure code/ is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logging import setup_logging, get_logger, log_module_imports, log_error_context

class TestLoggingInfrastructure:
    def test_setup_logging_console_handler(self):
        """Test that setup_logging creates a console handler."""
        logger = setup_logging("test_console")
        assert len(logger.handlers) >= 1
        has_console = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
        assert has_console, "Console handler not found"

    def test_setup_logging_file_handler(self):
        """Test that setup_logging creates a file handler when log_file is provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logging("test_file", log_file=log_path)
            
            assert log_path.exists(), "Log file was not created"
            has_file = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
            assert has_file, "File handler not found"

    def test_get_logger_reuses_existing(self):
        """Test that get_logger returns the existing logger without adding handlers."""
        name = "test_reuse"
        logger1 = setup_logging(name)
        initial_handler_count = len(logger1.handlers)
        
        logger2 = get_logger(name)
        assert logger1 is logger2
        assert len(logger2.handlers) == initial_handler_count

    def test_log_module_imports(self, caplog):
        """Test that log_module_imports writes the correct message."""
        with caplog.at_level(logging.INFO):
            logger = setup_logging("test_imports")
            log_module_imports(logger, "test_module")
            
        assert "Module imported: test_module" in caplog.text

    def test_log_error_context(self, caplog):
        """Test that log_error_context writes error with context."""
        with caplog.at_level(logging.ERROR):
            logger = setup_logging("test_error")
            try:
                raise ValueError("Test error")
            except Exception as e:
                log_error_context(logger, e, "Test context")
            
        assert "Test context" in caplog.text
        assert "Test error" in caplog.text

    def test_logger_level_configuration(self):
        """Test that logger level is set correctly."""
        logger = setup_logging("test_level", level=logging.DEBUG)
        assert logger.level == logging.DEBUG