"""
Unit tests for the logging infrastructure.

Tests verify that:
1. Log files are created in the correct location
2. Exclusion logging works correctly
3. Pipeline step logging works correctly
4. Log formats are correct
"""
import os
import logging
import pytest
from pathlib import Path
import shutil
from datetime import datetime

# Import the module under test
from logging_config import (
    get_logger,
    log_exclusion,
    log_pipeline_step,
    LOG_DIR,
    setup_logging
)

@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path):
    """Set up a temporary directory for logging during tests."""
    # Save original log dir
    original_log_dir = LOG_DIR
    
    # Create temp log dir
    test_log_dir = tmp_path / "test_logs"
    test_log_dir.mkdir(parents=True, exist_ok=True)
    
    # Temporarily override LOG_DIR by patching the module
    import logging_config
    logging_config.LOG_DIR = test_log_dir
    logging_config.LOG_FILE = test_log_dir / "pipeline_test.log"
    
    # Re-setup logging to use temp dir
    logging_config.setup_logging()
    
    yield test_log_dir
    
    # Restore original
    logging_config.LOG_DIR = original_log_dir
    logging_config.LOG_FILE = original_log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    # Re-setup with original
    setup_logging()

def test_log_directory_created(setup_test_environment):
    """Test that the log directory is created if it doesn't exist."""
    log_dir = setup_test_environment
    assert log_dir.exists(), "Log directory should be created"
    assert log_dir.is_dir(), "Log directory should be a directory"

def test_log_file_created(setup_test_environment):
    """Test that a log file is created when logging is initialized."""
    log_dir = setup_test_environment
    log_files = list(log_dir.glob("pipeline_*.log"))
    assert len(log_files) > 0, "At least one log file should be created"

def test_get_logger_returns_logger():
    """Test that get_logger returns a valid Logger instance."""
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger), "get_logger should return a Logger instance"
    assert logger.name == "test_module", "Logger name should match the provided name"

def test_log_exclusion(setup_test_environment):
    """Test that exclusion logging creates the correct log entry."""
    log_exclusion(
        reason="Straight-lining detected",
        entity_type="Participant",
        entity_id="P-TEST1234",
        context="Task T016"
    )
    
    exclusions_log = setup_test_environment / "exclusions.log"
    assert exclusions_log.exists(), "Exclusions log file should be created"
    
    content = exclusions_log.read_text()
    assert "EXCLUDED" in content, "Exclusion log should contain 'EXCLUDED'"
    assert "Participant" in content, "Exclusion log should mention entity type"
    assert "P-TEST1234" in content, "Exclusion log should mention entity ID"
    assert "Straight-lining detected" in content, "Exclusion log should mention reason"

def test_log_pipeline_step_started(setup_test_environment):
    """Test logging a pipeline step start."""
    log_pipeline_step("Test Step", "STARTED", "Starting test")
    
    log_file = setup_test_environment / "pipeline_test.log"
    content = log_file.read_text()
    
    assert "STEP: Test Step" in content, "Log should contain step name"
    assert "STATUS: STARTED" in content, "Log should contain start status"

def test_log_pipeline_step_completed(setup_test_environment):
    """Test logging a pipeline step completion."""
    log_pipeline_step("Test Step", "COMPLETED", "Finished test")
    
    log_file = setup_test_environment / "pipeline_test.log"
    content = log_file.read_text()
    
    assert "STATUS: COMPLETED" in content, "Log should contain completion status"

def test_log_pipeline_step_failed(setup_test_environment):
    """Test logging a pipeline step failure."""
    log_pipeline_step("Test Step", "FAILED", "Error occurred")
    
    log_file = setup_test_environment / "pipeline_test.log"
    content = log_file.read_text()
    
    assert "STATUS: FAILED" in content, "Log should contain failure status"
    # Check that the logger level is appropriate for errors
    logger = get_logger("pipeline.steps")
    assert logger.isEnabledFor(logging.ERROR), "Logger should be enabled for ERROR level"

def test_exclusion_log_format(setup_test_environment):
    """Test that exclusion logs have the correct format."""
    log_exclusion(
        reason="Missing data",
        entity_type="Stimulus",
        entity_id="S-001"
    )
    
    exclusions_log = setup_test_environment / "exclusions.log"
    content = exclusions_log.read_text()
    
    # Check for expected pipe-separated format
    lines = content.strip().split('\n')
    assert len(lines) > 0, "Exclusions log should have content"
    
    # Each line should contain pipe separators
    for line in lines:
        assert "|" in line, f"Exclusion log line should be pipe-separated: {line}"

def test_multiple_exclusions_logged(setup_test_environment):
    """Test that multiple exclusions are all logged."""
    log_exclusion("Reason 1", "Participant", "P-1")
    log_exclusion("Reason 2", "Participant", "P-2")
    log_exclusion("Reason 3", "Participant", "P-3")
    
    exclusions_log = setup_test_environment / "exclusions.log"
    content = exclusions_log.read_text()
    
    assert content.count("EXCLUDED") == 3, "All three exclusions should be logged"
    assert "P-1" in content and "P-2" in content and "P-3" in content
