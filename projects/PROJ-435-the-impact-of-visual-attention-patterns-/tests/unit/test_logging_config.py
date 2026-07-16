"""
Unit tests for the logging infrastructure (Task T008).
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
import pytest
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logging_config import (
    setup_logging,
    log_quality_warning,
    log_exclusion_count,
    log_pipeline_status,
    _load_config,
    _configured_loggers
)

@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config.yaml file."""
    config_data = {
        "logging": {
            "level": "DEBUG",
            "file": str(tmp_path / "test.log"),
            "format": "[TEST] %(levelname)s - %(message)s"
        }
    }
    config_path = Path(__file__).parent.parent.parent / "code" / "config.yaml"
    # Backup existing config if any
    backup_path = None
    if config_path.exists():
        backup_path = config_path.with_suffix(".bak")
        config_path.rename(backup_path)

    with open(config_path, "w") as f:
        yaml.dump(config_data, f)

    yield config_path

    # Restore backup
    if backup_path and backup_path.exists():
        backup_path.rename(config_path)
    elif config_path.exists():
        config_path.unlink()

@pytest.fixture
def clean_loggers():
    """Reset logger state before and after test."""
    _configured_loggers.clear()
    yield
    _configured_loggers.clear()

def test_setup_logging_creates_file(clean_loggers, tmp_path):
    """Test that setup_logging creates the log file and directory."""
    log_file = str(tmp_path / "subdir" / "output.log")
    logger = setup_logging(
        logger_name="test_logger_1",
        log_file=log_file,
        level="INFO"
    )
    
    assert logger is not None
    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.INFO
    assert Path(log_file).exists()

def test_setup_logging_uses_config(temp_config_file, clean_loggers):
    """Test that setup_logging respects config.yaml settings."""
    # Reset to ensure it picks up the new config
    logger = setup_logging(logger_name="test_logger_2")
    
    # The config specifies DEBUG level
    assert logger.level == logging.DEBUG
    
    # Check if file handler exists
    handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(handlers) > 0
    assert "test.log" in handlers[0].baseFilename

def test_log_quality_warning(clean_loggers, tmp_path):
    """Test that log_quality_warning writes to the log file."""
    log_file = str(tmp_path / "warning_test.log")
    setup_logging(
        logger_name="test_logger_3",
        log_file=log_file,
        level="WARNING"
    )
    
    log_quality_warning("Simulated signal loss", source="preprocessing")
    
    with open(log_file, "r") as f:
        content = f.read()
    
    assert "DATA QUALITY WARNING" in content
    assert "Simulated signal loss" in content
    assert "preprocessing" in content

def test_log_exclusion_count(clean_loggers, tmp_path):
    """Test that log_exclusion_count records counts correctly."""
    log_file = str(tmp_path / "exclusion_test.log")
    setup_logging(
        logger_name="test_logger_4",
        log_file=log_file,
        level="INFO"
    )
    
    log_exclusion_count(5, reason=">20% data loss", source="filtering")
    
    with open(log_file, "r") as f:
        content = f.read()
    
    assert "EXCLUSION COUNT" in content
    assert "5" in content
    assert ">20% data loss" in content

def test_log_pipeline_status(clean_loggers, tmp_path):
    """Test pipeline status logging."""
    log_file = str(tmp_path / "status_test.log")
    setup_logging(
        logger_name="test_logger_5",
        log_file=log_file,
        level="INFO"
    )
    
    log_pipeline_status("regression", "COMPLETED", details="R-squared=0.45")
    
    with open(log_file, "r") as f:
        content = f.read()
    
    assert "PIPELINE" in content
    assert "REGRESSION" in content
    assert "COMPLETED" in content
    assert "R-squared=0.45" in content

def test_no_duplicate_handlers(clean_loggers, tmp_path):
    """Test that calling setup_logging multiple times doesn't duplicate handlers."""
    log_file = str(tmp_path / "dup_test.log")
    
    logger = setup_logging(
        logger_name="test_logger_6",
        log_file=log_file,
        level="INFO"
    )
    initial_count = len(logger.handlers)
    
    # Call again with same name
    logger2 = setup_logging(
        logger_name="test_logger_6",
        log_file=log_file,
        level="INFO"
    )
    final_count = len(logger2.handlers)
    
    assert initial_count == final_count
    # Should have 2 handlers: file + console
    assert final_count == 2

def test_missing_config_falls_back_to_defaults(clean_loggers, tmp_path, monkeypatch):
    """Test fallback to defaults when config.yaml is missing."""
    # Temporarily move config out of the way
    config_path = Path(__file__).parent.parent.parent / "code" / "config.yaml"
    backup_path = None
    if config_path.exists():
        backup_path = config_path.with_suffix(".bak")
        config_path.rename(backup_path)
    
    try:
        log_file = str(tmp_path / "default_test.log")
        logger = setup_logging(
            logger_name="test_logger_7",
            log_file=log_file,
            level="INFO"
        )
        
        # Verify defaults were used (INFO level)
        assert logger.level == logging.INFO
        
        # Verify file was created
        assert Path(log_file).exists()
    finally:
        # Restore config
        if backup_path and backup_path.exists():
            backup_path.rename(config_path)