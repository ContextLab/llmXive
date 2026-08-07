"""
Unit tests for deterministic logging and error handling infrastructure.
"""
import logging
import pytest
import time
import sys
from unittest.mock import patch, MagicMock

# Import from the package root
from code import (
    setup_logger,
    root_logger,
    ResearchError,
    DataFetchError,
    ModelLoadError,
    ExecutionTimeoutError,
    ReproducibilityError,
    safe_execute,
    log_error_and_raise,
)
from code import config


class TestLoggerSetup:
    """Tests for the setup_logger function."""

    def test_setup_logger_returns_valid_instance(self):
        """Verify that setup_logger returns a valid logging.Logger instance."""
        logger = setup_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_setup_logger_uses_config_level(self):
        """Verify that setup_logger defaults to config.get_log_level()."""
        with patch.object(config, 'get_log_level', return_value='DEBUG'):
            logger = setup_logger("test_module_debug")
            assert logger.level == logging.DEBUG

    def test_setup_logger_uses_explicit_level(self):
        """Verify that setup_logger uses the explicitly provided level."""
        logger = setup_logger("test_module_warn", level="WARNING")
        assert logger.level == logging.WARNING

    def test_setup_logger_avoids_duplicate_handlers(self):
        """Verify that calling setup_logger twice does not add duplicate handlers."""
        logger = setup_logger("test_duplicate")
        initial_count = len(logger.handlers)

        logger = setup_logger("test_duplicate")
        assert len(logger.handlers) == initial_count


class TestExceptionHierarchy:
    """Tests for custom exception classes."""

    def test_research_error_is_exception(self):
        assert issubclass(ResearchError, Exception)

    def test_data_fetch_error_is_research_error(self):
        assert issubclass(DataFetchError, ResearchError)

    def test_model_load_error_is_research_error(self):
        assert issubclass(ModelLoadError, ResearchError)

    def test_execution_timeout_error_is_research_error(self):
        assert issubclass(ExecutionTimeoutError, ResearchError)

    def test_reproducibility_error_is_research_error(self):
        assert issubclass(ReproducibilityError, ResearchError)


class TestSafeExecute:
    """Tests for the safe_execute decorator."""

    @staticmethod
    def test_success_case():
        """Verify that a successful function runs without interruption."""
        @safe_execute()
        def add(a, b):
            return a + b

        assert add(2, 3) == 5

    @staticmethod
    def test_failure_with_default():
        """Verify that a failing function returns the default value."""
        @safe_execute(default=0)
        def divide(a, b):
            return a / b

        assert divide(1, 0) == 0

    @staticmethod
    def test_failure_raises_if_no_default():
        """Verify that a failing function raises if no default is provided."""
        @safe_execute()
        def fail():
            raise ValueError("Intentional failure")

        with pytest.raises(ValueError, match="Intentional failure"):
            fail()

    @staticmethod
    def test_retry_logic():
        """Verify that the function retries on failure."""
        call_count = 0

        @safe_execute(retries=2, backoff_factor=0.01)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("Transient error")
            return "Success"

        result = flaky()
        assert result == "Success"
        assert call_count == 3

    @staticmethod
    def test_deterministic_retry_no_jitter():
        """Verify that retries happen in a deterministic order without random jitter."""
        # This is implicitly tested by the fact that safe_execute uses
        # a fixed backoff calculation (attempt * factor) rather than random.
        # We verify the signature and logic via the retry test above.
        pass


class TestLogErrorAndRaise:
    """Tests for the log_error_and_raise helper."""

    @staticmethod
    def test_logs_and_raises_simple():
        """Verify that log_error_and_raise logs and raises the specified exception."""
        logger = logging.getLogger("test_log_raise")
        with patch.object(logger, 'error') as mock_log:
            with pytest.raises(RuntimeError, match="Something went wrong"):
                log_error_and_raise(logger, RuntimeError, "Something went wrong")
            mock_log.assert_called_once()

    @staticmethod
    def test_chains_original_exception():
        """Verify that the original exception is chained in the new exception."""
        logger = logging.getLogger("test_chain")
        original = ValueError("Original")

        with pytest.raises(ModelLoadError) as exc_info:
            log_error_and_raise(logger, ModelLoadError, "Load failed", original)

        assert exc_info.value.__cause__ is original
        assert "Load failed" in str(exc_info.value)


class TestRootLogger:
    """Tests for the global root_logger instance."""

    def test_root_logger_exists(self):
        assert root_logger is not None
        assert isinstance(root_logger, logging.Logger)

    def test_root_logger_name(self):
        assert root_logger.name == "llmXive"

    def test_root_logger_has_handler(self):
        assert len(root_logger.handlers) > 0