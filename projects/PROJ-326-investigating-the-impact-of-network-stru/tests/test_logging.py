"""
Tests for the logging infrastructure (T005).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from code.src.utils.logging import (
    log_run,
    log_metric,
    get_run_log,
    clear_run_log,
    _load_existing_log,
    _save_log,
    _LOG_FILE_PATH,
    _DATA_DIR
)


@pytest.fixture
def clean_log_file(tmp_path, monkeypatch):
    """
    Fixture to isolate logging tests to a temporary directory.
    Replaces the global _LOG_FILE_PATH and _DATA_DIR with temp equivalents.
    """
    # Create a temp directory structure
    temp_data = tmp_path / "data"
    temp_data.mkdir()
    temp_log = temp_data / "run_log.json"
    
    # Monkeypatch the module's global paths
    import code.src.utils.logging as logging_module
    original_log_path = logging_module._LOG_FILE_PATH
    original_data_dir = logging_module._DATA_DIR
    
    logging_module._LOG_FILE_PATH = temp_log
    logging_module._DATA_DIR = temp_data
    
    yield temp_log
    
    # Restore original paths
    logging_module._LOG_FILE_PATH = original_log_path
    logging_module._DATA_DIR = original_data_dir


def test_log_run_creates_entry(clean_log_file):
    """Test that log_run creates a new entry in the JSON file."""
    seed = 42
    params = {"alpha": 0.5}
    metrics = {"duration": 1.23}
    
    entry = log_run(seed=seed, parameters=params, metrics=metrics)
    
    # Check returned entry
    assert entry["seed"] == seed
    assert entry["parameters"] == params
    assert entry["metrics"] == metrics
    assert "run_id" in entry
    assert "timestamp" in entry
    
    # Check file on disk
    assert clean_log_file.exists()
    with open(clean_log_file, "r") as f:
        data = json.load(f)
    
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["seed"] == seed


def test_log_run_appends_entry(clean_log_file):
    """Test that subsequent log_run calls append to the list."""
    log_run(seed=1)
    log_run(seed=2)
    
    with open(clean_log_file, "r") as f:
        data = json.load(f)
    
    assert len(data) == 2
    assert data[0]["seed"] == 1
    assert data[1]["seed"] == 2


def test_log_metric_updates_existing_run(clean_log_file):
    """Test that log_metric updates the metrics dict of an existing run."""
    run_id = "test_run_001"
    log_run(run_id=run_id, seed=99)
    
    log_metric("accuracy", 0.95, run_id=run_id)
    
    entries = get_run_log()
    assert len(entries) == 1
    assert entries[0]["metrics"]["accuracy"] == 0.95


def test_log_metric_creates_new_entry_if_run_id_not_found(clean_log_file):
    """Test that log_metric creates a new entry if run_id is provided but not found."""
    # Log a run with a specific ID
    log_run(run_id="run_A", seed=1)
    
    # Log a metric for a DIFFERENT ID
    log_metric("loss", 0.5, run_id="run_B", seed=2)
    
    entries = get_run_log()
    assert len(entries) == 2
    
    run_a = next(e for e in entries if e["run_id"] == "run_A")
    run_b = next(e for e in entries if e["run_id"] == "run_B")
    
    assert "loss" not in run_a["metrics"]
    assert run_b["metrics"]["loss"] == 0.5


def test_log_metric_appends_to_latest_if_no_run_id(clean_log_file):
    """Test that log_metric appends to the last entry if run_id is None."""
    log_run(seed=1)
    log_run(seed=2) # This becomes the latest
    
    log_metric("val_loss", 0.3)
    
    entries = get_run_log()
    # Should still be 2 entries
    assert len(entries) == 2
    # The last one should have the metric
    assert entries[1]["metrics"]["val_loss"] == 0.3


def test_get_run_log(clean_log_file):
    """Test retrieving the full log."""
    log_run(seed=1)
    log_run(seed=2)
    
    log = get_run_log()
    assert len(log) == 2


def test_clear_run_log(clean_log_file):
    """Test that clear_run_log deletes the file."""
    log_run(seed=1)
    assert clean_log_file.exists()
    
    clear_run_log()
    assert not clean_log_file.exists()


def test_empty_log_file_handling(clean_log_file):
    """Test behavior when log file exists but is empty."""
    # Create empty file
    clean_log_file.touch()
    
    log = _load_existing_log()
    assert log == []


def test_invalid_json_handling(clean_log_file):
    """Test behavior when log file contains invalid JSON."""
    with open(clean_log_file, "w") as f:
        f.write("{ invalid json }")
    
    log = _load_existing_log()
    # Should return empty list on error
    assert log == []
