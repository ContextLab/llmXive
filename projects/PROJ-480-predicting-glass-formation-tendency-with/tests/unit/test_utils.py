"""
Unit tests for src/lib/utils.py
"""
import os
import tempfile
import hashlib
import pytest
from pathlib import Path

from src.lib.utils import calculate_sha256, get_logger
from src.lib.exceptions import DataValidationError

def test_calculate_sha256_simple():
    """Test SHA-256 calculation on a simple string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("hello world")
        temp_path = f.name

    try:
        calculated_hash = calculate_sha256(temp_path)
        expected_hash = hashlib.sha256(b"hello world").hexdigest()
        assert calculated_hash == expected_hash
    finally:
        os.unlink(temp_path)

def test_calculate_sha256_empty_file():
    """Test SHA-256 calculation on an empty file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        temp_path = f.name

    try:
        calculated_hash = calculate_sha256(temp_path)
        expected_hash = hashlib.sha256(b"").hexdigest()
        assert calculated_hash == expected_hash
    finally:
        os.unlink(temp_path)

def test_calculate_sha256_nonexistent_file():
    """Test that FileNotFoundError is raised for non-existent file."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256("/nonexistent/path/file.txt")

def test_get_logger():
    """Test logger creation and configuration."""
    logger = get_logger("test_logger", level=10) # DEBUG
    assert logger.name == "test_logger"
    assert logger.level == 10
    assert len(logger.handlers) == 1

def test_get_logger_reuse():
    """Test that getting the same logger again doesn't add duplicate handlers."""
    logger1 = get_logger("test_logger_reuse", level=20)
    logger2 = get_logger("test_logger_reuse", level=30)
    # Should have exactly one handler
    assert len(logger1.handlers) == 1
    assert len(logger2.handlers) == 1
