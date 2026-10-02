"""
Unit tests for the logging utility module.
"""
import logging
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Ensure we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.utils.logging import (
    get_logger,
    get_ingestion_logger,
    get_modeling_logger,
    get_visualization_logger,
    get_project_logger,
    _logger_cache
)


class TestLoggingConfiguration:
    """Tests for logging configuration and retrieval functions."""

    def setup_method(self):
        """Clear the logger cache before each test to ensure isolation."""
        _logger_cache.clear()

    def test_get_logger_returns_logger_instance(self):
        """Verify get_logger returns a valid Logger instance."""
        logger = get_logger("test.logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.logger"

    def test_get_ingestion_logger(self):
        """Verify get_ingestion_logger returns a logger with correct name."""
        logger = get_ingestion_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "ingestion"

    def test_get_modeling_logger(self):
        """Verify get_modeling_logger returns a logger with correct name."""
        logger = get_modeling_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "modeling"

    def test_get_visualization_logger(self):
        """Verify get_visualization_logger returns a logger with correct name."""
        logger = get_visualization_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "visualization"

    def test_get_project_logger(self):
        """Verify get_project_logger returns a logger with correct name."""
        logger = get_project_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "llmXive_mgb2"

    def test_logger_level_configuration(self):
        """Verify that loggers respect the configured level."""
        debug_logger = get_logger("test.debug", level=logging.DEBUG)
        info_logger = get_logger("test.info", level=logging.INFO)

        assert debug_logger.level == logging.DEBUG
        assert info_logger.level == logging.INFO

    def test_logger_caching(self):
        """Verify that calling get_logger multiple times returns the same instance."""
        logger1 = get_logger("test.cache")
        logger2 = get_logger("test.cache")
        assert logger1 is logger2

    def test_logger_has_handlers(self):
        """Verify that loggers are configured with at least one handler."""
        logger = get_logger("test.handlers")
        assert len(logger.handlers) > 0

    def test_logger_propagate_false(self):
        """Verify that loggers do not propagate to root to avoid double logging."""
        logger = get_logger("test.propagate")
        assert logger.propagate is False

    def test_custom_level_for_specific_loggers(self):
        """Verify custom levels can be set for specific logger types."""
        ingestion_logger = get_ingestion_logger(level=logging.WARNING)
        assert ingestion_logger.level == logging.WARNING

        modeling_logger = get_modeling_logger(level=logging.ERROR)
        assert modeling_logger.level == logging.ERROR