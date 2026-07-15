import json
import os
import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# Mock the logger and config to avoid dependency issues during unit testing
# We will test the logic of the status_manager directly by manipulating the file system

from state.status_manager import (
    ensure_state_dir,
    load_status,
    save_status,
    update_task_status,
    update_execution_summary,
    update_memory_logs,
    update_final_report_path,
    run_status_update_pipeline,
    STATUS_FILE,
    STATE_DIR
)

@pytest.fixture
def temp_state_dir():
    """Create a temporary directory for testing state file operations."""
    temp_dir = tempfile.mkdtemp()
    original_state_dir = STATE_DIR
    original_status_file = STATUS_FILE
    
    # Monkey patch the global paths to use the temp directory
    import state.status_manager as sm
    sm.STATE_DIR = Path(temp_dir)
    sm.STATUS_FILE = Path(temp_dir) / "execution_status.json"
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)
    # Restore original paths (optional if tests are isolated, but good practice)
    sm.STATE_DIR = original_state_dir
    sm.STATUS_FILE = original_status_file

def test_ensure_state_dir(temp_state_dir):
    """Test that ensure_state_dir creates the directory if it doesn't exist."""
    new_dir = Path(temp_state_dir) / "new_subdir"
    # The function should create the directory if it doesn't exist
    # Since ensure_state_dir operates on the global STATE_DIR which is mocked,
    # we verify the directory exists after calling it.
    # Actually, ensure_state_dir just ensures STATE_DIR exists.
    # Let's test that it creates the directory if missing.
    shutil.rmtree(temp_state_dir) # Remove to simulate non-existence
    ensure_state_dir()
    assert Path(temp_state_dir).exists()

def test_load_status_empty(temp_state_dir):
    """Test loading status when file doesn't exist."""
    status = load_status()
    assert status["pipeline_version"] == "1.0"
    assert status["tasks"] == {}
    assert status["last_updated"] is None
    assert status["memory_logs"] == []
    assert status["final_report_path"] is None

def test_save_and_load_status(temp_state_dir):
    """Test saving and loading status data."""
    test_data = {
        "pipeline_version": "1.0",
        "tasks": {"T001": {"status": "completed"}},
        "last_updated": "2023-01-01T00:00:00",
        "memory_logs": [],
        "final_report_path": None
    }
    save_status(test_data)
    
    loaded_data = load_status()
    assert loaded_data["tasks"]["T001"]["status"] == "completed"
    assert loaded_data["last_updated"] == "2023-01-01T00:00:00"

def test_update_task_status(temp_state_dir):
    """Test updating a specific task status."""
    update_task_status("T041", "completed", "Test details")
    
    status = load_status()
    assert "T041" in status["tasks"]
    assert status["tasks"]["T041"]["status"] == "completed"
    assert status["tasks"]["T041"]["details"] == "Test details"
    assert "timestamp" in status["tasks"]["T041"]

def test_update_execution_summary(temp_state_dir):
    """Test updating execution summary."""
    update_execution_summary(
        total_tasks=10,
        completed_tasks=8,
        failed_tasks=2,
        execution_time_seconds=100.5
    )
    
    status = load_status()
    assert "summary" in status
    assert status["summary"]["total_tasks"] == 10
    assert status["summary"]["completed_tasks"] == 8
    assert status["summary"]["failed_tasks"] == 2
    assert status["summary"]["execution_time_seconds"] == 100.5
    assert status["summary"]["status"] == "completed_with_errors"

def test_update_final_report_path(temp_state_dir):
    """Test updating final report path."""
    test_path = "data/reports/final_report.pdf"
    update_final_report_path(test_path)
    
    status = load_status()
    assert status["final_report_path"] == test_path

def test_run_status_update_pipeline(temp_state_dir):
    """Test the full pipeline update."""
    run_status_update_pipeline(
        task_id="T041",
        task_status="completed",
        task_details="All good",
        report_path="data/report.html",
        total_tasks=5,
        completed_tasks=5,
        failed_tasks=0,
        execution_time=60.0
    )
    
    status = load_status()
    # Check task
    assert status["tasks"]["T041"]["status"] == "completed"
    # Check summary
    assert status["summary"]["total_tasks"] == 5
    assert status["summary"]["failed_tasks"] == 0
    # Check report path
    assert status["final_report_path"] == "data/report.html"
    # Check last updated exists
    assert status["last_updated"] is not None
