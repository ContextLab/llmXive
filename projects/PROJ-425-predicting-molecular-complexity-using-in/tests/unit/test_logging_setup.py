import os
import logging
import tempfile
from pathlib import Path
import pytest

# We need to ensure code/ is in the path to import logging_setup
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from logging_setup import setup_logging, get_logger, log_skipped_molecule, log_data_loading_stats, log_timeout_event

@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file path for testing."""
    log_file = tmp_path / "test.log"
    return str(log_file)

def test_setup_logging_creates_file(temp_log_file):
    """Test that setup_logging creates the log file and handlers."""
    logger = setup_logging(log_file=temp_log_file)
    
    # Check that the file exists
    assert os.path.exists(temp_log_file), "Log file should be created"
    
    # Check that handlers are attached
    assert len(logger.handlers) > 0, "Logger should have handlers"
    
    # Check for FileHandler
    file_handler_found = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
    assert file_handler_found, "Logger should have a FileHandler"

def test_get_logger_returns_child_logger():
    """Test that get_logger returns a child logger."""
    parent = setup_logging()
    child = get_logger("test_module")
    
    assert child.name == "llmXive.test_module"
    assert child.parent.name == "llmXive"

def test_log_skipped_molecule(caplog, temp_log_file):
    """Test logging a skipped molecule."""
    setup_logging(log_file=temp_log_file)
    
    log_skipped_molecule("CID-123", "timeout", {"details": "took too long"})
    
    # Check log content
    assert "SKIPPED_MOLECULE" in caplog.text
    assert "CID-123" in caplog.text
    assert "timeout" in caplog.text
    assert "took too long" in caplog.text

def test_log_data_loading_stats(caplog, temp_log_file):
    """Test logging data loading statistics."""
    setup_logging(log_file=temp_log_file)
    
    log_data_loading_stats(10000, 5000, "checksum123", 10.5)
    
    assert "DATA_LOAD_STATS" in caplog.text
    assert "10000" in caplog.text
    assert "5000" in caplog.text
    assert "checksum123" in caplog.text
    assert "10.5" in caplog.text

def test_log_timeout_event(caplog, temp_log_file):
    """Test logging a timeout event."""
    setup_logging(log_file=temp_log_file)
    
    log_timeout_event("compute_lz", "CID-999", 5.0)
    
    assert "TIMEOUT_EVENT" in caplog.text
    assert "compute_lz" in caplog.text
    assert "CID-999" in caplog.text
    assert "5.0" in caplog.text
