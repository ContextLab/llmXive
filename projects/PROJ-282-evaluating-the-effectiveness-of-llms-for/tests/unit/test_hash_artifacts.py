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
    run_checksum_verification
)
from src.utils.config import get_project_root


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory structure simulating a project."""
    temp_dir = tempfile.mkdtemp()
    original_root = get_project_root()
    
    # Patch get_project_root to return our temp directory
    import src.utils.hash_artifacts as hash_module
    import src.utils.config as config_module
    
    original_get_root = config_module.get_project_root
    config_module.get_project_root = lambda: Path(temp_dir)
    hash_module.get_project_root = lambda: Path(temp_dir)
    
    # Create necessary directories
    (Path(temp_dir) / "data" / "processed").mkdir(parents=True)
    (Path(temp_dir) / "data" / "results").mkdir(parents=True)
    (Path(temp_dir) / "state" / "projects").mkdir(parents=True)
    
    yield Path(temp_dir)
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    # Restore original function
    config_module.get_project_root = original_get_root
    hash_module.get_project_root = lambda: original_root


def test_compute_file_hash_success(temp_project_dir):
    """Test successful file hashing."""
    test_file = temp_project_dir / "data" / "processed" / "test.txt"
    test_file.write_text("Hello, World!")
    
    hash_value = compute_sha256(test_file)
    
    assert len(hash_value) == 64  # SHA-256 hex length
    assert all(c in '0123456789abcdef' for c in hash_value)
    
    # Verify hash is deterministic
    hash_value_2 = compute_sha256(test_file)
    assert hash_value == hash_value_2


def test_compute_file_hash_not_found(temp_project_dir):
    """Test hashing a non-existent file raises FileNotFoundError."""
    non_existent = temp_project_dir / "non_existent.txt"
    
    with pytest.raises(FileNotFoundError):
        compute_sha256(non_existent)


def test_compute_file_hash_empty(temp_project_dir):
    """Test hashing an empty file."""
    empty_file = temp_project_dir / "data" / "processed" / "empty.txt"
    empty_file.touch()
    
    hash_value = compute_sha256(empty_file)
    
    # SHA-256 of empty string
    expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert hash_value == expected_hash


def test_load_current_state_valid_json(temp_project_dir):
    """Test loading a valid JSON state file."""
    state_file = temp_project_dir / "state" / "projects" / "test_state.json"
    test_state = {"version": 1, "data": "test"}
    
    with open(state_file, "w") as f:
        json.dump(test_state, f)
    
    loaded_state = load_current_state()
    
    assert loaded_state == test_state
    assert loaded_state["version"] == 1


def test_save_state_success(temp_project_dir):
    """Test saving state to file."""
    test_state = {"version": 2, "artifacts": {"test": "value"}}
    
    save_state(test_state)
    
    state_file = temp_project_dir / "state" / "projects" / "test_state.json"
    assert state_file.exists()
    
    with open(state_file, "r") as f:
        loaded = json.load(f)
    
    assert loaded == test_state


def test_hash_directory(temp_project_dir):
    """Test hashing all files in a directory."""
    # Create test files
    (temp_project_dir / "data" / "processed" / "file1.txt").write_text("Content 1")
    (temp_project_dir / "data" / "processed" / "file2.csv").write_text("a,b,c")
    (temp_project_dir / "data" / "results" / "report.json").write_text('{"key": "value"}')
    
    # Hash only text files
    text_hashes = hash_directory(temp_project_dir / "data" / "processed", extensions=[".txt"])
    
    assert "file1.txt" in text_hashes
    assert "file2.csv" not in text_hashes
    assert len(text_hashes) == 1
    
    # Hash all files
    all_hashes = hash_directory(temp_project_dir / "data" / "processed")
    assert len(all_hashes) == 2


def test_generate_artifact_manifest(temp_project_dir):
    """Test generating an artifact manifest."""
    # Create test files
    test_file = temp_project_dir / "data" / "processed" / "test.json"
    test_file.write_text('{"data": "test"}')
    
    manifest = generate_artifact_manifest(temp_project_dir / "data" / "processed")
    
    assert manifest["total_files"] == 1
    assert "test.json" in manifest["files"]
    assert "sha256" in manifest["files"]["test.json"]
    assert "size_bytes" in manifest["files"]["test.json"]
    assert "generated_at" in manifest


def test_update_state_integration(temp_project_dir):
    """Test updating state with a manifest."""
    initial_state = {"version": 1}
    
    manifest = {
        "directory": "test",
        "total_files": 1,
        "files": {"test.txt": {"sha256": "abc123"}}
    }
    
    updated_state = update_state_with_manifest(initial_state, manifest, "test_stage")
    
    assert "artifacts" in updated_state
    assert "test_stage" in updated_state["artifacts"]
    assert updated_state["version"] == 2
    assert "manifest" in updated_state["artifacts"]["test_stage"]


def test_checksum_verification_success(temp_project_dir):
    """Test successful checksum verification."""
    # Create initial state with known hashes
    test_file = temp_project_dir / "data" / "processed" / "verify.txt"
    test_file.write_text("Verify content")
    
    manifest = generate_artifact_manifest(temp_project_dir / "data" / "processed")
    
    state = {"artifacts": {"test_stage": {"manifest": manifest}}}
    
    verification = run_checksum_verification(state, temp_project_dir / "data" / "processed", "test_stage")
    
    assert verification["status"] == "verified"
    assert len(verification["unchanged_files"]) == 1
    assert len(verification["modified_files"]) == 0
    assert len(verification["missing_files"]) == 0


def test_checksum_verification_failure(temp_project_dir):
    """Test checksum verification when files are modified."""
    # Create initial state
    test_file = temp_project_dir / "data" / "processed" / "verify.txt"
    test_file.write_text("Original content")
    
    manifest = generate_artifact_manifest(temp_project_dir / "data" / "processed")
    
    state = {"artifacts": {"test_stage": {"manifest": manifest}}}
    
    # Modify the file
    test_file.write_text("Modified content")
    
    verification = run_checksum_verification(state, temp_project_dir / "data" / "processed", "test_stage")
    
    assert verification["status"] == "verification_failed"
    assert len(verification["modified_files"]) == 1
    assert "verify.txt" in verification["modified_files"]