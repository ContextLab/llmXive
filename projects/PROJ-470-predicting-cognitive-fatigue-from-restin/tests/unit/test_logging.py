"""
Unit tests for the logging infrastructure.
"""
import os
import sys
import csv
import pytest
from pathlib import Path
import shutil

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.logging import (
    get_logger, 
    log_participant_exclusion, 
    log_artifact_rejection, 
    save_rejection_summary, 
    get_rejection_counts,
    save_exclusion_log_csv
)

@pytest.fixture(autouse=True)
def reset_logger_state():
    """Reset the global logger state before each test."""
    import utils.logging
    utils.logging._logger = None
    # Clean up logs directory if it exists from previous runs
    logs_dir = Path("logs")
    if logs_dir.exists():
        shutil.rmtree(logs_dir)
    yield
    # Cleanup after test
    if logs_dir.exists():
        shutil.rmtree(logs_dir)

def test_get_logger_initialization():
    """Test that the logger is created and configured correctly."""
    logger = get_logger()
    assert logger is not None
    assert logger.name == "eeg_pipeline"
    assert hasattr(logger, 'rejection_log')
    assert hasattr(logger, 'exclusion_log')
    assert isinstance(logger.rejection_log, list)
    assert isinstance(logger.exclusion_log, list)

def test_log_participant_exclusion():
    """Test logging a participant exclusion."""
    log_participant_exclusion("P001", "amplitude > 100uV", "preprocessing")
    
    logger = get_logger()
    assert len(logger.exclusion_log) == 1
    
    record = logger.exclusion_log[0]
    assert record["participant_id"] == "P001"
    assert record["reason"] == "amplitude > 100uV"
    assert record["stage"] == "preprocessing"
    assert "timestamp" in record

def test_log_artifact_rejection():
    """Test logging an artifact rejection."""
    log_artifact_rejection("S001", "high amplitude", "amplitude", threshold=100.0, measured_value=150.0)
    
    logger = get_logger()
    assert len(logger.rejection_log) == 1
    
    record = logger.rejection_log[0]
    assert record["segment_id"] == "S001"
    assert record["reason"] == "high amplitude"
    assert record["artifact_type"] == "amplitude"
    assert record["threshold"] == 100.0
    assert record["measured_value"] == 150.0

def test_save_exclusion_log_csv():
    """Test that exclusion log is saved to CSV with correct format."""
    # Log some exclusions
    log_participant_exclusion("P001", "amplitude > 100uV", "preprocessing")
    log_participant_exclusion("P002", "segment < 120s", "preprocessing")
    log_participant_exclusion("P003", "line noise", "preprocessing")
    
    # Save to CSV
    save_exclusion_log_csv("logs/exclusion_log.csv")
    
    # Verify file exists
    csv_path = Path("logs/exclusion_log.csv")
    assert csv_path.exists()
    
    # Verify content
    with open(csv_path, mode='r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        assert len(rows) == 3
        
        # Check headers
        assert set(reader.fieldnames) == {"participant_id", "reason", "timestamp"}
        
        # Check data
        assert rows[0]["participant_id"] == "P001"
        assert rows[0]["reason"] == "amplitude > 100uV"
        
        assert rows[1]["participant_id"] == "P002"
        assert rows[1]["reason"] == "segment < 120s"
        
        assert rows[2]["participant_id"] == "P003"
        assert rows[2]["reason"] == "line noise"

def test_get_rejection_counts():
    """Test counting exclusions and rejections by reason."""
    log_participant_exclusion("P001", "amplitude > 100uV", "preprocessing")
    log_participant_exclusion("P002", "amplitude > 100uV", "preprocessing")
    log_participant_exclusion("P003", "segment < 120s", "preprocessing")
    
    log_artifact_rejection("S001", "high amplitude", "amplitude")
    log_artifact_rejection("S002", "high amplitude", "amplitude")
    
    counts = get_rejection_counts()
    
    assert counts["exclusions"]["amplitude > 100uV"] == 2
    assert counts["exclusions"]["segment < 120s"] == 1
    
    assert counts["rejections"]["high amplitude"] == 2

def test_save_rejection_summary():
    """Test saving rejection summary to JSON."""
    log_participant_exclusion("P001", "amplitude > 100uV", "preprocessing")
    log_artifact_rejection("S001", "high amplitude", "amplitude")
    
    save_rejection_summary("logs/rejection_summary.json")
    
    json_path = Path("logs/rejection_summary.json")
    assert json_path.exists()
    
    import json
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    assert "exclusions" in data
    assert "rejections" in data
    assert "generated_at" in data
    assert len(data["exclusions"]) == 1
    assert len(data["rejections"]) == 1
