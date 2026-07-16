import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the module under test
# We need to ensure the path is set up correctly if running standalone,
# but assuming the test runner adds 'code' to sys.path or we import relative to project root.
# Based on task description, we are in tests/ and code/ is sibling.
# The import in the main code is `from config import ...`, implying code/ is on sys.path.
# We will assume the test runner handles PYTHONPATH.
import sys
import importlib

# Ensure code directory is in path for imports
project_root = Path(__file__).parent.parent
code_path = project_root / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

# Reload modules to ensure fresh state if tests run multiple times
if "logging_config" in sys.modules:
    del sys.modules["logging_config"]
if "config" in sys.modules:
    # We might need to mock config if get_output_path depends on env vars not set
    # For this test, we assume config is valid or we patch it.
    pass

from logging_config import setup_logging, get_logger
from config import get_output_path


class TestLoggingSetup:
    def test_creates_log_file(self, tmp_path):
        """Test that setup_logging creates the log file in the specified directory."""
        # Mock get_output_path to return a temporary directory
        with patch("logging_config.get_output_path", return_value=tmp_path):
            logger = setup_logging(log_file="test_run.log", console=False)

            log_file_path = tmp_path / "test_run.log"
            assert log_file_path.exists()

            # Verify content
            content = log_file_path.read_text()
            assert "Logging initialized" in content

    def test_console_handler_added(self):
        """Test that console handler is added when console=True."""
        # Use a temp dir to avoid cluttering actual outputs during test
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch("logging_config.get_output_path", return_value=Path(tmp_dir)):
                logger = setup_logging(console=True)
                handlers = logger.handlers
                # Should have FileHandler and StreamHandler
                assert any(isinstance(h, logging.FileHandler) for h in handlers)
                assert any(isinstance(h, logging.StreamHandler) for h in handlers)

    def test_console_handler_not_added(self):
        """Test that console handler is NOT added when console=False."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch("logging_config.get_output_path", return_value=Path(tmp_dir)):
                logger = setup_logging(console=False)
                handlers = logger.handlers
                # Should only have FileHandler
                assert len(handlers) == 1
                assert isinstance(handlers[0], logging.FileHandler)

    def test_logger_level(self):
        """Test that the logger respects the specified level."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch("logging_config.get_output_path", return_value=Path(tmp_dir)):
                logger = setup_logging(level=logging.DEBUG, console=False)
                assert logger.level == logging.DEBUG

    def test_get_logger_child(self):
        """Test that get_logger returns a child logger."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch("logging_config.get_output_path", return_value=Path(tmp_dir)):
                setup_logging(console=False) # Initialize root
                child = get_logger("test.child")
                assert child.name == "llmXive.test.child"
                assert child.parent.name == "llmXive"

    def test_idempotent_handlers(self):
        """Test that calling setup_logging multiple times doesn't add duplicate handlers."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch("logging_config.get_output_path", return_value=Path(tmp_dir)):
                logger = setup_logging(console=False)
                initial_count = len(logger.handlers)

                # Call again
                logger2 = setup_logging(console=False)

                # Should be the same logger instance (or at least same handlers count if root)
                # The implementation checks `if logger.handlers` so it should return early.
                assert len(logger.handlers) == initial_count
                assert logger is logger2