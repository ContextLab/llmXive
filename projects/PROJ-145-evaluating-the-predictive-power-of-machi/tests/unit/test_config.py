"""
Unit tests for configuration loading and validation.
"""
import pytest
from config import ensure_dirs, setup_logging
import logging

def test_setup_logging():
    """Test that logging is configured correctly."""
    logger = setup_logging()
    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.INFO

def test_ensure_dirs(tmp_path):
    """Test that ensure_dirs creates the required directory structure."""
    # Mock the config paths to use a temporary directory
    import config
    original_data_root = config.DATA_ROOT
    config.DATA_ROOT = str(tmp_path)
    
    try:
        ensure_dirs()
        
        # Verify directories exist
        assert (tmp_path / "raw").exists()
        assert (tmp_path / "processed").exists()
        assert (tmp_path / "models").exists()
        assert (tmp_path / "figures").exists()
    finally:
        config.DATA_ROOT = original_data_root
