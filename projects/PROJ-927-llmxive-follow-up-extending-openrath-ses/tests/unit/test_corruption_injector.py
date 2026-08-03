"""Unit tests for the corruption_injector (T023, T018)."""
import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest

from simulators.corruption_injector import CorruptionInjector

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure."""
    root = tempfile.mkdtemp()
    # Create mock log directory
    log_dir = Path(root) / "data" / "processed" / "corrupted_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a mock log file
    log_file = log_dir / "wf_001_log.json"
    log_file.write_text(json.dumps({
        "workflow_id": "wf_001",
        "steps": [
            {"id": 1, "data": "keep"},
            {"id": 2, "data": "remove"},
            {"id": 3, "data": "modify"}
        ]
    }))
    
    original_cwd = os.getcwd()
    os.chdir(root)
    yield root
    os.chdir(original_cwd)
    shutil.rmtree(root)

def test_corruption_injector_delete(temp_project_root):
    """Test deleting a log entry."""
    injector = CorruptionInjector(corruption_rate=1.0) # 100% rate for testing
    log_path = Path(temp_project_root) / "data" / "processed" / "corrupted_logs" / "wf_001_log.json"
    
    # Mock the logic to force deletion of step 2
    injector.corrupt_log(str(log_path), action="delete", target_index=1)
    
    with open(log_path) as f:
        data = json.load(f)
    
    # Step 2 should be gone
    assert len(data["steps"]) == 2
    assert data["steps"][0]["id"] == 1
    assert data["steps"][1]["id"] == 3

def test_corruption_injector_modify(temp_project_root):
    """Test modifying a log entry."""
    injector = CorruptionInjector(corruption_rate=1.0)
    log_path = Path(temp_project_root) / "data" / "processed" / "corrupted_logs" / "wf_001_log.json"
    
    injector.corrupt_log(str(log_path), action="modify", target_index=2, new_data="corrupted")
    
    with open(log_path) as f:
        data = json.load(f)
    
    assert data["steps"][2]["data"] == "corrupted"

def test_corruption_injector_no_corruption(temp_project_root):
    """Test that with 0 rate, no corruption happens."""
    injector = CorruptionInjector(corruption_rate=0.0)
    log_path = Path(temp_project_root) / "data" / "processed" / "corrupted_logs" / "wf_001_log.json"
    original_content = log_path.read_text()
    
    injector.inject_corruption() # Should do nothing effectively
    
    assert log_path.read_text() == original_content
