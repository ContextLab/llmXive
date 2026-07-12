"""
Unit tests for utility functions.
"""
import pytest
import os
import tempfile
from pathlib import Path

def test_logging():
    """Test that logging utility works correctly."""
    from src.utils.logging import get_logger
    
    logger = get_logger("test_logger")
    assert logger is not None
    
    # Test logging
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "test.log")
        logger.addHandler(logging.FileHandler(log_file))
        
        logger.info("Test message")
        
        # Verify log file was created
        assert os.path.exists(log_file)

def test_file_operations():
    """Test file utility functions."""
    from src.utils.files import ensure_dir, read_json, write_json
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test ensure_dir
        test_dir = os.path.join(tmpdir, "test_dir")
        ensure_dir(test_dir)
        assert os.path.exists(test_dir)
        
        # Test read_json and write_json
        test_data = {"key": "value"}
        json_file = os.path.join(tmpdir, "test.json")
        write_json(json_file, test_data)
        
        loaded_data = read_json(json_file)
        assert loaded_data == test_data