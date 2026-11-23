"""
Unit tests for the validation and logging infrastructure (T006a).
"""
import json
import os
import time
import pytest
from pathlib import Path
import tempfile
import shutil

# Import from the project
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from code.validation import RuntimeTracker, update_pipeline_log, validate_data_integrity

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def tracker_with_temp_log(temp_log_dir):
    """Create a RuntimeTracker pointing to a temp log file."""
    log_path = Path(temp_log_dir) / "pipeline_log.json"
    tracker = RuntimeTracker(log_path=log_path)
    return tracker, log_path

def test_tracker_initialization(tracker_with_temp_log):
    """Test that the tracker initializes the log file correctly."""
    tracker, log_path = tracker_with_temp_log
    assert not log_path.exists()
    
    tracker._ensure_log_exists()
    assert log_path.exists()
    
    with open(log_path, 'r') as f:
        data = json.load(f)
    
    assert "stages" in data
    assert data["stages"] == []
    assert data["total_elapsed_seconds"] == 0.0

def test_start_and_stop(tracker_with_temp_log):
    """Test starting and stopping the timer."""
    tracker, log_path = tracker_with_temp_log
    tracker._ensure_log_exists() # Ensure file exists first

    tracker.start()
    time.sleep(0.1) # Sleep to ensure some time passes
    duration = tracker.stop("test_stage")

    assert duration >= 0.1
    
    with open(log_path, 'r') as f:
        data = json.load(f)
    
    assert len(data["stages"]) == 1
    assert data["stages"][0]["name"] == "test_stage"
    assert data["stages"][0]["duration_seconds"] >= 0.1
    assert data["total_elapsed_seconds"] >= 0.1

def test_multiple_stages(tracker_with_temp_log):
    """Test tracking multiple stages."""
    tracker, log_path = tracker_with_temp_log
    tracker._ensure_log_exists()

    tracker.start()
    time.sleep(0.05)
    tracker.stop("stage_1")

    tracker.start()
    time.sleep(0.05)
    tracker.stop("stage_2")

    with open(log_path, 'r') as f:
        data = json.load(f)
    
    assert len(data["stages"]) == 2
    assert data["stages"][0]["name"] == "stage_1"
    assert data["stages"][1]["name"] == "stage_2"
    assert data["total_elapsed_seconds"] >= 0.1

def test_check_limit(tracker_with_temp_log):
    """Test the time limit check."""
    tracker, log_path = tracker_with_temp_log
    tracker._ensure_log_exists()
    
    # Set a very low limit for testing
    original_limit = tracker.MAX_RUNTIME_SECONDS if hasattr(tracker, 'MAX_RUNTIME_SECONDS') else 6*3600
    # We can't easily change the class constant in the instance, so we test logic directly
    # The check_limit method uses the class constant or a property. 
    # Since the class uses a module constant, we test the behavior by manually accumulating.
    
    # Simulate accumulated time > 6 hours (21600 seconds)
    tracker.elapsed_accumulated = 21601.0
    assert tracker.check_limit() is True

    tracker.elapsed_accumulated = 100.0
    assert tracker.check_limit() is False

def test_update_pipeline_log(tracker_with_temp_log):
    """Test the update_pipeline_log helper."""
    tracker, log_path = tracker_with_temp_log
    tracker._ensure_log_exists()

    update_pipeline_log("manual_stage", status="completed")

    with open(log_path, 'r') as f:
        data = json.load(f)
    
    assert len(data["stages"]) == 1
    assert data["stages"][0]["name"] == "manual_stage"
    assert data["stages"][0]["status"] == "completed"

def test_validate_data_integrity(tracker_with_temp_log):
    """Test the data integrity validator."""
    tracker, log_path = tracker_with_temp_log
    
    # Test non-existent file
    assert not validate_data_integrity(Path("/non/existent/file.txt"))
    
    # Test empty file
    empty_file = tracker.log_path.parent / "empty.txt"
    empty_file.touch()
    assert not validate_data_integrity(empty_file)
    
    # Test non-empty file
    non_empty_file = tracker.log_path.parent / "non_empty.txt"
    non_empty_file.write_text("content")
    assert validate_data_integrity(non_empty_file)

    # Cleanup
    empty_file.unlink()
    non_empty_file.unlink()
