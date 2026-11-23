"""Unit tests for the corruption_log_manager utility."""
import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest

from simulators.corruption_log_manager import (
    get_corruption_map_path,
    load_corruption_map,
    save_corruption_map,
    mark_workflow_corrupted,
    is_workflow_corrupted,
    get_corruption_details,
    clear_corruption_log
)
from config import PROCESSED_DATA_DIR

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure."""
    root = tempfile.mkdtemp()
    # Setup processed data dir
    processed_dir = Path(root) / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    original_cwd = os.getcwd()
    os.chdir(root)
    yield root
    os.chdir(original_cwd)
    shutil.rmtree(root)

def test_get_corruption_map_path(temp_project_root):
    """Test that the corruption map path is correctly constructed."""
    path = get_corruption_map_path()
    assert isinstance(path, str)
    assert "corruption_map.json" in path
    assert os.path.dirname(path) == str(Path(temp_project_root) / "data" / "processed")

def test_load_corruption_map_empty(temp_project_root):
    """Test loading a non-existent corruption map returns empty dict."""
    # Ensure file doesn't exist
    map_path = get_corruption_map_path()
    if os.path.exists(map_path):
        os.remove(map_path)
    
    result = load_corruption_map()
    assert result == {}

def test_load_corruption_map_exists(temp_project_root):
    """Test loading an existing corruption map."""
    map_path = get_corruption_map_path()
    test_data = {"wf_001": {"status": "corrupted", "details": ["node_1"]}}
    save_corruption_map(test_data)
    
    result = load_corruption_map()
    assert result == test_data

def test_mark_workflow_corrupted(temp_project_root):
    """Test marking a workflow as corrupted."""
    wf_id = "wf_test_123"
    details = ["missing_node", "corrupted_output"]
    
    mark_workflow_corrupted(wf_id, details)
    
    map_data = load_corruption_map()
    assert wf_id in map_data
    assert map_data[wf_id]["status"] == "corrupted"
    assert map_data[wf_id]["details"] == details

def test_is_workflow_corrupted(temp_project_root):
    """Test checking if a workflow is corrupted."""
    wf_id = "wf_check_456"
    assert not is_workflow_corrupted(wf_id)
    
    mark_workflow_corrupted(wf_id, ["test"])
    assert is_workflow_corrupted(wf_id)
    
    # Check a non-existent one
    assert not is_workflow_corrupted("wf_non_existent")

def test_get_corruption_details(temp_project_root):
    """Test retrieving corruption details."""
    wf_id = "wf_details_789"
    expected_details = ["detail_a", "detail_b"]
    
    mark_workflow_corrupted(wf_id, expected_details)
    details = get_corruption_details(wf_id)
    
    assert details == expected_details
    assert get_corruption_details("wf_fake") is None

def test_clear_corruption_log(temp_project_root):
    """Test clearing the entire corruption log."""
    mark_workflow_corrupted("wf_1", ["x"])
    mark_workflow_corrupted("wf_2", ["y"])
    
    assert len(load_corruption_map()) == 2
    
    clear_corruption_log()
    assert load_corruption_map() == {}
