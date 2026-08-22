import os
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import yaml

from src.utils.state_manager import (
    compute_file_hash,
    scan_directory_for_artifacts,
    load_state,
    save_state,
    update_artifact_hashes,
    verify_artifacts
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_file(temp_dir):
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("Hello, World!")
    return file_path

def test_compute_file_hash(sample_file):
    expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
    assert compute_file_hash(sample_file) == expected_hash

def test_compute_file_hash_missing(temp_dir):
    missing_file = temp_dir / "nonexistent.txt"
    with pytest.raises(FileNotFoundError):
        compute_file_hash(missing_file)

def test_scan_directory_for_artifacts(temp_dir):
    # Create some files
    (temp_dir / "a.txt").write_text("a")
    (temp_dir / "b.txt").write_text("b")
    (temp_dir / "sub").mkdir()
    (temp_dir / "sub" / "c.py").write_text("c")
    
    # Scan all
    all_files = scan_directory_for_artifacts(temp_dir)
    assert len(all_files) == 3
    
    # Scan specific pattern
    txt_files = scan_directory_for_artifacts(temp_dir, pattern="*.txt")
    assert len(txt_files) == 2
    assert all(f.suffix == ".txt" for f in txt_files)

def test_scan_directory_nonexistent(temp_dir):
    nonexistent = temp_dir / "does_not_exist"
    result = scan_directory_for_artifacts(nonexistent)
    assert result == []

def test_load_state_missing_file(temp_dir):
    missing_path = temp_dir / "missing.yaml"
    state = load_state(missing_path)
    assert state == {"project_id": None, "artifacts": {}}

def test_save_state_and_load(temp_dir):
    state_path = temp_dir / "state.yaml"
    test_state = {"project_id": "TEST-001", "artifacts": {"key": "value"}}
    
    save_state(test_state, state_path)
    
    loaded = load_state(state_path)
    assert loaded["project_id"] == "TEST-001"
    assert loaded["artifacts"]["key"] == "value"

def test_update_artifact_hashes_integration(temp_dir):
    # Create a dummy file
    data_dir = temp_dir / "data"
    data_dir.mkdir()
    file_path = data_dir / "dummy.csv"
    content = "id,value\n1,100"
    file_path.write_text(content)
    
    expected_hash = hashlib.sha256(content.encode()).hexdigest()
    
    state = {}
    project_id = "PROJ-TEST"
    
    updated_state = update_artifact_hashes(state, project_id, [data_dir])
    
    assert updated_state["project_id"] == project_id
    assert "artifacts" in updated_state
    
    # Check if the file was recorded
    artifacts = updated_state["artifacts"]
    # The key depends on how the path is converted to string, usually relative or absolute
    # We just check that one of the keys contains 'data' and has the file
    found = False
    for dir_key, dir_info in artifacts.items():
        if "data" in dir_key:
            files = dir_info.get("files", {})
            # Check if our file is in there (path might be relative or absolute depending on run context)
            if any("dummy.csv" in p for p in files.keys()):
                # Verify hash
                file_hash = list(files.values())[list(files.keys()).index([p for p in files.keys() if "dummy.csv" in p][0])]
                assert file_hash == expected_hash
                found = True
                break
    
    assert found, "File was not found in updated state artifacts"

def test_verify_artifacts(temp_dir):
    # Setup
    data_dir = temp_dir / "data"
    data_dir.mkdir()
    file_path = data_dir / "test.txt"
    content = "test content"
    file_path.write_text(content)
    
    # Create initial state with correct hash
    correct_hash = hashlib.sha256(content.encode()).hexdigest()
    state = {
        "project_id": "PROJ-VERIFY",
        "artifacts": {
            str(data_dir): {
                "last_updated": None,
                "files": {str(file_path): correct_hash}
            }
        }
    }
    
    # Verify should pass
    assert verify_artifacts(state, "PROJ-VERIFY") is True
    
    # Modify file
    file_path.write_text("modified content")
    
    # Verify should fail
    assert verify_artifacts(state, "PROJ-VERIFY") is False
    
    # Project ID mismatch
    state["project_id"] = "WRONG-PROJ"
    assert verify_artifacts(state, "PROJ-VERIFY") is False
