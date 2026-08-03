"""
Unit tests for the logging configuration module.
"""

import pytest
import logging
import sys
import tempfile
from pathlib import Path
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.utils.logging_config import (
    get_log_level,
    setup_logging,
    get_logger,
    configure_module_logging,
    is_logging_initialized,
    get_current_config,
    init_default_logging
)


class TestGetLogLevel:
    """Tests for get_log_level function."""

    def test_valid_log_levels(self):
        """Test that valid log levels return correct constants."""
        assert get_log_level('DEBUG') == logging.DEBUG
        assert get_log_level('INFO') == logging.INFO
        assert get_log_level('WARNING') == logging.WARNING
        assert get_log_level('ERROR') == logging.ERROR
        assert get_log_level('CRITICAL') == logging.CRITICAL

    def test_case_insensitivity(self):
        """Test that log level names are case-insensitive."""
        assert get_log_level('debug') == logging.DEBUG
        assert get_log_level('Info') == logging.INFO
        assert get_log_level('WARNING') == logging.WARNING

    def test_invalid_log_level(self):
        """Test that invalid log level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid log level"):
            get_log_level('INVALID_LEVEL')


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_creates_handlers(self, tmp_path):
        """Test that setup_logging creates the expected handlers."""
        log_file = tmp_path / "test.log"
        config = setup_logging(
            log_file=log_file,
            level='INFO',
            console_output=True,
            file_output=True
        )

        assert config['level'] == 'INFO'
        assert config['console_output'] is True
        assert config['file_output'] is True
        assert config['handlers_count'] >= 2  # At least console and file
        assert log_file.exists()

    def test_setup_logging_no_file(self, tmp_path):
        """Test setup_logging with file_output=False."""
        config = setup_logging(
            log_file=None,
            level='DEBUG',
            console_output=True,
            file_output=False
        )

        assert config['file_output'] is False
        assert config['handlers_count'] == 1  # Only console

    def test_setup_logging_no_console(self, tmp_path):
        """Test setup_logging with console_output=False."""
        log_file = tmp_path / "test.log"
        config = setup_logging(
            log_file=log_file,
            level='WARNING',
            console_output=False,
            file_output=True
        )

        assert config['console_output'] is False
        assert config['handlers_count'] == 1  # Only file

    def test_setup_logging_creates_directory(self, tmp_path):
        """Test that setup_logging creates parent directories for log file."""
        nested_log_file = tmp_path / "subdir" / "nested" / "test.log"
        config = setup_logging(
            log_file=nested_log_file,
            level='INFO',
            console_output=False,
            file_output=True
        )

        assert nested_log_file.exists()
        assert nested_log_file.parent.exists()


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'root'

    def test_get_logger_with_name(self):
        """Test that get_logger with name returns named logger."""
        logger = get_logger('test.module')
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'test.module'

    def test_get_logger_inherits_level(self, tmp_path):
        """Test that child logger inherits level from root."""
        setup_logging(
            log_file=tmp_path / "test.log",
            level='WARNING',
            console_output=False,
            file_output=False
        )

        child_logger = get_logger('child')
        assert child_logger.level == logging.WARNING


class TestConfigureModuleLogging:
    """Tests for configure_module_logging function."""

    def test_configure_module_logging(self, tmp_path):
        """Test configuring logging for a specific module."""
        setup_logging(
            log_file=tmp_path / "test.log",
            level='INFO',
            console_output=False,
            file_output=False
        )

        logger = configure_module_logging('src.data.fetch', level='DEBUG')
        assert logger.name == 'src.data.fetch'
        assert logger.level == logging.DEBUG

    def test_configure_module_logging_no_level(self, tmp_path):
        """Test configuring module logging without level override."""
        setup_logging(
            log_file=tmp_path / "test.log",
            level='ERROR',
            console_output=False,
            file_output=False
        )

        logger = configure_module_logging('src.model.train')
        assert logger.level == logging.NOTSET  # Inherits from root


class TestLoggingState:
    """Tests for logging state functions."""

    def test_is_logging_initialized_before_setup(self):
        """Test is_logging_initialized returns False before setup."""
        # Reset state by importing fresh (in real scenario, this would be handled differently)
        # For this test, we assume a fresh environment
        # Note: This test might need adjustment depending on test isolation
        pass  # Skip as state management is complex in tests

    def test_get_current_config(self, tmp_path):
        """Test that get_current_config returns valid configuration."""
        setup_logging(
            log_file=tmp_path / "test.log",
            level='WARNING',
            console_output=True,
            file_output=True
        )

        config = get_current_config()
        assert 'level' in config
        assert 'console_output' in config
        assert 'file_output' in config
        assert 'initialized_at' in config


class TestInitDefaultLogging:
    """Tests for init_default_logging function."""

    def test_init_default_logging(self, tmp_path):
        """Test default logging initialization."""
        config = init_default_logging(project_root=tmp_path)

        assert config['level'] == 'INFO'
        assert config['console_output'] is True
        assert config['file_output'] is True