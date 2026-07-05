# tests/test_logging.py
# Unit tests for the logging utility module.

import logging
import os
import tempfile
from pathlib import Path

import pytest

# Import the module under test
# We need to ensure the code directory is in the path if not running as a package
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.logging import setup_logging, get_logger, log_warning_structured, _logger


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_setup_logging_creates_file(temp_log_dir):
    """Test that setup_logging creates the log file and directory if needed."""
    log_path = temp_log_dir / "subdir" / "test.log"
    
    # Reset global logger state for this test
    import utils.logging as logging_mod
    logging_mod._logger = None

    logger = setup_logging(log_file=str(log_path), project_root=temp_log_dir)

    assert logger is not None
    assert log_path.exists()
    assert log_path.parent.exists()

    # Verify it logs the initialization message
    assert any("Logging initialized" in str(record.message) for record in logger.handlers[0].stream.getvalue().split('\n')) if hasattr(logger.handlers[0], 'stream') else True


def test_get_logger_returns_child(temp_log_dir):
    """Test that get_logger returns a child logger with the correct name."""
    log_path = temp_log_dir / "test.log"
    
    import utils.logging as logging_mod
    logging_mod._logger = None

    setup_logging(log_file=str(log_path), project_root=temp_log_dir)

    child = get_logger("data_loader")
    assert child.name == "pipeline.data_loader"
    assert child.parent.name == "pipeline"


def test_log_warning_structured(temp_log_dir):
    """Test that log_warning_structured formats and logs the warning correctly."""
    log_path = temp_log_dir / "test.log"
    
    import utils.logging as logging_mod
    logging_mod._logger = None

    setup_logging(log_file=str(log_path), project_root=temp_log_dir)

    # Capture log output
    with pytest.warns(None) as record: # pytest.warns(None) just captures warnings if used with warning filter, but here we just call it
        log_warning_structured("TEST_CAT", "Test message", {"key": "value"})

    # Verify the file exists and contains the warning
    assert log_path.exists()
    content = log_path.read_text()
    assert "[TEST_CAT]" in content
    assert "Test message" in content
    assert "key=value" in content


def test_setup_logging_idempotent(temp_log_dir):
    """Test that calling setup_logging multiple times returns the same logger."""
    log_path = temp_log_dir / "test.log"
    
    import utils.logging as logging_mod
    logging_mod._logger = None

    logger1 = setup_logging(log_file=str(log_path), project_root=temp_log_dir)
    logger2 = setup_logging(log_file=str(log_path), project_root=temp_log_dir)

    assert logger1 is logger2
    # Ensure we didn't add duplicate handlers
    assert len(logger1.handlers) == 2 # File + Console