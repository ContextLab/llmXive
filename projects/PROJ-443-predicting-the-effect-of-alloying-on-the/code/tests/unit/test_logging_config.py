"""
Unit tests for the logging configuration module.

Tests cover log level conversion, logging setup, logger retrieval,
and configuration state management.
"""
import pytest
import logging
import sys
import tempfile
from pathlib import Path
import os

# Import the module under test
from src.utils.logging_config import (
    get_log_level,
    setup_logging,
    get_logger,
    configure_module_logging,
    is_logging_initialized,
    get_current_config,
    init_default_logging,
    LOG_LEVELS,
    _logging_initialized,
    _current_config,
)

class TestGetLogLevel:
    """Tests for the get_log_level function."""

    def test_valid_levels(self):
        """Test that valid log level strings return correct constants."""
        assert get_log_level("DEBUG") == logging.DEBUG
        assert get_log_level("INFO") == logging.INFO
        assert get_log_level("WARNING") == logging.WARNING
        assert get_log_level("ERROR") == logging.ERROR
        assert get_log_level("CRITICAL") == logging.CRITICAL

    def test_case_insensitive(self):
        """Test that log level strings are case-insensitive."""
        assert get_log_level("debug") == logging.DEBUG
        assert get_log_level("Info") == logging.INFO
        assert get_log_level("WARNING") == logging.WARNING

    def test_invalid_level(self):
        """Test that invalid log level strings raise ValueError."""
        with pytest.raises(ValueError, match="Invalid log level"):
            get_log_level("INVALID")
        
        with pytest.raises(ValueError):
            get_log_level("")

class TestSetupLogging:
    """Tests for the setup_logging function."""

    def test_basic_setup(self):
        """Test basic logging setup with default parameters."""
        # Reset state before test
        from src.utils import logging_config
        logging_config._logging_initialized = False
        logging_config._current_config = None
        
        setup_logging(level="INFO")
        
        assert is_logging_initialized()
        config = get_current_config()
        assert config["level"] == "INFO"
        assert config["console_output"] is True
        assert config["file_output"] is False

    def test_file_output(self):
        """Test logging setup with file output."""
        from src.utils import logging_config
        logging_config._logging_initialized = False
        logging_config._current_config = None
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            setup_logging(
                level="DEBUG",
                log_file=log_file,
                file_output=True
            )
            
            assert is_logging_initialized()
            config = get_current_config()
            assert config["file_output"] is True
            assert log_file.exists()

    def test_custom_format(self):
        """Test logging setup with custom format."""
        from src.utils import logging_config
        logging_config._logging_initialized = False
        logging_config._current_config = None
        
        custom_format = "%(levelname)s: %(message)s"
        setup_logging(format_str=custom_format)
        
        config = get_current_config()
        assert config["format"] == custom_format

    def test_no_console_output(self):
        """Test logging setup without console output."""
        from src.utils import logging_config
        logging_config._logging_initialized = False
        logging_config._current_config = None
        
        setup_logging(console_output=False, file_output=False)
        
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) == 0

class TestGetLogger:
    """Tests for the get_logger function."""

    def test_get_root_logger(self):
        """Test getting the root logger."""
        logger = get_logger()
        assert logger.name == "root"

    def test_get_named_logger(self):
        """Test getting a named logger."""
        logger = get_logger("test_module")
        assert logger.name == "test_module"

    def test_logger_reuse(self):
        """Test that the same logger is returned on multiple calls."""
        logger1 = get_logger("reused_module")
        logger2 = get_logger("reused_module")
        assert logger1 is logger2

    def test_auto_initialization(self):
        """Test that get_logger initializes logging if not already done."""
        from src.utils import logging_config
        logging_config._logging_initialized = False
        logging_config._current_config = None
        
        logger = get_logger("auto_init")
        
        assert is_logging_initialized()

class TestConfigureModuleLogging:
    """Tests for the configure_module_logging function."""

    def test_module_logger_creation(self):
        """Test creating a module-specific logger."""
        logger = configure_module_logging("test.module")
        assert logger.name == "test.module"

    def test_level_override(self):
        """Test setting a specific log level for a module."""
        logger = configure_module_logging("level_test", level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_propagate_false(self):
        """Test disabling propagation for a module logger."""
        logger = configure_module_logging("no_propagate", propagate=False)
        assert logger.propagate is False

class TestLoggingState:
    """Tests for logging state management functions."""

    def test_is_logging_initialized(self):
        """Test the is_logging_initialized function."""
        from src.utils import logging_config
        logging_config._logging_initialized = False
        
        assert is_logging_initialized() is False
        
        setup_logging()
        assert is_logging_initialized() is True

    def test_get_current_config(self):
        """Test getting the current configuration."""
        from src.utils import logging_config
        logging_config._logging_initialized = False
        logging_config._current_config = None
        
        assert get_current_config() is None
        
        setup_logging(level="WARNING")
        config = get_current_config()
        assert config is not None
        assert "level" in config
        assert config["level"] == "WARNING"

    def test_config_is_copy(self):
        """Test that get_current_config returns a copy, not the original."""
        setup_logging(level="INFO")
        config1 = get_current_config()
        config1["test"] = "modified"
        config2 = get_current_config()
        assert "test" not in config2

class TestInitDefaultLogging:
    """Tests for the init_default_logging function."""

    def test_initializes_once(self):
        """Test that init_default_logging only initializes once."""
        from src.utils import logging_config
        logging_config._logging_initialized = False
        logging_config._current_config = None
        
        init_default_logging()
        first_config = get_current_config()
        
        init_default_logging()  # Call again
        second_config = get_current_config()
        
        # Should be the same config object
        assert first_config["timestamp"] == second_config["timestamp"]

    def test_default_level_is_info(self):
        """Test that default initialization uses INFO level."""
        from src.utils import logging_config
        logging_config._logging_initialized = False
        logging_config._current_config = None
        
        init_default_logging()
        config = get_current_config()
        assert config["level"] == "INFO"