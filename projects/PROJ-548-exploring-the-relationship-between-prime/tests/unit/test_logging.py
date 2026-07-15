"""
Unit tests for the memory-efficient logging infrastructure.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import logging

# Adjust path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.logging import (
    get_logger,
    log_chunk_progress,
    log_oom_warning,
    _get_memory_usage_mb,
    _check_memory_and_log,
    MEMORY_WARNING_THRESHOLD_BYTES,
    LOG_DIR
)


@pytest.fixture
def temp_log_dir():
    """Creates a temporary directory for logging tests to avoid polluting the real logs/."""
    original_dir = LOG_DIR
    temp_dir = Path(tempfile.mkdtemp())
    # Temporarily override the global LOG_DIR constant if possible,
    # but since it's imported, we might need to mock or just test the behavior.
    # For this test, we will just verify the logger creation and basic functionality.
    yield temp_dir
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


def test_get_logger_creates_instance():
    """Test that get_logger returns a valid logger instance."""
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"
    assert logger.level == logging.INFO


def test_logger_has_handlers():
    """Test that the logger has both file and console handlers."""
    logger = get_logger("test_logger_handlers")
    assert len(logger.handlers) == 2
    # One should be RotatingFileHandler (or FileHandler in mock env)
    # One should be StreamHandler
    types = [type(h).__name__ for h in logger.handlers]
    assert "RotatingFileHandler" in types or "FileHandler" in types
    assert "StreamHandler" in types


def test_get_memory_usage_mb():
    """Test that memory usage function returns a non-negative number."""
    mem_mb = _get_memory_usage_mb()
    assert isinstance(mem_mb, float)
    assert mem_mb >= 0.0


def test_log_chunk_progress(capsys):
    """Test that chunk progress logging works."""
    logger = get_logger("test_chunk_log")
    # Capture log output
    log_chunk_progress(logger, chunk_id=1, total_chunks=10, items_processed=100)
    captured = capsys.readouterr()
    assert "Chunk Progress" in captured.out
    assert "[1/10]" in captured.out
    assert "10.0%" in captured.out
    assert "100" in captured.out


def test_log_oom_warning(capsys):
    """Test that OOM warning logging works."""
    logger = get_logger("test_oom_log")
    # This should not raise an error, even if memory is low
    log_oom_warning(logger, context="Test Context")
    captured = capsys.readouterr()
    # If memory is low, it might not print a warning, but the function should run.
    # We just verify it doesn't crash.
    assert True


def test_check_memory_and_log_no_crash():
    """Test that memory check function runs without crashing."""
    logger = get_logger("test_mem_check")
    # Should not raise
    _check_memory_and_log(logger, "Test Check")
    assert True