import os
import json
import pytest
from pathlib import Path
import tempfile
import shutil

# Mock config for testing to avoid dependency on real paths if needed, 
# but we assume config.py is set up correctly.
# For this test, we will temporarily override PROCESSED_DATA_DIR in config if possible,
# or just test the logic assuming the path exists.

# Since we cannot easily mock the global config without importing it,
# we will test the functions that rely on the file system.

# We need to ensure the directory exists before testing.
# In a real test suite, we might use fixtures to create a temp dir.

from simulators.corruption_log_manager import (
    load_corruption_map,
    save_corruption_map,
    mark_workflow_corrupted,
    is_workflow_corrupted,
    get_corruption_details,
    clear_corruption_log,
    get_corruption_map_path
)
from config import PROCESSED_DATA_DIR, ensure_directories

@pytest.fixture
def clean_corruption_log():
    """Fixture to ensure a clean state before and after each test."""
    ensure_directories()
    # Clear before
    clear_corruption_log()
    yield
    # Clear after
    clear_corruption_log()

def test_load_empty_map(clean_corruption_log):
    data = load_corruption_map()
    assert "entries" in data
    assert data["entries"] == {}
    assert data["version"] == "1.0"

def test_mark_workflow_corrupted(clean_corruption_log):
    workflow_id = "test_wf_123"
    mark_workflow_corrupted(
        workflow_id=workflow_id,
        corruption_type="file_deleted",
        details={"file": "log_123.json"}
    )
    
    assert is_workflow_corrupted(workflow_id)
    
    details = get_corruption_details(workflow_id)
    assert details is not None
    assert details["corrupted"] is True
    assert details["corruption_type"] == "file_deleted"
    assert details["details"]["file"] == "log_123.json"

def test_mark_multiple_workflows(clean_corruption_log):
    wfs = ["wf_1", "wf_2", "wf_3"]
    for i, wid in enumerate(wfs):
        mark_workflow_corrupted(
            workflow_id=wid,
            corruption_type="field_modified",
            details={"index": i}
        )
    
    for wid in wfs:
        assert is_workflow_corrupted(wid)
    
    data = load_corruption_map()
    assert len(data["entries"]) == 3

def test_clear_corruption_log(clean_corruption_log):
    mark_workflow_corrupted("wf_x", "test", {})
    assert is_workflow_corrupted("wf_x")
    
    clear_corruption_log()
    assert not is_workflow_corrupted("wf_x")
    assert load_corruption_map()["entries"] == {}

def test_mark_workflow_without_details(clean_corruption_log):
    mark_workflow_corrupted("wf_no_details", "unknown")
    details = get_corruption_details("wf_no_details")
    assert details["details"] == {}

def test_corruption_map_file_exists(clean_corruption_log):
    mark_workflow_corrupted("wf_file_check", "test", {})
    path = get_corruption_map_path()
    assert path.exists()
    assert path.suffix == ".json"