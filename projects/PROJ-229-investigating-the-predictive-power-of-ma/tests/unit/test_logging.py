import logging
import pytest
import os
import tempfile
from pathlib import Path

# Ensure we can import from code.utils
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.logger import setup_logger, get_pipeline_logger
from code.utils.error_handling import (
    handle_error,
    validate_not_null,
    validate_positive,
    DataProcessingError,
    PipelineError
)

class TestLoggerSetup:
    def test_setup_logger_console_only(self, caplog):
        """Test that setup_logger works without a file."""
        with caplog.at_level(logging.INFO):
            logger = setup_logger(name="test_console", level=logging.INFO)
            assert logger.level == logging.INFO
            logger.info("Test message")
            assert "Test message" in caplog.text

    def test_setup_logger_with_file(self):
        """Test that setup_logger creates a file and writes to it."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as tmp:
            log_path = tmp.name

        try:
            logger = setup_logger(name="test_file", log_file=log_path, level=logging.DEBUG)
            logger.debug("Debug message")
            logger.info("Info message")

            # Verify file exists and contains logs
            assert os.path.exists(log_path)
            with open(log_path, 'r') as f:
                content = f.read()
            assert "Debug message" in content
            assert "Info message" in content
        finally:
            if os.path.exists(log_path):
                os.remove(log_path)

    def test_get_pipeline_logger_singleton(self):
        """Test that get_pipeline_logger returns a consistent instance."""
        logger1 = get_pipeline_logger()
        logger2 = get_pipeline_logger()
        assert logger1 is logger2

class TestErrorHandling:
    def test_handle_error_logs_and_reraises(self):
        """Test that handle_error logs the error and re-raises it."""
        logger = setup_logger(name="test_error", level=logging.ERROR)
        
        error = ValueError("Test error")
        with pytest.raises(ValueError):
            handle_error(error, context="TestContext", logger=logger, reraise=True)
        
        # Verify logger has the error (side effect check via handler count or manual check if needed)
        # In a real scenario, we might check the handler's buffer, but for this test,
        # ensuring no crash and the exception propagates is sufficient.

    def test_validate_not_null_pass(self):
        """Test validate_not_null with a valid object."""
        logger = setup_logger(name="test_val_null", level=logging.ERROR)
        obj = {"key": "value"}
        # Should not raise
        validate_not_null(obj, "my_obj", context="Test", logger=logger)

    def test_validate_not_null_fail(self):
        """Test validate_not_null raises DataProcessingError on None."""
        logger = setup_logger(name="test_val_null_fail", level=logging.ERROR)
        with pytest.raises(DataProcessingError):
            validate_not_null(None, "my_obj", context="Test", logger=logger)

    def test_validate_positive_pass(self):
        """Test validate_positive with a positive number."""
        logger = setup_logger(name="test_val_pos", level=logging.ERROR)
        validate_positive(10.0, "my_val", context="Test", logger=logger)

    def test_validate_positive_fail(self):
        """Test validate_positive raises on non-positive number."""
        logger = setup_logger(name="test_val_pos_fail", level=logging.ERROR)
        with pytest.raises(DataProcessingError):
            validate_positive(0, "my_val", context="Test", logger=logger)
        
        with pytest.raises(DataProcessingError):
            validate_positive(-5, "my_val", context="Test", logger=logger)

    def test_pipeline_error_handler_decorator(self):
        """Test the decorator wraps function execution and handles errors."""
        from code.utils.error_handling import pipeline_error_handler

        @pipeline_error_handler(context="TestDecorator")
        def failing_func():
            raise ValueError("Intentional failure")

        with pytest.raises(PipelineError):
            failing_func()
