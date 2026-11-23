import pytest
import logging
import os
from pathlib import Path
import sys

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from logging_config import setup_logging
from config import load_config, ensure_directories

class TestLoggingInfrastructure:
    """Tests for T007: Configure logging infrastructure."""

    def test_setup_logging_creates_file(self, tmp_path):
        """Verify that setup_logging creates the log file in the specified path."""
        # Use a temporary directory for this test to avoid polluting outputs/
        # We temporarily override the ensure_directories call logic by mocking or 
        # simply pointing the log file to the tmp_path.
        
        log_file_path = tmp_path / "test_analysis.log"
        
        # Setup logging pointing to our temp file
        logger = setup_logging(str(log_file_path))
        
        # Verify the file exists
        assert log_file_path.exists(), "Log file was not created."

    def test_setup_logging_writes_message(self, tmp_path):
        """Verify that logging actually writes messages to the file."""
        log_file_path = tmp_path / "test_analysis.log"
        
        # Setup logging
        logger = setup_logging(str(log_file_path))
        test_logger = logging.getLogger("test_module")
        
        # Write a test message
        test_logger.info("Test message for T007 verification")
        
        # Force flush (FileHandler usually auto-flushes on close, but let's be sure)
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.flush()

        # Read file content
        content = log_file_path.read_text()
        
        assert "Test message for T007 verification" in content, "Log message not found in file."

    def test_setup_logging_adds_console_handler(self):
        """Verify that a console handler is added to the root logger."""
        # Clear handlers first to ensure a clean state for this specific check
        root = logging.getLogger()
        original_handlers = root.handlers[:]
        root.handlers.clear()
        
        try:
            logger = setup_logging("outputs/analysis.log")
            
            has_console = any(isinstance(h, logging.StreamHandler) for h in root.handlers)
            assert has_console, "Console handler not found in root logger."
        finally:
            # Restore original handlers
            root.handlers.clear()
            root.handlers.extend(original_handlers)
