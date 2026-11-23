"""
Unit tests for logging configuration.
"""
import pytest
import logging
import os
from pathlib import Path
from utils.logging_config import setup_logging, get_logger
from config import get_log_level, get_log_format


class TestLoggingConfig:
    def test_setup_logging_creates_file(self):
        # Ensure the log directory exists for the test
        log_dir = Path("data/processed/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Run setup
        setup_logging()
        
        # Verify root logger has handlers
        root = logging.getLogger()
        assert len(root.handlers) > 0
        
        # Verify log file exists
        log_file = log_dir / "pipeline.log"
        assert log_file.exists()

    def test_get_logger_returns_instance(self):
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_default_name(self):
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "solder_pipeline"

    def test_log_levels(self):
        setup_logging(log_level="DEBUG")
        logger = get_logger("level_test")
        # Just verify we can log without error
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
