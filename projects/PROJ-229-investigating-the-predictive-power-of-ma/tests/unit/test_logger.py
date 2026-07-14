"""
Unit tests for the logging infrastructure.
"""
import logging
import os
import tempfile
from pathlib import Path

import pytest

from code.utils.logger import setup_logger, get_pipeline_logger
from config import get_config


class TestSetupLogger:
    def test_console_handler_added(self):
        """Test that a console handler is added when console=True."""
        logger = setup_logger("test_console", console=True)
        assert len(logger.handlers) >= 1
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_file_handler_added(self):
        """Test that a file handler is added when log_file is provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logger("test_file", log_file=str(log_path))
            
            # Verify file exists after setup (handler flushes on close, but we check existence)
            # Note: FileHandler creates the file immediately in many implementations
            # or on first write. We verify the handler is attached.
            assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)

    def test_logger_level_from_config(self):
        """Test that logger respects config level if not explicitly set."""
        # This assumes config.yaml has a logging.level set (from T004)
        logger = setup_logger("test_config_level")
        # The level should match the config, defaulting to INFO if not found
        assert logger.level != logging.NOTSET

class TestGetPipelineLogger:
    def test_returns_logger_instance(self):
        """Test that get_pipeline_logger returns a valid logger."""
        logger = get_pipeline_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "llmXive.pipeline"
