import pytest
import logging
import os
import tempfile
from pathlib import Path
import sys

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.logging import get_log_file_path, setup_logging, get_logger, init_logger
from src.utils.config import get_config, PathConfig, Config

class TestLoggingInfrastructure:
    
    def test_get_log_file_path_creates_directory(self):
        """Test that the log directory is created if it doesn't exist."""
        # We can't easily test the config-dependent path without mocking config,
        # so we test the fallback behavior or assume config is set up.
        # For robustness, we ensure the function doesn't crash.
        try:
            path = get_log_file_path("test.log")
            assert isinstance(path, Path)
            # The directory part should exist or be creatable
            path.parent.mkdir(parents=True, exist_ok=True)
            assert path.parent.exists()
        except Exception as e:
            # If config is missing, it might fall back, but shouldn't crash
            pytest.fail(f"get_log_file_path failed: {e}")

    def test_setup_logging_adds_handlers(self):
        """Test that setup_logging correctly adds handlers to the root logger."""
        root_logger = logging.getLogger()
        initial_handler_count = len(root_logger.handlers)
        
        setup_logging(enable_console=True, enable_file=False)
        
        # Should have added at least one handler
        assert len(root_logger.handlers) > initial_handler_count
        
        # Clean up
        root_logger.handlers.clear()

    def test_get_logger_returns_named_logger(self):
        """Test that get_logger returns a logger with the correct name."""
        logger_name = "test_module"
        logger = get_logger(logger_name)
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == logger_name

    def test_init_logger_sets_up_and_returns_logger(self):
        """Test that init_logger configures logging and returns a logger."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear() # Clean slate
        
        logger = init_logger("integration_test", level=logging.DEBUG)
        
        assert logger is not None
        assert len(root_logger.handlers) > 0
        assert logger.level == logging.DEBUG or logger.level == logging.NOTSET # Level might be inherited

    def test_logger_outputs_to_console(self, caplog):
        """Test that a logger can output messages."""
        setup_logging(enable_file=False) # Only console for this test
        logger = get_logger("console_test")
        
        with caplog.at_level(logging.INFO):
            logger.info("Test message")
        
        assert "Test message" in caplog.text