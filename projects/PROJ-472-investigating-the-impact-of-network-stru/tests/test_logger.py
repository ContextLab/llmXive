"""
Tests for the robust logging infrastructure.
"""
import pytest
import logging
import os
import sys
import tempfile
from pathlib import Path
import json
import time
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import (
    setup_logger,
    get_logger,
    log_exception,
    handle_exceptions,
    safe_execute,
    log_pipeline_start,
    log_pipeline_end,
    ResearchError,
    DataLoadError,
    SimulationError,
    AnalysisError,
    ConfigError
)
from utils.error_handlers import retry_on_exception, validate_path_exists, validate_file_not_empty

class TestLoggerSetup:
    def test_setup_logger_creates_file_and_console_handlers(self):
        """Test that setup_logger creates both file and console handlers."""
        logger = setup_logger("test_basic_setup")
        
        assert len(logger.handlers) >= 2
        
        has_file = False
        has_console = False
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                has_file = True
            if isinstance(handler, logging.StreamHandler):
                has_console = True
        
        assert has_file, "File handler not created"
        assert has_console, "Console handler not created"

    def test_get_logger_returns_same_instance(self):
        """Test that get_logger returns the same logger instance."""
        logger1 = get_logger("test_singleton")
        logger2 = get_logger("test_singleton")
        
        assert logger1 is logger2

    def test_log_exception_captures_traceback(self, caplog):
        """Test that log_exception captures the full traceback."""
        try:
            raise ValueError("Test error for traceback")
        except Exception as e:
            with caplog.at_level(logging.ERROR):
                log_exception(e, context="Test context")
            
            assert "Test context" in caplog.text
            assert "ValueError" in caplog.text
            assert "Test error for traceback" in caplog.text

class TestCustomExceptions:
    def test_research_error_with_context(self):
        """Test ResearchError creation with context."""
        ctx = {"key": "value", "number": 42}
        error = ResearchError("Test message", context=ctx)
        
        assert error.message == "Test message"
        assert error.context == ctx
        assert hasattr(error, "timestamp")

    def test_subclass_exceptions(self):
        """Test that specific exception subclasses work correctly."""
        data_err = DataLoadError("Data load failed", {"file": "test.csv"})
        sim_err = SimulationError("Sim failed")
        
        assert isinstance(data_err, ResearchError)
        assert isinstance(sim_err, ResearchError)
        assert data_err.context["file"] == "test.csv"

class TestContextManagers:
    def test_handle_exceptions_logs_and_suppresses(self, caplog):
        """Test that handle_exceptions logs errors and suppresses them."""
        with caplog.at_level(logging.ERROR):
            with handle_exceptions("test_suppress"):
                raise ValueError("Should be caught")
        
        assert "Should be caught" in caplog.text
        assert "ValueError" in caplog.text

    def test_handle_exceptions_reraises_when_flagged(self):
        """Test that handle_exceptions re-raises when reraise=True."""
        with pytest.raises(ValueError):
            with handle_exceptions("test_reraise", reraise=True):
                raise ValueError("Should be re-raised")

    def test_safe_execute_returns_none_on_error(self, caplog):
        """Test that safe_execute returns None on error."""
        def failing_func():
            raise RuntimeError("Always fails")
        
        with caplog.at_level(logging.ERROR):
            result = safe_execute(failing_func, logger_name="test_safe")
        
        assert result is None
        assert "Always fails" in caplog.text

    def test_safe_execute_returns_value_on_success(self):
        """Test that safe_execute returns value on success."""
        def success_func(x, y):
            return x + y
        
        result = safe_execute(success_func, 2, 3, logger_name="test_safe_success")
        assert result == 5

class TestRetryLogic:
    @retry_on_exception(exceptions=(ValueError,), max_attempts=3, delay=0.01, backoff=1)
    def flaky_function(self, fail_count: int):
        """Function that fails N times then succeeds."""
        if fail_count > 0:
            self.fail_count -= 1
            raise ValueError("Retry me")
        return "Success"

    def test_retry_succeeds_after_failures(self):
        """Test that retry decorator succeeds after failures."""
        self.fail_count = 2
        result = self.flaky_function(2)
        assert result == "Success"

    def test_retry_raises_after_max_attempts(self):
        """Test that retry raises after max attempts."""
        self.fail_count = 100
        with pytest.raises(ValueError):
            self.flaky_function(100)

class TestValidation:
    def test_validate_path_exists_passes(self, tmp_path):
        """Test validate_path_exists passes for existing path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        validate_path_exists(test_file, "test file")

    def test_validate_path_exists_raises(self, tmp_path):
        """Test validate_path_exists raises for missing path."""
        missing_path = tmp_path / "nonexistent.txt"
        
        with pytest.raises(ResearchError) as exc_info:
            validate_path_exists(missing_path, "missing file")
        
        assert "does not exist" in str(exc_info.value)

    def test_validate_file_not_empty_passes(self, tmp_path):
        """Test validate_file_not_empty passes for non-empty file."""
        test_file = tmp_path / "nonempty.txt"
        test_file.write_text("content")
        
        validate_file_not_empty(test_file, "test file")

    def test_validate_file_not_empty_raises_empty(self, tmp_path):
        """Test validate_file_not_empty raises for empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        
        with pytest.raises(ResearchError):
            validate_file_not_empty(empty_file, "empty file")

class TestPipelineLogging:
    def test_log_pipeline_start(self, caplog):
        """Test pipeline start logging."""
        with caplog.at_level(logging.INFO):
            log_pipeline_start("test_stage", {"param": "value"})
        
        assert "Pipeline Stage Started: test_stage" in caplog.text
        assert "param" in caplog.text

    def test_log_pipeline_end_success(self, caplog):
        """Test pipeline end logging for success."""
        with caplog.at_level(logging.INFO):
            log_pipeline_end("test_stage", success=True, duration=10.5)
        
        assert "Pipeline Stage Ended: test_stage [SUCCESS]" in caplog.text
        assert "Duration: 10.50s" in caplog.text

    def test_log_pipeline_end_failure(self, caplog):
        """Test pipeline end logging for failure."""
        with caplog.at_level(logging.INFO):
            log_pipeline_end("test_stage", success=False)
        
        assert "Pipeline Stage Ended: test_stage [FAILED]" in caplog.text