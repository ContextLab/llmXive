"""
Unit tests for the logging infrastructure (T005).
"""

import logging
import pytest
import tempfile
import time
from pathlib import Path
import sys
import os

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logger import (
    setup_logger,
    log_error,
    safe_execute,
    ResearchError,
    DataLoadError,
    ModelExecutionError,
    ConfigurationError,
    AnalysisError
)


class TestLoggerSetup:
    """Tests for setup_logger function."""

    def test_logger_initialization(self):
        """Verify logger is created with correct name and level."""
        logger = setup_logger(name="test_logger", level=logging.DEBUG)
        assert logger.name == "test_logger"
        assert logger.level == logging.DEBUG

    def test_console_handler_added(self):
        """Verify console handler is added when console=True."""
        logger = setup_logger(name="test_console", console=True)
        handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(handlers) > 0

    def test_file_handler_added(self):
        """Verify file handler is added when log_file is provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logger(name="test_file", log_file=log_path)
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) > 0
            assert log_path.exists()

    def test_no_duplicate_handlers(self):
        """Verify calling setup_logger twice doesn't duplicate handlers."""
        logger = setup_logger(name="test_duplicate", console=True)
        initial_count = len(logger.handlers)
        logger_again = setup_logger(name="test_duplicate", console=True)
        assert len(logger_again.handlers) == initial_count


class TestExceptionHierarchy:
    """Tests for custom exception classes."""

    def test_research_error_base(self):
        """Verify ResearchError is a subclass of Exception."""
        assert issubclass(ResearchError, Exception)

    def test_research_error_with_context(self):
        """Verify ResearchError stores context."""
        error = ResearchError("Test error", context={"key": "value"})
        assert error.message == "Test error"
        assert error.context == {"key": "value"}
        assert "Context" in str(error)

    def test_data_load_error(self):
        """Verify DataLoadError inherits from ResearchError."""
        assert issubclass(DataLoadError, ResearchError)
        error = DataLoadError("Data failed")
        assert "Data failed" in str(error)

    def test_model_execution_error(self):
        """Verify ModelExecutionError inherits from ResearchError."""
        assert issubclass(ModelExecutionError, ResearchError)

    def test_configuration_error(self):
        """Verify ConfigurationError inherits from ResearchError."""
        assert issubclass(ConfigurationError, ResearchError)

    def test_analysis_error(self):
        """Verify AnalysisError inherits from ResearchError."""
        assert issubclass(AnalysisError, ResearchError)


class TestSafeExecute:
    """Tests for safe_execute function."""

    def test_successful_execution(self):
        """Verify safe_execute returns result on success."""
        def success_func():
            return 42

        result = safe_execute(success_func)
        assert result == 42

    def test_error_with_raise(self):
        """Verify safe_execute raises on error when raise_on_error=True."""
        def fail_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            safe_execute(fail_func, raise_on_error=True)

    def test_error_with_default(self):
        """Verify safe_execute returns default on error when raise_on_error=False."""
        def fail_func():
            raise ValueError("Test error")

        result = safe_execute(fail_func, default_return=-1, raise_on_error=False)
        assert result == -1

    def test_error_logging(self):
        """Verify safe_execute logs error when logger is provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logger(name="test_safe", log_file=log_path)

            def fail_func():
                raise ValueError("Test error")

            safe_execute(fail_func, logger=logger, raise_on_error=False)

            # Check log file contains error
            content = log_path.read_text()
            assert "ValueError" in content
            assert "Test error" in content


class TestLogErrorAndRaise:
    """Tests for log_error function."""

    def test_log_error_basic(self):
        """Verify log_error writes to logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logger(name="test_log_err", log_file=log_path)

            error = ValueError("Test value error")
            log_error(logger, error, context={"step": "load"})

            content = log_path.read_text()
            assert "ValueError" in content
            assert "Test value error" in content
            assert "Context" in content

    def test_log_error_no_context(self):
        """Verify log_error works without context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logger(name="test_log_no_ctx", log_file=log_path)

            error = RuntimeError("Runtime issue")
            log_error(logger, error)

            content = log_path.read_text()
            assert "RuntimeError" in content
            assert "Runtime issue" in content


class TestRootLogger:
    """Tests for logger behavior in the root namespace."""

    def test_logger_persistence(self):
        """Verify logger state persists across calls."""
        name = "test_persist"
        logger1 = setup_logger(name=name)
        logger1.info("First message")

        logger2 = setup_logger(name=name)
        logger2.info("Second message")

        # Both should reference the same logger instance
        assert logger1 is logger2

    def test_level_override(self):
        """Verify level is respected on initial setup."""
        name = "test_level"
        logger = setup_logger(name=name, level=logging.WARNING)
        assert logger.level == logging.WARNING
        # Reset for other tests
        logging.getLogger(name).handlers.clear()
        logging.getLogger(name).setLevel(logging.NOTSET)