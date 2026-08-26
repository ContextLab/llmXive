"""
Tests for the logger utility module.
"""
import logging
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Ensure code directory is in path for imports
@pytest.fixture(autouse=True)
def setup_path():
    code_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(code_dir))
    yield
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

class TestLogger:
    @pytest.fixture
    def logger(self):
        from src.utils.logger import setup_default_logger
        return setup_default_logger("test_logger")

    def test_logger_creation(self, logger):
        """Test that a logger can be created."""
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_logger_log_levels(self, logger):
        """Test that logger supports standard log levels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            handler = logging.FileHandler(log_file)
            logger.addHandler(handler)
            
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")
            
            assert log_file.exists()
            with open(log_file, 'r') as f:
                content = f.read()
                assert "Debug message" in content
                assert "Info message" in content
                assert "Warning message" in content
                assert "Error message" in content
                assert "Critical message" in content
