import logging
import os
import tempfile
from pathlib import Path
import pytest
from code.utils.logging_config import get_logger, setup_root_logger, LOG_DIR

@pytest.fixture(autouse=True)
def reset_loggers():
    # Reset the global logger registry before each test
    from code.utils.logging_config import _loggers
    _loggers.clear()
    # Clear root handlers to ensure clean state
    logging.getLogger().handlers.clear()
    yield
    # Cleanup after test
    logging.getLogger().handlers.clear()
    _loggers.clear()

def test_get_logger_creates_instance():
    logger = get_logger("test_module")
    assert logger is not None
    assert logger.name == "test_module"

def test_get_logger_returns_same_instance():
    logger1 = get_logger("test_singleton")
    logger2 = get_logger("test_singleton")
    assert logger1 is logger2

def test_logger_has_handlers():
    # Ensure root is setup first
    setup_root_logger()
    logger = get_logger("test_handlers")
    # Since propagate is True, it relies on root handlers.
    # But let's check if root has handlers
    root = logging.getLogger()
    assert len(root.handlers) > 0

def test_log_file_created(tmp_path):
    # Temporarily override LOG_DIR for testing if needed, 
    # but here we just verify that setup_root_logger creates a handler.
    # Since LOG_DIR is global, we can't easily change it without patching.
    # We verify that the handler is added.
    setup_root_logger()
    root = logging.getLogger()
    file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) == 1

def test_setup_root_logger():
    logger = setup_root_logger()
    assert logger.level == logging.INFO
    assert len(logger.handlers) >= 2  # File and Console

def test_logger_levels():
    setup_root_logger()
    debug_logger = get_logger("debug_test", level=logging.DEBUG)
    assert debug_logger.level == logging.DEBUG
    
    error_logger = get_logger("error_test", level=logging.ERROR)
    assert error_logger.level == logging.ERROR
