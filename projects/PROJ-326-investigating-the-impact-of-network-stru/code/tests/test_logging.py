"""
Tests for the logging infrastructure (T005).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add code to path if running from tests
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.utils.logging import (
    _load_existing_log,
    _save_log,
    log_run,
    log_metric,
    get_run_log,
    clear_run_log,
    _DATA_DIR,
    _LOG_FILE_PATH
)


@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file path for testing."""
    # Temporarily override the module-level paths
    original_log_path = _LOG_FILE_PATH
    original_data_dir = _DATA_DIR
    
    # We can't easily mock the module-level constants, so we test the functions
    # by manipulating the actual file if it exists, or using a temp file strategy
    # For this test, we will rely on the clear_run_log fixture to clean up.
    
    yield _LOG_FILE_PATH
    
    # Cleanup
    if _LOG_FILE_PATH.exists():
        _LOG_FILE_PATH.unlink()


def test_log_run_creates_entry(temp_log_file):
    """Test that log_run creates a new entry in the log file."""
    # Ensure clean state
    if _LOG_FILE_PATH.exists():
        _LOG_FILE_PATH.unlink()
        
    seed = 42
    params = {"alpha": 0.5, "beta": 1.0}
    metrics = {"duration": 1.23, "nodes": 100}
    run_id = "test_run_001"
    
    entry = log_run(seed=seed, parameters=params, metrics=metrics, run_id=run_id)
    
    # Verify returned entry
    assert entry["run_id"] == run_id
    assert entry["seed"] == seed
    assert entry["parameters"] == params
    assert entry["metrics"] == metrics
    assert "timestamp" in entry
    
    # Verify file exists and contains the entry
    assert _LOG_FILE_PATH.exists()
    log_data = _load_existing_log()
    assert len(log_data) == 1
    assert log_data[0]["run_id"] == run_id


def test_log_run_appends_entry(temp_log_file):
    """Test that log_run appends to existing entries."""
    # Ensure clean state
    if _LOG_FILE_PATH.exists():
        _LOG_FILE_PATH.unlink()
        
    # First run
    log_run(run_id="run_1", seed=1)
    # Second run
    log_run(run_id="run_2", seed=2)
    
    log_data = _load_existing_log()
    assert len(log_data) == 2
    assert log_data[0]["run_id"] == "run_1"
    assert log_data[1]["run_id"] == "run_2"


def test_log_metric_updates_existing_run(temp_log_file):
    """Test that log_metric updates an existing run entry."""
    if _LOG_FILE_PATH.exists():
        _LOG_FILE_PATH.unlink()
        
    run_id = "test_run_metric"
    log_run(run_id=run_id, seed=99)
    
    # Add a metric
    updated_entry = log_metric("accuracy", 0.95, run_id=run_id)
    
    assert updated_entry["metrics"]["accuracy"] == 0.95
    assert updated_entry["run_id"] == run_id
    
    # Verify persistence
    log_data = _load_existing_log()
    assert log_data[0]["metrics"]["accuracy"] == 0.95


def test_log_metric_creates_new_run_if_not_found(temp_log_file):
    """Test that log_metric creates a new entry if run_id is not found."""
    if _LOG_FILE_PATH.exists():
        _LOG_FILE_PATH.unlink()
        
    # Log a metric for a non-existent run_id
    entry = log_metric("new_metric", 123, run_id="phantom_run", seed=7)
    
    log_data = _load_existing_log()
    assert len(log_data) == 1
    assert log_data[0]["run_id"] == "phantom_run"
    assert log_data[0]["metrics"]["new_metric"] == 123


def test_get_run_log_returns_all_entries(temp_log_file):
    """Test retrieval of the full log."""
    if _LOG_FILE_PATH.exists():
        _LOG_FILE_PATH.unlink()
        
    log_run(run_id="a")
    log_run(run_id="b")
    log_run(run_id="c")
    
    all_logs = get_run_log()
    assert len(all_logs) == 3
    ids = [e["run_id"] for e in all_logs]
    assert "a" in ids and "b" in ids and "c" in ids


def test_clear_run_log_deletes_file(temp_log_file):
    """Test that clear_run_log removes the file."""
    if _LOG_FILE_PATH.exists():
        _LOG_FILE_PATH.unlink()
        
    log_run(run_id="to_be_deleted")
    assert _LOG_FILE_PATH.exists()
    
    clear_run_log()
    assert not _LOG_FILE_PATH.exists()


def test_log_run_auto_generates_run_id(temp_log_file):
    """Test that run_id is auto-generated if not provided."""
    if _LOG_FILE_PATH.exists():
        _LOG_FILE_PATH.unlink()
        
    entry = log_run(seed=123)
    
    assert entry["run_id"].startswith("run_")
    assert len(entry["run_id"]) > 5
    assert entry["seed"] == 123
