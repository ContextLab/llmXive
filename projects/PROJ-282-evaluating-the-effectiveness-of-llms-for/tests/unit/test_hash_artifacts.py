import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
from src.utils.hash_artifacts import (
    compute_sha256, load_current_state, save_state, hash_directory,
    generate_artifact_manifest, update_state_with_manifest,
    run_checksum_verification, main
)


@pytest.fixture
def temp_project_dir():
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)


def test_compute_file_hash_success(temp_project_dir):
    test_file = temp_project_dir / "test.txt"
    test_file.write_text("hello world")
    hash_val = compute_sha256(test_file)
    assert hash_val is not None
    assert len(hash_val) == 64  # SHA256 hex length


def test_compute_file_hash_not_found(temp_project_dir):
    with pytest.raises(FileNotFoundError):
        compute_sha256(temp_project_dir / "nonexistent.txt")


def test_compute_file_hash_empty(temp_project_dir):
    test_file = temp_project_dir / "empty.txt"
    test_file.touch()
    hash_val = compute_sha256(test_file)
    assert hash_val is not None


def test_load_current_state_valid_json(temp_project_dir):
    state_file = temp_project_dir / "state.json"
    state_file.write_text(json.dumps({"version": "1.0"}))
    state = load_current_state(state_file)
    assert state["version"] == "1.0"


def test_save_state_success(temp_project_dir):
    state_file = temp_project_dir / "state.json"
    save_state({"key": "value"}, state_file)
    assert state_file.exists()
    with open(state_file) as f:
        data = json.load(f)
    assert data["key"] == "value"


def test_hash_directory(temp_project_dir):
    # Create a file
    (temp_project_dir / "file.txt").write_text("data")
    manifest = hash_directory(temp_project_dir)
    assert "file.txt" in manifest


def test_generate_artifact_manifest(temp_project_dir):
    (temp_project_dir / "a.txt").write_text("1")
    (temp_project_dir / "b.txt").write_text("2")
    manifest = generate_artifact_manifest(temp_project_dir)
    assert len(manifest) == 2


def test_update_state_integration(temp_project_dir):
    state_file = temp_project_dir / "state.json"
    save_state({}, state_file)
    update_state_with_manifest(state_file, temp_project_dir)
    assert state_file.exists()


def test_checksum_verification_success(temp_project_dir):
    # Create a file and its hash in state
    test_file = temp_project_dir / "verify.txt"
    test_file.write_text("content")
    state_file = temp_project_dir / "state.json"
    save_state({
        "artifacts": {
            "verify.txt": compute_sha256(test_file)
        }
    }, state_file)
    
    result = run_checksum_verification(state_file, temp_project_dir)
    assert result is True


def test_checksum_verification_failure(temp_project_dir):
    test_file = temp_project_dir / "verify.txt"
    test_file.write_text("content")
    state_file = temp_project_dir / "state.json"
    # Save wrong hash
    save_state({
        "artifacts": {
            "verify.txt": "wrong_hash"
        }
    }, state_file)
    
    result = run_checksum_verification(state_file, temp_project_dir)
    assert result is False
