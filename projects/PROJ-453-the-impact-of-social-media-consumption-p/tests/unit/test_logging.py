"""
Unit tests for logging configuration.
"""
import logging
import sys
from pathlib import Path

def test_logger_initialization():
    """Test that the logger is properly initialized."""
    from logging_config import setup_logging, get_logger
    
    # Setup logging
    setup_logging()
    
    # Get logger
    logger = get_logger("test_logger")
    
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"
    assert logger.level == logging.INFO

def test_logger_format():
    """Test that the logger output format is correct."""
    from logging_config import setup_logging, get_logger
    
    # Setup logging
    setup_logging()
    
    # Get logger
    logger = get_logger("test_format")
    
    # Check handlers
    handlers = logger.handlers if logger.handlers else logging.root.handlers
    assert len(handlers) > 0
    
    # Check formatter
    for handler in handlers:
        if hasattr(handler, 'formatter'):
            fmt = handler.formatter._fmt
            assert "[%(asctime)s] %(levelname)s: %(message)s" in fmt or "asctime" in fmt

def test_checksum_file():
    """Test the checksum_file utility function."""
    from utils import checksum_file
    import tempfile
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        checksum = checksum_file(temp_path)
        assert len(checksum) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)
    finally:
        import os
        os.unlink(temp_path)

def test_causal_language_scanner():
    """Test the causal language scanner."""
    from utils import causal_language_scanner
    
    # Test positive case
    assert causal_language_scanner("This causes that", ["causes"]) is True
    assert causal_language_scanner("This leads to that", ["leads to"]) is True
    
    # Test negative case
    assert causal_language_scanner("This is associated with that", ["causes", "leads to"]) is False
    
    # Test case insensitivity
    assert causal_language_scanner("This CAUSES that", ["causes"]) is True
