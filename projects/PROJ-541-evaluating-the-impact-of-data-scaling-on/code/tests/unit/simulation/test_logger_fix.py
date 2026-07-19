"""Test cases for the setup_logger function with various call signatures."""
import pytest
import sys
from pathlib import Path
from simulation.logger import setup_logger

def test_setup_logger_with_batch_id():
    """Test setup_logger called with batch_id keyword argument."""
    logger = setup_logger(batch_id="main_pipeline")
    assert logger is not None
    assert logger.name == "batch_main_pipeline"
    assert logger.batch_id == "main_pipeline"

def test_setup_logger_with_name():
    """Test setup_logger called with a string name."""
    logger = setup_logger("test_scaling")
    assert logger is not None
    assert logger.name == "test_scaling"

def test_setup_logger_with_name_and_batch_id():
    """Test setup_logger called with both name and batch_id."""
    logger = setup_logger("test_name", batch_id="test_batch")
    assert logger is not None
    # Name takes precedence when provided as positional arg
    assert logger.name == "test_name"

def test_setup_logger_with_underscore_name():
    """Test setup_logger called with __name__ style argument."""
    logger = setup_logger(__name__)
    assert logger is not None
    assert logger.name == __name__

def test_setup_logger_no_args():
    """Test setup_logger called with no arguments."""
    logger = setup_logger()
    assert logger is not None
    assert logger.name == "reproducibility"

def test_setup_logger_returns_logger_instance():
    """Test that setup_logger returns a ReproducibilityLogger instance."""
    from simulation.logger import ReproducibilityLogger
    logger = setup_logger("test")
    assert isinstance(logger, ReproducibilityLogger)

def test_logger_log_method():
    """Test that logger has a log method that returns LogEntry."""
    logger = setup_logger("test")
    entry = logger.log("test_operation", param1="value1")
    assert entry is not None
    assert entry.operation == "test_operation"
    assert entry.parameters["param1"] == "value1"

def test_logger_info_method():
    """Test that logger.info is a no-op (tolerant)."""
    logger = setup_logger("test")
    # Should not raise
    logger.info("test message")
    logger.debug("debug message")
    logger.warning("warning message")
    logger.error("error message")
    logger.critical("critical message")
