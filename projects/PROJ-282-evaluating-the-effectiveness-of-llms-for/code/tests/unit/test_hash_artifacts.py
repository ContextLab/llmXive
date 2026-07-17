import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

from src.utils.hash_artifacts import (
    compute_sha256,
    load_current_state,
    save_state,
    hash_directory,
    generate_artifact_manifest,
    update_state_with_manifest,
    run_checksum_verification,
    PROJECT_ROOT
)

@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project structure for testing."""
    # Create a mock project root structure
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    # Create a test file
    test_file = data_dir / "test.csv"
    test_file.write_text("id,label\n1,vulnerable\n2,safe\n")
    
    # Create another test file
    test_file2 = data_dir / "metrics.json"
    test_file2.write_text('{"accuracy": 0.95}')
    
    # Create a state directory
    state_dir = tmp_path / "state" / "projects"
    state_dir.mkdir(parents=True)
    
    return tmp_path

def test_compute_file_hash_success(temp_project_dir):
    """Test successful SHA-256 computation."""
    file_path = temp_project_dir / "data" / "processed" / "test.csv"
    hash_val = compute_sha256(file_path)
    assert len(hash_val) == 64  # SHA-256 hex length
    assert isinstance(hash_val, str)

def test_compute_file_hash_not_found():
    """Test error handling for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_sha256(Path("/nonexistent/file.txt"))

def test_compute_file_hash_empty(tmp_path):
    """Test computation on an empty file."""
    empty_file = tmp_path / "empty.txt"
    empty_file.touch()
    hash_val = compute_sha256(empty_file)
    # SHA-256 of empty string
    expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert hash_val == expected

def test_load_current_state_valid_json(tmp_path):
    """Test loading a valid JSON state file."""
    state_file = tmp_path / "state.json"
    test_state = {"artifacts": {"file1.txt": "hash1"}, "last_updated": "2023-01-01"}
    state_file.write_text(json.dumps(test_state))
    
    # Temporarily override PROJECT_ROOT for testing if needed, 
    # but here we test the logic directly on the fixture path if we mock
    # Since the function uses a global PROJECT_ROOT, we test the logic
    # by creating a state file in a known location and mocking or 
    # by testing the return structure if we assume the function works as intended.
    # For unit testing isolation, we will test the logic by creating a temp file
    # and passing it, but the function uses a global. 
    # Let's test the behavior by creating the file in the expected location 
    # relative to a temp root if we could, but simpler:
    # Just verify the function doesn't crash on valid JSON in the default path
    # by creating the file there.
    
    state_path = PROJECT_ROOT / "state" / "projects" / "PROJ-282-evaluating-the-effectiveness-of-llms-for.yaml"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(test_state))
    
    result = load_current_state()
    assert result["artifacts"]["file1.txt"] == "hash1"
    assert result["last_updated"] == "2023-01-01"
    
    # Cleanup
    state_path.unlink()

def test_save_state_success(tmp_path):
    """Test saving state to file."""
    state_path = PROJECT_ROOT / "state" / "projects" / "PROJ-282-evaluating-the-effectiveness-of-llms-for.yaml"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    test_state = {"artifacts": {}, "last_updated": "2023-01-01"}
    save_state(test_state)
    
    assert state_path.exists()
    with open(state_path, "r") as f:
        loaded = json.load(f)
    assert loaded == test_state
    
    state_path.unlink()

def test_hash_directory(temp_project_dir):
    """Test hashing all files in a directory."""
    data_dir = temp_project_dir / "data" / "processed"
    hashes = hash_directory(data_dir, "*.csv")
    
    assert len(hashes) == 1
    assert "data/processed/test.csv" in hashes
    assert len(hashes["data/processed/test.csv"]) == 64

def test_generate_artifact_manifest(temp_project_dir):
    """Test generating a full artifact manifest."""
    data_dir = temp_project_dir / "data" / "processed"
    manifest = generate_artifact_manifest([data_dir], ["*.csv", "*.json"])
    
    assert "generated_at" in manifest
    assert "artifacts" in manifest
    assert len(manifest["artifacts"]) == 2
    
    assert any("test.csv" in k for k in manifest["artifacts"])
    assert any("metrics.json" in k for k in manifest["artifacts"])

def test_update_state_integration(temp_project_dir):
    """Test updating state with a new manifest."""
    # Clear state first
    state_path = PROJECT_ROOT / "state" / "projects" / "PROJ-282-evaluating-the-effectiveness-of-llms-for.yaml"
    if state_path.exists():
        state_path.unlink()
    
    data_dir = temp_project_dir / "data" / "processed"
    manifest = generate_artifact_manifest([data_dir], ["*.csv"])
    
    update_state_with_manifest(manifest)
    
    state = load_current_state()
    assert len(state["artifacts"]) == 1
    assert "last_updated" in state

def test_checksum_verification_success(temp_project_dir):
    """Test verification when files match state."""
    # First, update state
    data_dir = temp_project_dir / "data" / "processed"
    manifest = generate_artifact_manifest([data_dir], ["*.csv", "*.json"])
    update_state_with_manifest(manifest)
    
    # Then verify
    success = run_checksum_verification([data_dir], ["*.csv", "*.json"])
    assert success is True

def test_checksum_verification_failure(temp_project_dir):
    """Test verification when files are modified."""
    # Update state
    data_dir = temp_project_dir / "data" / "processed"
    manifest = generate_artifact_manifest([data_dir], ["*.csv"])
    update_state_with_manifest(manifest)
    
    # Modify file
    csv_file = data_dir / "test.csv"
    original_content = csv_file.read_text()
    csv_file.write_text(original_content + "\nmodified")
    
    # Verify should fail
    success = run_checksum_verification([data_dir], ["*.csv"])
    assert success is False
    
    # Restore
    csv_file.write_text(original_content)