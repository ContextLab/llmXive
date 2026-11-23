"""
Tests for the logging and error handling utilities.
"""

import logging
import os
import tempfile
import pytest
from src.utils.logger import (
    get_logger,
    setup_logging,
    ResearchPipelineError,
    DataLoadingError,
    ConfigurationError,
    ValidationError,
    AnalysisError
)

def test_custom_exception_hierarchy():
    """Test that custom exceptions inherit correctly and store context."""
    base_error = ResearchPipelineError("Base error", context={"key": "value"})
    assert base_error.message == "Base error"
    assert base_error.context == {"key": "value"}
    assert hasattr(base_error, "timestamp")

    data_error = DataLoadingError("Data load failed", context={"file": "test.csv"})
    assert isinstance(data_error, ResearchPipelineError)
    assert data_error.message == "Data load failed"

def test_setup_logging_console_only():
    """Test logging setup with only console output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "test.log")
        # Ensure no file is created
        setup_logging(log_level=logging.INFO, log_file=None, enable_console=True)
        logger = get_logger("test_console")
        logger.info("Console test message")
        # Verify root has handlers
        assert len(logging.getLogger().handlers) > 0

def test_setup_logging_with_file():
    """Test logging setup with file output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "test.log")
        setup_logging(log_level=logging.INFO, log_file=log_file, enable_console=False)

        logger = get_logger("test_file")
        logger.info("File test message")

        # Flush handlers to ensure content is written
        for handler in logging.getLogger().handlers:
            handler.flush()

        assert os.path.exists(log_file)
        with open(log_file, "r") as f:
            content = f.read()
        assert "File test message" in content

def test_get_logger_caching():
    """Test that get_logger returns the same instance for the same name."""
    logger1 = get_logger("cached_logger")
    logger2 = get_logger("cached_logger")
    assert logger1 is logger2

def test_error_context_serialization():
    """Test that error context is preserved."""
    try:
        raise DataLoadingError("Failed to load", context={"row": 123, "col": "A"})
    except ResearchPipelineError as e:
        assert e.context["row"] == 123
        assert e.context["col"] == "A"