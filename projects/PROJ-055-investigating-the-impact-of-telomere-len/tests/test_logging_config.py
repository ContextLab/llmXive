import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from logging_config import (
    ensure_log_directory,
    get_memory_usage_bytes,
    check_memory_pressure,
    get_memory_status,
    setup_logging,
    log_memory_status,
    handle_memory_pressure,
    init_project_logging,
    MEMORY_THRESHOLD_BYTES
)

@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary log directory for testing."""
    return tmp_path / "logs"

def test_ensure_log_directory_creates_dir(tmp_path):
    """Test that ensure_log_directory creates the directory if it doesn't exist."""
    test_dir = tmp_path / "test_logs"
    with patch('logging_config.LOG_DIR', test_dir):
        result = ensure_log_directory()
        assert result.exists()
        assert result.is_dir()

def test_ensure_log_directory_existing_dir(tmp_path):
    """Test that ensure_log_directory doesn't fail if directory exists."""
    test_dir = tmp_path / "test_logs"
    test_dir.mkdir()
    with patch('logging_config.LOG_DIR', test_dir):
        result = ensure_log_directory()
        assert result.exists()

def test_get_memory_usage_bytes_returns_positive():
    """Test that memory usage is a positive integer."""
    mem_bytes = get_memory_usage_bytes()
    assert isinstance(mem_bytes, int)
    assert mem_bytes > 0

def test_get_memory_status_contains_expected_keys():
    """Test that memory status dict contains all expected keys."""
    status = get_memory_status()
    expected_keys = ['rss_bytes', 'vms_bytes', 'percent', 'threshold_bytes', 'exceeds_threshold']
    for key in expected_keys:
        assert key in status

def test_check_memory_pressure_returns_boolean():
    """Test that check_memory_pressure returns a boolean."""
    result = check_memory_pressure()
    assert isinstance(result, bool)

def test_setup_logging_creates_handlers():
    """Test that setup_logging creates appropriate handlers."""
    logger = setup_logging(log_level="INFO", log_file="test.log")
    assert len(logger.handlers) >= 1
    assert logger.level == 20  # INFO level

def test_setup_logging_without_file():
    """Test setup_logging without file logging."""
    logger = setup_logging(log_level="DEBUG")
    # Should have at least console handler
    assert len(logger.handlers) >= 1

def test_log_memory_status_does_not_raise(caplog):
    """Test that log_memory_status doesn't raise exceptions."""
    logger = setup_logging()
    with caplog.at_level("INFO"):
        log_memory_status(logger)
        assert len(caplog.records) >= 1

def test_handle_memory_pressure_returns_boolean():
    """Test that handle_memory_pressure returns a boolean."""
    logger = setup_logging()
    result = handle_memory_pressure(logger)
    assert isinstance(result, bool)

def test_init_project_logging_returns_logger():
    """Test that init_project_logging returns a configured logger."""
    logger = init_project_logging(log_file="init_test.log", log_level="INFO")
    assert logger is not None
    assert logger.level == 20  # INFO

def test_memory_threshold_is_6gb():
    """Test that memory threshold is correctly set to 6GB."""
    assert MEMORY_THRESHOLD_BYTES == 6 * 1024**3

def test_handle_memory_pressure_logs_warning_when_exceeded(caplog):
    """Test that memory pressure warning is logged when threshold exceeded."""
    logger = setup_logging()
    
    # Mock check_memory_pressure to return True
    with patch('logging_config.check_memory_pressure', return_value=True):
        with caplog.at_level("WARNING"):
            result = handle_memory_pressure(logger)
            assert result is True
            assert any("MEMORY PRESSURE" in record.message for record in caplog.records)

def test_handle_memory_pressure_no_warning_when_not_exceeded(caplog):
    """Test that no warning is logged when memory is within limits."""
    logger = setup_logging()
    
    # Mock check_memory_pressure to return False
    with patch('logging_config.check_memory_pressure', return_value=False):
        with caplog.at_level("WARNING"):
            result = handle_memory_pressure(logger)
            assert result is False
            # No warning messages should be present
            warning_messages = [r.message for r in caplog.records if r.levelname == "WARNING"]
            assert len(warning_messages) == 0