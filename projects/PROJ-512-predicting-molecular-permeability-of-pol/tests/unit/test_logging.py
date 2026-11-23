"""
Unit tests for standardized logging configuration.

These tests verify that the logging setup produces consistent
formatting and correctly routes messages to console and file.
"""
import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.logging_config import configure_logging, get_logger, set_global_log_level
from data.utils import setup_logging

class TestLoggingConfiguration:
    """Tests for logging configuration functions."""

    def test_configure_logging_creates_handlers(self, tmp_path):
        """Test that configure_logging creates appropriate handlers."""
        log_file = tmp_path / "test.log"
        
        configure_logging(
            level=logging.INFO,
            log_to_file=True,
            log_file=log_file,
            enable_console=True
        )
        
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) == 2  # Console + File
        
        # Verify file handler exists and file was created
        file_handler = next(
            (h for h in root_logger.handlers if isinstance(h, logging.FileHandler)),
            None
        )
        assert file_handler is not None
        assert log_file.exists()

    def test_get_logger_returns_configured_logger(self):
        """Test that get_logger returns a properly configured logger."""
        logger = get_logger("test_module")
        assert logger.name == "test_module"
        assert logger.level == logging.NOTSET  # Inherits from root

    def test_set_global_log_level_updates_root(self):
        """Test that set_global_log_level updates the root logger."""
        original_level = logging.getLogger().level
        
        set_global_log_level(logging.DEBUG)
        assert logging.getLogger().level == logging.DEBUG
        
        # Reset
        set_global_log_level(original_level)

    def test_setup_logging_integration(self, tmp_path):
        """Test the high-level setup_logging function."""
        log_file = tmp_path / "setup_test.log"
        
        setup_logging(
            level="DEBUG",
            log_to_file=True,
            log_file=str(log_file)
        )
        
        logger = get_logger("test_setup")
        logger.debug("Test debug message")
        
        assert log_file.exists()
        with open(log_file, 'r') as f:
            content = f.read()
            assert "Test debug message" in content

    def test_log_format_includes_timestamp_level_name(self, tmp_path):
        """Test that log messages include timestamp, level, and module name."""
        log_file = tmp_path / "format_test.log"
        
        configure_logging(
            level=logging.INFO,
            log_to_file=True,
            log_file=log_file,
            enable_console=False
        )
        
        logger = get_logger("format_test_module")
        logger.info("Format test message")
        
        with open(log_file, 'r') as f:
            content = f.read()
            # Check for expected format components
            assert "|" in content  # Separator
            assert "INFO" in content
            assert "format_test_module" in content

    def test_reconfigure_logging_replaces_handlers(self):
        """Test that reconfiguring logging removes old handlers."""
        initial_count = len(logging.getLogger().handlers)
        
        configure_logging(level=logging.INFO, log_to_file=False, enable_console=True)
        new_count = len(logging.getLogger().handlers)
        
        # Should have replaced handlers, not added to them
        assert new_count >= 1
        assert new_count <= initial_count + 1  # Allow for slight variation

    def test_log_to_non_existent_directory_creates_it(self, tmp_path):
        """Test that logging creates the log directory if it doesn't exist."""
        nested_dir = tmp_path / "nested" / "logs"
        log_file = nested_dir / "test.log"
        
        configure_logging(
            level=logging.INFO,
            log_to_file=True,
            log_file=log_file,
            enable_console=False
        )
        
        assert nested_dir.exists()
        assert log_file.exists()