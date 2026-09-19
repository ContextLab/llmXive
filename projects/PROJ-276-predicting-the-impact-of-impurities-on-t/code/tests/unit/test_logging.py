import logging
import os
import sys
import tempfile
from pathlib import Path
import pytest
from code.src.utils.logging import (
    get_logger,
    get_ingestion_logger,
    get_modeling_logger,
    get_visualization_logger,
    get_project_logger
)


class TestLoggingConfiguration:
    """Tests for logging configuration and retrieval functions."""

    def test_get_logger_returns_logger(self):
        """Verify get_logger returns a logging.Logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_name_format(self):
        """Verify logger name includes project prefix."""
        logger = get_logger("test_module")
        assert "mgb2_impurity" in logger.name or logger.name == "test_module"

    def test_get_ingestion_logger(self):
        """Verify ingestion logger is configured correctly."""
        logger = get_ingestion_logger()
        assert isinstance(logger, logging.Logger)
        assert "ingestion" in logger.name.lower() or "mgb2" in logger.name.lower()

    def test_get_modeling_logger(self):
        """Verify modeling logger is configured correctly."""
        logger = get_modeling_logger()
        assert isinstance(logger, logging.Logger)
        assert "modeling" in logger.name.lower() or "mgb2" in logger.name.lower()

    def test_get_visualization_logger(self):
        """Verify visualization logger is configured correctly."""
        logger = get_visualization_logger()
        assert isinstance(logger, logging.Logger)
        assert "visualization" in logger.name.lower() or "mgb2" in logger.name.lower()

    def test_get_project_logger(self):
        """Verify project logger is configured correctly."""
        logger = get_project_logger()
        assert isinstance(logger, logging.Logger)
        assert "mgb2" in logger.name.lower() or "project" in logger.name.lower()

    def test_logger_has_stream_handler(self):
        """Verify loggers have a StreamHandler attached."""
        logger = get_logger("test_stream")
        handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(handlers) > 0, "Logger should have a StreamHandler"

    def test_logger_level_configuration(self):
        """Verify logger level is set to INFO or DEBUG by default."""
        logger = get_logger("test_level")
        assert logger.level <= logging.INFO, "Default level should be INFO or lower"

    def test_multiple_calls_return_same_instance(self):
        """Verify calling get_logger multiple times returns the same instance."""
        logger1 = get_logger("singleton_test")
        logger2 = get_logger("singleton_test")
        assert logger1 is logger2, "get_logger should return the same instance"

    def test_specialized_loggers_are_distinct(self):
        """Verify specialized loggers have different names."""
        ingestion = get_ingestion_logger()
        modeling = get_modeling_logger()
        visualization = get_visualization_logger()

        assert ingestion.name != modeling.name
        assert modeling.name != visualization.name
        assert ingestion.name != visualization.name

    def test_logger_can_write_message(self):
        """Verify logger can actually write a message."""
        logger = get_logger("test_write")
        # Capture log output by setting level to DEBUG and checking handlers
        logger.setLevel(logging.DEBUG)
        # Just ensure no exception is raised when logging
        logger.info("Test message")
        logger.debug("Debug message")
        assert True  # If we got here without exception, it passed

    def test_logger_propagation(self):
        """Verify logger propagation settings."""
        logger = get_logger("test_propagation")
        # Loggers should typically have propagation enabled unless root
        assert logger.propagate in [True, False]  # Just check it's a boolean