import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest
import hashlib

# We need to mock the STATE_FILE path to use a temp directory
import src.utils.state_manager as sm_module

@pytest.fixture
def temp_state_dir():
    """Create a temporary directory to act as the state directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Patch the module constants
        original_dir = sm_module.STATE_DIR
        original_file = sm_module.STATE_FILE
        
        sm_module.STATE_DIR = tmp_path
        sm_module.STATE_FILE = tmp_path / f"{sm_module.PROJECT_ID}.yaml"
        
        yield tmp_path
        
        # Restore original paths
        sm_module.STATE_DIR = original_dir
        sm_module.STATE_FILE = original_file

def test_default_state_structure(temp_state_dir):
    state = sm_module.get_state()
    assert "project_id" in state
    assert state["project_id"] == sm_module.PROJECT_ID
    assert "created_at" in state
    assert "stages" in state
    assert "artifacts" in state

def test_compute_file_checksum(temp_state_dir):
    test_file = temp_state_dir / "test.txt"
    test_content = "Hello, World!"
    test_file.write_text(test_content)
    
    expected_hash = hashlib.sha256(test_content.encode()).hexdigest()
    actual_hash = sm_module.get_artifact_checksum(str(test_file))
    
    assert actual_hash == expected_hash

def test_compute_file_checksum_missing_file(temp_state_dir):
    result = sm_module.get_artifact_checksum(str(temp_state_dir / "nonexistent.txt"))
    assert result is None

def test_update_artifact_list(temp_state_dir):
    # Create a dummy file
    test_file = temp_state_dir / "data.csv"
    test_file.write_text("col1,col2\n1,2")
    
    sm_module.register_artifact(str(test_file), "dataset", {"source": "test"})
    
    state = sm_module.get_state()
    assert len(state["artifacts"]) == 1
    assert state["artifacts"][0]["type"] == "dataset"
    assert "checksum" in state["artifacts"][0]

def test_update_artifact_list_replace_existing(temp_state_dir):
    test_file = temp_state_dir / "model.json"
    test_file.write_text("{}")
    
    # Register first time
    sm_module.register_artifact(str(test_file), "model", {"v": 1})
    state1 = sm_module.get_state()
    reg_time_1 = state1["artifacts"][0]["registered_at"]
    
    # Wait a tiny bit to ensure time diff if needed, though not strictly necessary for logic
    import time
    time.sleep(0.01)
    
    # Update content and register again
    test_file.write_text('{"v": 2}')
    sm_module.register_artifact(str(test_file), "model", {"v": 2})
    state2 = sm_module.get_state()
    
    assert len(state2["artifacts"]) == 1
    assert state2["artifacts"][0]["metadata"]["v"] == 2
    # Checksum should change
    assert state1["artifacts"][0]["checksum"] != state2["artifacts"][0]["checksum"]

def test_update_stage_status(temp_state_dir):
    sm_module.update_stage_status("ingestion", "completed", {"rows": 100})
    state = sm_module.get_state()
    assert "ingestion" in state["stages"]
    assert state["stages"]["ingestion"]["status"] == "completed"
    assert state["stages"]["ingestion"]["details"]["rows"] == 100

def test_update_stage_status_creates_new(temp_state_dir):
    sm_module.update_stage_status("new_stage", "running")
    state = sm_module.get_state()
    assert "new_stage" in state["stages"]
    assert state["stages"]["new_stage"]["status"] == "running"

def test_register_artifact(temp_state_dir):
    test_file = temp_state_dir / "report.txt"
    test_file.write_text("report content")
    
    sm_module.register_artifact(str(test_file), "report")
    state = sm_module.get_state()
    assert any(a["path"] == str(test_file.resolve()) for a in state["artifacts"])

def test_get_state(temp_state_dir):
    state = sm_module.get_state()
    assert isinstance(state, dict)

def test_verify_artifact_integrity_success(temp_state_dir):
    test_file = temp_state_dir / "valid.txt"
    test_file.write_text("valid")
    sm_module.register_artifact(str(test_file), "test")
    
    assert sm_module.verify_artifact_integrity(str(test_file)) is True

def test_verify_artifact_integrity_fail(temp_state_dir):
    test_file = temp_state_dir / "tampered.txt"
    test_file.write_text("valid")
    sm_module.register_artifact(str(test_file), "test")
    
    # Tamper with file
    test_file.write_text("invalid")
    
    assert sm_module.verify_artifact_integrity(str(test_file)) is False

def test_verify_artifact_missing_file(temp_state_dir):
    fake_path = temp_state_dir / "gone.txt"
    assert sm_module.verify_artifact_integrity(str(fake_path)) is False

def test_get_artifact_checksum(temp_state_dir):
    test_file = temp_state_dir / "checksum.txt"
    test_file.write_text("data")
    checksum = sm_module.get_artifact_checksum(str(test_file))
    assert checksum is not None
    assert len(checksum) == 64 # SHA256 hex length

def test_get_artifact_checksum_not_found(temp_state_dir):
    checksum = sm_module.get_artifact_checksum(str(temp_state_dir / "missing.txt"))
    assert checksum is None

def test_save_and_load_state(temp_state_dir):
    sm_module.update_stage_status("test", "completed")
    # Reload manually to ensure persistence
    state = sm_module.get_state()
    assert state["stages"]["test"]["status"] == "completed"
