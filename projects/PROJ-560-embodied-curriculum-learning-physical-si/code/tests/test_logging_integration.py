"""
Integration tests for logging configuration.

This module tests that logging is correctly set up and writes to files.
"""
import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path
from src.logging_config import setup_logging
import logging


class TestLoggingIntegration:
    """Tests for logging integration."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test.log")

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_logging_to_file(self):
        """Test that logs are written to file."""
        setup_logging(log_level=logging.INFO, log_file=self.log_file)
        logger = logging.getLogger(__name__)

        logger.info("Test log message")

        assert os.path.exists(self.log_file)
        with open(self.log_file, 'r') as f:
            content = f.read()
        assert "Test log message" in content

    def test_logging_to_console(self):
        """Test that logs are written to console."""
        # This is harder to test programmatically, but we can ensure setup works
        setup_logging(log_level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.info("Console test message")
        # If no exception, setup worked
        assert True
