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

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory structure mimicking the project."""
    temp_dir = tempfile.mkdtemp()
    # Create structure
    (Path(temp_dir) / "data" / "processed").mkdir(parents=True)
    (Path(temp_dir) / "data" / "results").mkdir(parents=True)
    (Path(temp_dir) / "state" / "projects").mkdir(parents=True)
    
    # Create a dummy file
    dummy_file = Path(temp_dir) / "data" / "processed" / "test.csv"
    dummy_file.write_text("id,label\n1,vulnerable\n")
    
    yield temp_dir
    
    shutil.rmtree(temp_dir)

def test_compute_file_hash_success(temp_project_dir):
    file_path = Path(temp_project_dir) / "data" / "processed" / "test.csv"
    hash_val = compute_sha256(file_path)
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64  # SHA-256 hex length

def test_compute_file_hash_not_found():
    with pytest.raises(FileNotFoundError):
        compute_sha256(Path("/nonexistent/file.txt"))

def test_compute_file_hash_empty(tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.touch()
    hash_val = compute_sha256(empty_file)
    assert hash_val == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

def test_load_current_state_valid_json(temp_project_dir):
    state_file = Path(temp_project_dir) / "state" / "projects" / "test.yaml"
    state_data = {"project_id": "test", "artifacts": {}}
    with open(state_file, "w") as f:
        json.dump(state_data, f)
    
    loaded = load_current_state(state_file)
    assert loaded["project_id"] == "test"

def test_save_state_success(temp_project_dir):
    state_file = Path(temp_project_dir) / "state" / "projects" / "test.yaml"
    state_data = {"project_id": "test", "completed_tasks": ["T010"]}
    save_state(state_data, state_file)
    
    assert state_file.exists()
    with open(state_file, "r") as f:
        loaded = json.load(f)
    assert loaded["project_id"] == "test"

def test_hash_directory(temp_project_dir):
    dir_path = Path(temp_project_dir) / "data" / "processed"
    hashes = hash_directory(dir_path)
    assert "test.csv" in hashes
    assert len(hashes) == 1

def test_generate_artifact_manifest(temp_project_dir):
    artifacts_dir = Path(temp_project_dir) / "data"
    state_dir = Path(temp_project_dir) / "state" / "projects"
    manifest = generate_artifact_manifest(artifacts_dir, state_dir)
    
    assert "generated_at" in manifest
    assert "directories" in manifest
    assert "data/processed" in manifest["directories"]

def test_update_state_integration(temp_project_dir):
    state_file = Path(temp_project_dir) / "state" / "projects" / "test.yaml"
    state_data = {"project_id": "test", "artifacts": {}}
    
    manifest = {"test": "data"}
    updated = update_state_with_manifest(manifest, state_data, "T010")
    
    assert "T010" in updated["artifacts"]
    assert "T010" in updated["completed_tasks"]

def test_checksum_verification_success(temp_project_dir):
    artifacts_dir = Path(temp_project_dir) / "data"
    state_dir = Path(temp_project_dir) / "state" / "projects"
    manifest = generate_artifact_manifest(artifacts_dir, state_dir)
    
    # Verify against itself should pass
    assert run_checksum_verification(manifest, artifacts_dir) is True

def test_checksum_verification_failure(temp_project_dir):
    # Create a manifest with a wrong hash
    bad_manifest = {
        "directories": {
            "processed": {
                "files": {
                    "test.csv": "0000000000000000000000000000000000000000000000000000000000000000"
                }
            }
        }
    }
    artifacts_dir = Path(temp_project_dir) / "data"
    assert run_checksum_verification(bad_manifest, artifacts_dir) is False