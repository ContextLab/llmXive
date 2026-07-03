import os
import logging
import tempfile
import pytest
from pathlib import Path

# Import the module to test
# We need to ensure the code directory is in the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.logging_config import setup_logging, get_logger, LOG_DIR

class TestLoggingConfig:
    @pytest.fixture
    def temp_log_file(self):
        """Create a temporary file for logging tests."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            yield Path(f.name)
        os.unlink(f.name)

    def test_setup_logging_creates_file(self, temp_log_file):
        """Test that setup_logging creates the log file and writes to it."""
        logger = setup_logging(log_file=temp_log_file, console_output=False)
        
        # Log a message
        logger.info("Test log message")
        
        # Force flush
        for handler in logger.handlers:
            handler.flush()

        # Check file exists
        assert temp_log_file.exists(), "Log file was not created"

        # Check content
        with open(temp_log_file, 'r') as f:
            content = f.read()
        
        assert "Test log message" in content, "Log message not found in file"
        assert "INFO" in content, "Log level not found in file"

    def test_setup_logging_console_output(self, capsys):
        """Test that setup_logging writes to console when enabled."""
        # Create a temp file to satisfy the file handler requirement
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            temp_path = Path(f.name)
        
        try:
            logger = setup_logging(log_file=temp_path, console_output=True)
            logger.info("Console test message")
            
            # Flush handlers
            for handler in logger.handlers:
                handler.flush()

            captured = capsys.readouterr()
            assert "Console test message" in captured.out
        finally:
            if temp_path.exists():
                os.unlink(temp_path)

    def test_get_logger_returns_instance(self):
        """Test that get_logger returns a valid logger instance."""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "llmXive"

    def test_get_logger_child_logger(self):
        """Test that get_logger creates child loggers correctly."""
        child = get_logger("data.fetch_prs")
        assert isinstance(child, logging.Logger)
        assert child.name == "llmXive.data.fetch_prs"

    def test_log_levels(self, temp_log_file):
        """Test that different log levels are respected."""
        logger = setup_logging(log_file=temp_log_file, level=logging.WARNING, console_output=False)
        
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        
        for handler in logger.handlers:
            handler.flush()

        with open(temp_log_file, 'r') as f:
            content = f.read()
        
        assert "Debug message" not in content
        assert "Info message" not in content
        assert "Warning message" in content