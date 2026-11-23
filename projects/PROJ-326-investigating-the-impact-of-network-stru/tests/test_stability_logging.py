"""
Unit tests for the stability logging infrastructure (T026b).
Verifies that runtime_duration_seconds is correctly logged to data/run_log.json.
"""
import json
import os
import sys
import time
import pytest
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.simulation.stability import log_simulation_runtime
from code.src.utils.logging import get_run_log, _ensure_log_file, _save_log
from code.src.utils.config import load_config

@pytest.fixture
def clean_log_file(tmp_path):
    """Fixture to provide a clean log file for testing."""
    # Backup original if exists
    original_path = Path("data/run_log.json")
    backup = None
    if original_path.exists():
        backup = original_path.read_text()

    # Use temp path for testing
    test_log_path = tmp_path / "run_log.json"
    # We need to patch the logging module to use this temp path
    # For simplicity, we'll just clear the real one and restore after
    original_path.parent.mkdir(parents=True, exist_ok=True)
    original_path.write_text("[]")

    yield original_path

    # Restore original
    if backup:
        original_path.write_text(backup)
    else:
        original_path.unlink(missing_ok=True)

def test_log_simulation_runtime_creates_entry(clean_log_file):
    """Test that log_simulation_runtime creates a valid entry in run_log.json."""
    config = load_config()
    run_id = "test_run_123"
    start_time = time.time() - 1.5  # Simulate 1.5 seconds ago

    log_simulation_runtime(run_id, start_time, config)

    log_data = get_run_log()

    assert len(log_data) >= 1, "Log should have at least one entry"

    # Find the entry for our run
    entry = None
    for item in log_data:
        if item.get("run_id") == run_id and item.get("event_type") == "simulation_runtime":
            entry = item
            break

    assert entry is not None, "Could not find the logged entry"

    # Verify schema
    assert "duration_seconds" in entry, "Entry must contain duration_seconds"
    assert isinstance(entry["duration_seconds"], float), "duration_seconds must be a float"
    assert entry["duration_seconds"] > 1.0, "Duration should be at least 1.5 seconds (with tolerance)"
    assert entry["duration_seconds"] < 5.0, "Duration should be reasonable"

def test_log_simulation_runtime_multiple_runs(clean_log_file):
    """Test that multiple runs are logged correctly."""
    config = load_config()
    run_id_1 = "run_A"
    run_id_2 = "run_B"
    start_time_1 = time.time() - 1.0
    start_time_2 = time.time() - 2.0

    log_simulation_runtime(run_id_1, start_time_1, config)
    log_simulation_runtime(run_id_2, start_time_2, config)

    log_data = get_run_log()

    # Count entries for our runs
    entries = [
        item for item in log_data
        if item.get("event_type") == "simulation_runtime"
        and item.get("run_id") in [run_id_1, run_id_2]
    ]

    assert len(entries) == 2, "Should have 2 entries for our runs"

def test_log_simulation_runtime_creates_file_if_missing(tmp_path):
    """Test that the function creates the log file if it doesn't exist."""
    # Remove the file if it exists
    log_path = Path("data/run_log.json")
    was_existing = log_path.exists()
    if was_existing:
        content_backup = log_path.read_text()
        log_path.unlink()

    try:
        config = load_config()
        run_id = "new_file_test"
        start_time = time.time() - 0.1

        # This should create the file
        log_simulation_runtime(run_id, start_time, config)

        assert log_path.exists(), "Log file should be created"

        # Verify content
        with open(log_path, "r") as f:
            data = json.load(f)

        assert isinstance(data, list), "Log file should be a JSON array"
        assert len(data) == 1, "Should have one entry"
    finally:
        # Restore state
        if was_existing:
            log_path.write_text(content_backup)
        else:
            log_path.unlink(missing_ok=True)