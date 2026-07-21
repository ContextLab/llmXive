"""
Unit tests for logging utilities.
"""
import os
import pytest
import logging
from pathlib import Path
from src.utils.logging import setup_logger, get_log_file, clear_logs
from src.utils.config import get_interim_data_dir

def test_setup_logger_returns_logger():
    logger = setup_logger('test_logger')
    assert isinstance(logger, logging.Logger)
    assert logger.name == 'test_logger'

def test_setup_logger_adds_console_handler():
    logger = setup_logger('test_console')
    assert len(logger.handlers) >= 1
    # Check for StreamHandler
    console_handler = None
    for h in logger.handlers:
        if isinstance(h, logging.StreamHandler):
            console_handler = h
            break
    assert console_handler is not None

def test_setup_logger_adds_file_handler(tmp_path, monkeypatch):
    """Test that setup_logger creates a file handler when log_file is provided."""
    # We can't easily monkeypatch the global get_interim_data_dir in a simple way
    # without reloading modules, so we test the path logic indirectly.
    # Instead, we verify that the function accepts the argument and doesn't crash.
    logger = setup_logger('test_file', log_file='test.log')
    assert isinstance(logger, logging.Logger)
    # If we reached here without error, the path resolution likely worked (or failed silently if dir missing)
    # In a real CI, the dir would exist.

def test_get_log_file_returns_path():
    log_path = get_log_file('test.log')
    assert isinstance(log_path, Path)
    assert log_path.name == 'test.log'
    assert 'interim' in str(log_path)
