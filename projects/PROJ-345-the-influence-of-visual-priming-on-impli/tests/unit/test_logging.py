import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.main import setup_logging
from code.config import Config

class TestLoggingConfiguration:
    """Tests for logging configuration in code/main.py"""

    def test_setup_logging_creates_file_handler(self):
        """Verify that setup_logging creates a file handler pointing to code/logs/pipeline.log"""
        # Ensure clean state
        log_dir = Path("code/logs")
        log_file = log_dir / "pipeline.log"
        
        if log_file.exists():
            log_file.unlink()
        
        # Setup logging
        setup_logging()
        
        # Verify file exists
        assert log_file.exists(), "Log file code/logs/pipeline.log should be created"

    def test_setup_logging_format(self):
        """Verify that log format matches the required pattern"""
        log_dir = Path("code/logs")
        log_file = log_dir / "pipeline.log"
        
        if log_file.exists():
            log_file.unlink()
        
        # Setup logging
        setup_logging()
        logger = logging.getLogger("test_logger")
        logger.info("Test message for format verification")
        
        # Read log file and check format
        assert log_file.exists()
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Check that the log line contains expected components
        assert "test_logger" in content, "Log should contain logger name"
        assert "INFO" in content, "Log should contain level"
        assert "Test message for format verification" in content, "Log should contain message"
        
        # Check timestamp format (basic check)
        assert "-" in content, "Log should use '-' as separator"

    def test_setup_logging_stdout(self):
        """Verify that logging also outputs to stdout"""
        log_dir = Path("code/logs")
        log_file = log_dir / "pipeline.log"
        
        if log_file.exists():
            log_file.unlink()
        
        # Setup logging
        setup_logging()
        logger = logging.getLogger("test_stdout_logger")
        
        # Capture stdout
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            logger.info("Test stdout message")
        
        output = f.getvalue()
        assert "Test stdout message" in output, "Log should output to stdout"

    def test_log_file_contains_entries_after_run(self):
        """Verify that log file contains entries after running the main function"""
        log_dir = Path("code/logs")
        log_file = log_dir / "pipeline.log"
        
        # Clean previous log
        if log_file.exists():
            log_file.unlink()
        
        # Import and run main (without arguments)
        from code.main import main
        main()
        
        # Verify log file exists and has content
        assert log_file.exists(), "Log file should exist after main() execution"
        with open(log_file, 'r') as f:
            content = f.read()
        
        assert len(content) > 0, "Log file should contain entries"
        assert "Pipeline" in content or "pipeline" in content, "Log should contain pipeline-related messages"