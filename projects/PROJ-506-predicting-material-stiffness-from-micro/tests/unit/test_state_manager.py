import pytest
import yaml
from pathlib import Path
from code.utils.state_manager import load_state_file, compute_file_hash, update_project_state

def test_load_state_file_missing():
    path = Path("/tmp/nonexistent.yaml")
    assert load_state_file(path) == {}

def test_compute_file_hash(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello world")
    h = compute_file_hash(file_path)
    assert len(h) == 64  # SHA256 hex length
    assert h != ""

def test_update_project_state(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    projects_dir = state_dir / "projects"
    projects_dir.mkdir()
    
    project_id = "TEST-001"
    test_file = tmp_path / "test_artifact.txt"
    test_file.write_text("content")
    
    update_project_state(
        project_id, 
        state_dir, 
        [test_file], 
        "Test update"
    )
    
    state_file = projects_dir / f"{project_id}.yaml"
    assert state_file.exists()
    
    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)
    
    assert project_id in state
    assert "artifact_hashes" in state[project_id]
    assert "last_updated" in state[project_id]
    assert "history" in state[project_id]
    assert len(state[project_id]["history"]) == 1