"""
Unit tests for logging infrastructure.
"""
import os
import sys
import logging
import json
import tempfile
from pathlib import Path
import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from logging_config import (
    configure_logger,
    get_pipeline_logger,
    log_exception,
    log_stage_start,
    log_stage_end,
    log_warning_count,
    get_log_dir,
    _loggers_initialized
)

@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary log directory for testing."""
    # Temporarily override LOG_DIR
    import logging_config
    original_log_dir = logging_config.LOG_DIR
    logging_config.LOG_DIR = tmp_path / "logs"
    yield tmp_path / "logs"
    logging_config.LOG_DIR = original_log_dir

@pytest.fixture
def reset_loggers():
    """Reset logger registry before each test."""
    _loggers_initialized.clear()
    yield
    _loggers_initialized.clear()

def test_configure_logger_console_only(reset_loggers):
    """Test logger configuration with console output only."""
    logger = configure_logger(
        name="test.console_only",
        level=logging.INFO,
        stage_name="test_stage",
        log_to_file=False,
        log_to_console=True
    )
    
    assert logger.name == "test.console_only"
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)

def test_configure_logger_file_only(temp_log_dir, reset_loggers):
    """Test logger configuration with file output only."""
    logger = configure_logger(
        name="test.file_only",
        level=logging.DEBUG,
        stage_name="test_file_stage",
        log_to_file=True,
        log_to_console=False
    )
    
    assert logger.name == "test.file_only"
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.FileHandler)
    
    # Verify log file exists
    log_files = list(temp_log_dir.glob("test_file_stage_*.log"))
    assert len(log_files) == 1

def test_configure_logger_both(temp_log_dir, reset_loggers):
    """Test logger configuration with both console and file output."""
    logger = configure_logger(
        name="test.both",
        level=logging.WARNING,
        stage_name="test_both_stage",
        log_to_file=True,
        log_to_console=True
    )
    
    assert logger.name == "test.both"
    assert logger.level == logging.WARNING
    assert len(logger.handlers) == 2
    
    # Verify handlers
    handler_types = [type(h).__name__ for h in logger.handlers]
    assert "StreamHandler" in handler_types
    assert "FileHandler" in handler_types

def test_get_pipeline_logger(temp_log_dir, reset_loggers):
    """Test pipeline-specific logger creation."""
    logger = get_pipeline_logger("test_pipeline", level=logging.INFO)
    
    assert logger.name == "pipeline.test_pipeline"
    assert logger.level == logging.INFO
    
    # Should have both console and file handlers
    assert len(logger.handlers) == 2

def test_log_exception(reset_loggers, caplog):
    """Test exception logging functionality."""
    logger = configure_logger(
        name="test.exception",
        level=logging.ERROR,
        stage_name="test_exc",
        log_to_file=False,
        log_to_console=True
    )
    
    try:
        raise ValueError("Test error message")
    except Exception as e:
        log_exception(logger, "An error occurred", e, level=logging.ERROR)
    
    # Check that log contains expected information
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelno == logging.ERROR
    assert "An error occurred" in record.message
    assert "ValueError" in record.message
    assert "Test error message" in record.message
    assert "Traceback" in record.message or "traceback" in record.message.lower()

def test_log_stage_start(reset_loggers, caplog):
    """Test stage start logging."""
    logger = configure_logger(
        name="test.stage_start",
        level=logging.INFO,
        stage_name="test_start",
        log_to_file=False,
        log_to_console=True
    )
    
    config = {"param1": "value1", "param2": 123}
    log_stage_start(logger, "preprocessing", config)
    
    assert len(caplog.records) == 3
    assert any("STARTING STAGE" in record.message for record in caplog.records)
    assert any("preprocessing" in record.message for record in caplog.records)
    assert any("param1" in record.message for record in caplog.records)

def test_log_stage_end_success(reset_loggers, caplog):
    """Test successful stage end logging."""
    logger = configure_logger(
        name="test.stage_end",
        level=logging.INFO,
        stage_name="test_end",
        log_to_file=False,
        log_to_console=True
    )
    
    metrics = {"accuracy": 0.95, "epochs": 150}
    log_stage_end(logger, "feature_extraction", success=True, metrics=metrics)
    
    assert len(caplog.records) == 3
    assert any("SUCCESS" in record.message for record in caplog.records)
    assert any("feature_extraction" in record.message for record in caplog.records)
    assert any("accuracy" in record.message for record in caplog.records)

def test_log_stage_end_failure(reset_loggers, caplog):
    """Test failed stage end logging."""
    logger = configure_logger(
        name="test.stage_fail",
        level=logging.INFO,
        stage_name="test_fail",
        log_to_file=False,
        log_to_console=True
    )
    
    log_stage_end(logger, "classification", success=False)
    
    assert len(caplog.records) == 3
    assert any("FAILED" in record.message for record in caplog.records)

def test_log_warning_count(reset_loggers, caplog):
    """Test warning count logging."""
    logger = configure_logger(
        name="test.warning_count",
        level=logging.WARNING,
        stage_name="test_warn",
        log_to_file=False,
        log_to_console=True
    )
    
    # Test with warnings
    log_warning_count(logger, "preprocessing", warning_count=5)
    assert len(caplog.records) == 1
    assert "5 warnings" in caplog.records[0].message
    
    # Reset caplog
    caplog.records.clear()
    
    # Test without warnings
    log_warning_count(logger, "preprocessing", warning_count=0)
    assert len(caplog.records) == 1
    assert "no warnings" in caplog.records[0].message

def test_get_log_dir_creates_directory(temp_log_dir):
    """Test that get_log_dir creates the directory if it doesn't exist."""
    import logging_config
    
    # Temporarily set to a non-existent subdirectory
    new_path = temp_log_dir / "new_subdir"
    logging_config.LOG_DIR = new_path
    
    result = get_log_dir()
    
    assert result == new_path
    assert result.exists()
    assert result.is_dir()