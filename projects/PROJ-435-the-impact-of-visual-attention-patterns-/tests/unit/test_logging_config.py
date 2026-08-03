import pytest
import os
import json
from pathlib import Path
import logging
import shutil

from code.utils.logging_config import (
    setup_logging,
    get_quality_logger,
    get_exclusion_logger,
    get_pipeline_logger,
    log_data_quality_warning,
    log_exclusion,
    log_pipeline_progress,
    _append_to_json_state,
    _update_exclusion_counts,
    LOG_DIR,
    EXCLUSION_LOG_FILE,
    QUALITY_WARNING_LOG_FILE,
    PIPELINE_PROGRESS_LOG_FILE,
)

@pytest.fixture(autouse=True)
def setup_and_teardown_logging():
    """
    Setup: Create necessary directories and clear existing log files.
    Teardown: Clean up log files and directories after test.
    """
    # Setup
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    for file in [EXCLUSION_LOG_FILE, QUALITY_WARNING_LOG_FILE, PIPELINE_PROGRESS_LOG_FILE]:
        if Path(file).exists():
            Path(file).unlink()
    if Path("state/exclusion_counts_summary.json").exists():
        Path("state/exclusion_counts_summary.json").unlink()

    # Run test
    yield

    # Teardown
    if LOG_DIR.exists():
        shutil.rmtree(LOG_DIR)
    for file in [EXCLUSION_LOG_FILE, QUALITY_WARNING_LOG_FILE, PIPELINE_PROGRESS_LOG_FILE]:
        if Path(file).exists():
            Path(file).unlink()
    if Path("state/exclusion_counts_summary.json").exists():
        Path("state/exclusion_counts_summary.json").unlink()

def test_setup_logging_creates_handlers():
    """Test that setup_logging creates console and file handlers."""
    setup_logging(log_level="INFO")
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) >= 2  # Console + File
    assert any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers)
    assert any(isinstance(h, logging.FileHandler) for h in root_logger.handlers)

def test_get_quality_logger_returns_configured_logger():
    """Test that get_quality_logger returns a configured logger with file handler."""
    logger = get_quality_logger()
    assert logger.name == "quality"
    assert logger.level == logging.WARNING
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.FileHandler)

def test_get_exclusion_logger_returns_configured_logger():
    """Test that get_exclusion_logger returns a configured logger with file handler."""
    logger = get_exclusion_logger()
    assert logger.name == "exclusion"
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.FileHandler)

def test_get_pipeline_logger_returns_configured_logger():
    """Test that get_pipeline_logger returns a configured logger with file handler."""
    logger = get_pipeline_logger()
    assert logger.name == "pipeline"
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.FileHandler)

def test_log_data_quality_warning_creates_json_file():
    """Test that log_data_quality_warning creates and appends to JSON state file."""
    log_data_quality_warning("Test warning", context={"test": "value"})
    assert Path(QUALITY_WARNING_LOG_FILE).exists()
    with open(QUALITY_WARNING_LOG_FILE, "r") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["message"] == "Test warning"
    assert data[0]["context"] == {"test": "value"}

def test_log_exclusion_updates_json_file_and_counts():
    """Test that log_exclusion creates JSON entry and updates exclusion counts."""
    log_exclusion("data_loss > 20", "participant", "P001")
    
    # Check exclusion log file
    assert Path(EXCLUSION_LOG_FILE).exists()
    with open(EXCLUSION_LOG_FILE, "r") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["reason"] == "data_loss > 20"
    assert data[0]["entity_type"] == "participant"
    assert data[0]["entity_id"] == "P001"

    # Check counts summary file
    assert Path("state/exclusion_counts_summary.json").exists()
    with open("state/exclusion_counts_summary.json", "r") as f:
        counts = json.load(f)
    assert "counts" in counts
    assert "participant_data_loss > 20" in counts["counts"]
    assert counts["counts"]["participant_data_loss > 20"] == 1

def test_log_pipeline_progress_creates_json_file():
    """Test that log_pipeline_progress creates and appends to JSON state file."""
    log_pipeline_progress("preprocessing", "completed", "Done", {"rows": 100})
    assert Path(PIPELINE_PROGRESS_LOG_FILE).exists()
    with open(PIPELINE_PROGRESS_LOG_FILE, "r") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["stage"] == "preprocessing"
    assert data[0]["status"] == "completed"
    assert data[0]["metrics"] == {"rows": 100}

def test_multiple_exclusions_increment_counts():
    """Test that multiple exclusions with same reason increment the count."""
    log_exclusion("data_loss > 20", "participant", "P001")
    log_exclusion("data_loss > 20", "participant", "P002")
    
    with open("state/exclusion_counts_summary.json", "r") as f:
        counts = json.load(f)
    assert counts["counts"]["participant_data_loss > 20"] == 2

def test_log_exclusion_different_reasons_separate_counts():
    """Test that different exclusion reasons have separate counts."""
    log_exclusion("data_loss > 20", "participant", "P001")
    log_exclusion("missing_roi", "participant", "P002")
    
    with open("state/exclusion_counts_summary.json", "r") as f:
        counts = json.load(f)
    assert counts["counts"]["participant_data_loss > 20"] == 1
    assert counts["counts"]["participant_missing_roi"] == 1