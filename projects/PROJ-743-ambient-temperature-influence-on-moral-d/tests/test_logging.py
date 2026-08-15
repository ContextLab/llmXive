import logging
import os
from pathlib import Path
import tempfile
import shutil

import pytest

from code.setup_logging import (
    setup_logging,
    get_data_quality_logger,
    get_model_diagnostics_logger,
    ensure_directories,
    _handlers_configured
)
from code.config import get_path_env_override


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for logging tests."""
    temp_dir = tempfile.mkdtemp()
    log_path = Path(temp_dir) / "logs"
    yield log_path
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture(autouse=True)
def reset_logging_state():
    """Reset logging state before each test to ensure isolation."""
    # We need to reset the global flag and handlers to test setup logic
    # This is a bit hacky for a module-level global, but necessary for idempotency testing
    import code.setup_logging as sl
    sl._handlers_configured = False
    # Clear root handlers to avoid pollution
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    # Clear specific loggers
    for name in ['data_quality', 'model_diagnostics']:
        log = logging.getLogger(name)
        log.handlers.clear()
        log.setLevel(logging.NOTSET)
    yield
    # Reset after
    sl._handlers_configured = False


def test_ensure_directories_creates_path(temp_log_dir):
    """Test that ensure_directories creates the folder if missing."""
    target = temp_log_dir / "subdir"
    assert not target.exists()
    ensure_directories(target)
    assert target.exists()
    assert target.is_dir()


def test_setup_logging_creates_files(temp_log_dir):
    """Test that setup_logging creates the required log files."""
    setup_logging(temp_log_dir)
    
    assert (temp_log_dir / "pipeline.log").exists()
    assert (temp_log_dir / "data_quality.log").exists()
    assert (temp_log_dir / "model_diagnostics.log").exists()


def test_get_data_quality_logger_returns_valid_logger(temp_log_dir):
    """Test that the data quality logger is correctly configured."""
    # Force setup first
    setup_logging(temp_log_dir)
    
    logger = get_data_quality_logger()
    assert isinstance(logger, logging.Logger)
    assert logger.name == 'data_quality'
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) > 0
    
    # Verify it writes to the correct file
    handler = logger.handlers[0]
    assert isinstance(handler, logging.FileHandler)
    assert "data_quality.log" in handler.baseFilename


def test_get_model_diagnostics_logger_returns_valid_logger(temp_log_dir):
    """Test that the model diagnostics logger is correctly configured."""
    setup_logging(temp_log_dir)
    
    logger = get_model_diagnostics_logger()
    assert isinstance(logger, logging.Logger)
    assert logger.name == 'model_diagnostics'
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) > 0
    
    handler = logger.handlers[0]
    assert isinstance(handler, logging.FileHandler)
    assert "model_diagnostics.log" in handler.baseFilename


def test_logging_writes_actual_entries(temp_log_dir, caplog):
    """Test that log messages are actually written to the files."""
    setup_logging(temp_log_dir)
    
    dq_logger = get_data_quality_logger()
    test_message = "Test data quality message"
    
    dq_logger.info(test_message)
    
    # Read the file content
    log_file = temp_log_dir / "data_quality.log"
    assert log_file.exists()
    
    content = log_file.read_text()
    assert test_message in content


def test_loggers_do_not_propagate_to_root(temp_log_dir):
    """Test that specific loggers do not double-log to the root handler."""
    setup_logging(temp_log_dir)
    
    dq_logger = get_data_quality_logger()
    root_logger = logging.getLogger()
    
    # Verify propagate is False
    assert dq_logger.propagate is False
    
    # If we add a handler to root that captures DEBUG, 
    # the data_quality logger should NOT send messages there.
    # This test ensures the configuration isolates the logs.
    assert len(dq_logger.handlers) == 1
    assert len(root_logger.handlers) > 0 # Should have general/console
    
    # The handler on root should be the general one (INFO+)
    # If dq_logger propagated, it would hit root.
    # Since propagate=False, it only hits its own file handler.
    # This is verified by the fact that we didn't see duplicates in a real run,
    # but structurally we check the flag.
    

def test_idempotency_of_setup(temp_log_dir):
    """Test that calling setup_logging multiple times doesn't duplicate handlers."""
    setup_logging(temp_log_dir)
    first_count = len(logging.getLogger('data_quality').handlers)
    
    setup_logging(temp_log_dir)
    second_count = len(logging.getLogger('data_quality').handlers)
    
    assert first_count == second_count
    assert first_count == 1 # Should only have one file handler