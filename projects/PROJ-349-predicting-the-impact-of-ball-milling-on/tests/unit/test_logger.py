"""
Unit tests for the logging infrastructure (src/utils/logger.py).
"""

import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the module under test
# We need to adjust the import path based on where tests are run from
# Assuming tests/unit is at the same level as src/
import sys
from pathlib import Path

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logger import (
    get_logger,
    set_log_level,
    _get_log_level_from_env,
    _setup_logging,
    DEFAULT_LOG_LEVEL,
    LOG_LEVEL_ENV_VAR,
    LOGS_DIR
)


class TestGetLogLevelFromEnv:
    """Tests for _get_log_level_from_env function."""

    def test_default_when_env_not_set(self):
        """Should return DEFAULT_LOG_LEVEL when env var is not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove the var if it exists in the test env
            if LOG_LEVEL_ENV_VAR in os.environ:
                del os.environ[LOG_LEVEL_ENV_VAR]
            
            # Since the function reads directly, we need to ensure it's not set
            level = _get_log_level_from_env()
            assert level == DEFAULT_LOG_LEVEL

    def test_valid_levels(self):
        """Should return correct level for valid environment strings."""
        valid_levels = [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("WARN", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL),
            ("FATAL", logging.CRITICAL),
        ]

        for level_str, expected_level in valid_levels:
            with patch.dict(os.environ, {LOG_LEVEL_ENV_VAR: level_str}):
                assert _get_log_level_from_env() == expected_level

    def test_invalid_level_raises(self):
        """Should raise ValueError for invalid log level string."""
        with patch.dict(os.environ, {LOG_LEVEL_ENV_VAR: "INVALID_LEVEL"}):
            with pytest.raises(ValueError):
                _get_log_level_from_env()

    def test_case_insensitive(self):
        """Should handle case-insensitive log level strings."""
        with patch.dict(os.environ, {LOG_LEVEL_ENV_VAR: "info"}):
            assert _get_log_level_from_env() == logging.INFO
        
        with patch.dict(os.environ, {LOG_LEVEL_ENV_VAR: "Info"}):
            assert _get_log_level_from_env() == logging.INFO


class TestSetupLogging:
    """Tests for _setup_logging function."""

    def test_handlers_added(self):
        """Should add console and file handlers."""
        # Reset state for testing
        from src.utils import logger as logger_module
        logger_module._configured = False
        
        _setup_logging(logging.INFO)
        
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) >= 2  # Console + File (at least)
        
        # Verify handlers exist
        handlers = root_logger.handlers
        console_found = any(isinstance(h, logging.StreamHandler) for h in handlers)
        file_found = any(isinstance(h, logging.FileHandler) for h in handlers)
        
        assert console_found, "Console handler not found"
        assert file_found, "File handler not found"

    def test_log_level_set(self):
        """Should set the correct log level."""
        from src.utils import logger as logger_module
        logger_module._configured = False
        
        _setup_logging(logging.DEBUG)
        
        assert logging.getLogger().level == logging.DEBUG

    def test_idempotent(self):
        """Should not add duplicate handlers on subsequent calls."""
        from src.utils import logger as logger_module
        logger_module._configured = False
        
        _setup_logging(logging.INFO)
        initial_count = len(logging.getLogger().handlers)
        
        _setup_logging(logging.INFO)  # Call again
        assert len(logging.getLogger().handlers) == initial_count


class TestGetLogger:
    """Tests for get_logger function."""

    def test_returns_logger(self):
        """Should return a logging.Logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_configures_root_logger(self):
        """Should ensure root logger is configured."""
        from src.utils import logger as logger_module
        logger_module._configured = False
        
        # Root logger should not be configured initially (handlers might be empty)
        # Actually, get_logger triggers setup
        logger = get_logger("test_module")
        
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0

    def test_logger_name(self):
        """Should preserve the logger name."""
        logger = get_logger("com.example.project.module")
        assert logger.name == "com.example.project.module"


class TestSetLogLevel:
    """Tests for set_log_level function."""

    def test_updates_all_handlers(self):
        """Should update log level for all handlers."""
        from src.utils import logger as logger_module
        logger_module._configured = False
        
        _setup_logging(logging.INFO)
        
        set_log_level(logging.WARNING)
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING
        
        for handler in root_logger.handlers:
            assert handler.level == logging.WARNING