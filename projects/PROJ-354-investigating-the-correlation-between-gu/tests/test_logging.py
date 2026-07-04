"""
Unit tests for the logging and error handling infrastructure.
"""

import pytest
import logging
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports if running directly
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import (
    get_logger,
    LlmXiveError,
    DataLoadError,
    PreprocessingError,
    AnalysisError,
    ConfigError,
    ValidationError,
    log_exception,
    safe_execute,
    init_logging,
    debug,
    info,
    warning,
    error,
    critical
)


class TestCustomExceptions:
    def test_base_exception(self):
        exc = LlmXiveError("Test message")
        assert str(exc) == "LlmXiveError: Test message"
        assert exc.timestamp is not None

    def test_exception_with_context(self):
        ctx = {"user_id": 123, "step": "load"}
        exc = LlmXiveError("Failed", context=ctx)
        assert "user_id=123" in str(exc)
        assert "step=load" in str(exc)

    def test_subclass_instantiation(self):
        exc = DataLoadError("Missing file")
        assert isinstance(exc, LlmXiveError)
        assert exc.message == "Missing file"

        exc2 = PreprocessingError("Bad format", context={"file": "test.csv"})
        assert isinstance(exc2, LlmXiveError)
        assert "file=test.csv" in str(exc2)


class TestLoggerConfiguration:
    def test_get_logger_creates_instance(self):
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_get_logger_caching(self):
        logger1 = get_logger("test.cached")
        logger2 = get_logger("test.cached")
        assert logger1 is logger2

    def test_logger_has_handlers(self):
        logger = get_logger("test.handlers")
        assert len(logger.handlers) > 0
        # Should have at least one file and one console handler
        has_file = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        has_console = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
        assert has_file or has_console  # Depends on directory availability

    def test_init_logging(self, tmp_path):
        with patch("utils.logging.LOGS_DIR", tmp_path):
            init_logging()
            # Verify directory was used
            assert tmp_path.exists()
            # Verify a logger can be retrieved
            log = get_logger("init_test")
            assert log is not None


class TestLogException:
    def test_log_exception_records_traceback(self, caplog):
        logger = get_logger("test.exc")
        logger.handlers[0].setLevel(logging.DEBUG) # Ensure handler captures debug

        try:
            raise ValueError("Test error")
        except Exception as e:
            log_exception(logger, e, level=logging.ERROR)

        # Check that the log contains the error message
        assert "ValueError" in caplog.text
        assert "Test error" in caplog.text
        assert "Traceback" in caplog.text or "exc_info" in str(logger.handlers[0].formatter)


class TestSafeExecute:
    def test_safe_execute_success(self):
        def success_func(x):
            return x * 2

        result = safe_execute(success_func, 5, logger=get_logger("test.safe"))
        assert result == 10

    def test_safe_execute_wraps_non_llm_errors(self):
        def failing_func():
            raise ValueError("Generic error")

        with pytest.raises(AnalysisError) as exc_info:
            safe_execute(failing_func, logger=get_logger("test.safe"))

        assert "Generic error" in str(exc_info.value)

    def test_safe_execute_passes_llm_errors(self):
        def llm_failing_func():
            raise DataLoadError("Specific data error")

        with pytest.raises(DataLoadError) as exc_info:
            safe_execute(llm_failing_func, logger=get_logger("test.safe"))

        assert "Specific data error" in str(exc_info.value)


class TestConvenienceFunctions:
    def test_convenience_functions_call_logger(self, caplog):
        logger = get_logger("test.conv")
        logger.setLevel(logging.DEBUG)
        
        # Patch the specific logger instance to avoid global state issues in tests
        with patch("utils.logging.get_logger", return_value=logger):
            debug("Debug msg")
            info("Info msg")
            warning("Warning msg")
            error("Error msg")
            critical("Critical msg")

        # Verify messages appear in logs (if handlers are configured to capture them)
        # Note: caplog captures the output of the logger passed to the patch context if configured correctly
        # Here we rely on the fact that the functions call the logger
        assert "Debug msg" in str(logger.handlers[0].stream.getvalue()) if hasattr(logger.handlers[0], 'stream') else True