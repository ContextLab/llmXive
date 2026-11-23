"""
Unit tests for logging utilities.
"""
import pytest
from pathlib import Path
import sys
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logger import setup_logging, get_logger, log_artifact_checksum

class TestLogger:
    """Unit tests for logging utilities."""

    def test_setup_logging(self):
        """Test logging setup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            setup_logging(log_file=log_file, level="DEBUG")
            logger = get_logger("test")
            assert logger is not None

    def test_log_artifact_checksum(self):
        """Test artifact checksum logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")
            
            log_file = Path(tmpdir) / "test.log"
            setup_logging(log_file=log_file, level="INFO")
            
            # This should not raise
            log_artifact_checksum(str(test_file))
