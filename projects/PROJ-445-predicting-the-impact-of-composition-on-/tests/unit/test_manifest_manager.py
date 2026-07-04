import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the functions we are testing
from src.utils.manifest_manager import (
    compute_file_hash,
    load_manifest,
    save_manifest,
    initialize_manifest,
    register_artifact,
    verify_artifact,
    MANIFEST_PATH
)

@pytest.fixture
def temp_project_root():
    """Creates a temporary directory to simulate a project root."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    # Create the state directory structure
    state_dir = Path("state")
    state_dir.mkdir(exist_ok=True)
    
    yield temp_dir
    
    # Cleanup
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_compute_file_hash(temp_project_root):
    """Test computing hash of a known file."""
    test_file = Path("state/test_file.txt")
    test_file.write_text("Hello, World!")
    
    hash_val = compute_file_hash(test_file)
    assert hash_val is not None
    assert len(hash_val) == 64  # SHA-256 hex length

def test_initialize_manifest(temp_project_root):
    """Test initializing a new manifest."""
    manifest_path = Path("state/manifest.json")
    
    # Ensure it doesn't exist
    if manifest_path.exists():
        manifest_path.unlink()
    
    result = initialize_manifest(manifest_path)
    assert result is True
    assert manifest_path.exists()
    
    with open(manifest_path, "r") as f:
        data = json.load(f)
    
    assert data["initialized"] is True
    assert "artifacts" in data
    assert isinstance(data["artifacts"], dict)

def test_load_manifest_when_empty(temp_project_root):
    """Test loading manifest when file does not exist."""
    manifest_path = Path("state/manifest.json")
    if manifest_path.exists():
        manifest_path.unlink()
    
    data = load_manifest(manifest_path)
    assert data["initialized"] is False
    assert data["artifacts"] == {}

def test_register_artifact(temp_project_root):
    """Test registering an artifact in the manifest."""
    # Create a test artifact
    artifact = Path("data/test.csv")
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("col1,col2\n1,2\n")
    
    # Initialize manifest first
    initialize_manifest()
    
    result = register_artifact(artifact)
    assert result is True
    
    # Verify it's in the manifest
    manifest = load_manifest()
    # Check if the path is recorded (might be absolute or relative depending on implementation)
    # We check that the hash exists for the registered path
    found = False
    for path_str, info in manifest["artifacts"].items():
        if str(artifact) in path_str or "test.csv" in path_str:
            found = True
            assert "hash" in info
            assert info["hash"] == compute_file_hash(artifact)
            break
    
    assert found, "Artifact path not found in manifest"

def test_verify_artifact_success(temp_project_root):
    """Test verifying an artifact that hasn't changed."""
    artifact = Path("data/verify_test.txt")
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("content")
    
    initialize_manifest()
    register_artifact(artifact)
    
    # Modify nothing
    assert verify_artifact(artifact) is True

def test_verify_artifact_failure_modified(temp_project_root):
    """Test verifying an artifact that has been modified."""
    artifact = Path("data/modify_test.txt")
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("original")
    
    initialize_manifest()
    register_artifact(artifact)
    
    # Modify the file
    artifact.write_text("modified")
    
    assert verify_artifact(artifact) is False

def test_verify_artifact_failure_missing(temp_project_root):
    """Test verifying an artifact that has been deleted."""
    artifact = Path("data/delete_test.txt")
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("to delete")
    
    initialize_manifest()
    register_artifact(artifact)
    
    # Delete the file
    artifact.unlink()
    
    assert verify_artifact(artifact) is False

def test_save_and_load_manifest(temp_project_root):
    """Test saving and loading manifest with custom data."""
    manifest_path = Path("state/custom_manifest.json")
    
    test_data = {
        "initialized": True,
        "artifacts": {
            "data/sample.csv": {"hash": "abc123"}
        },
        "metadata": {"version": "1.0"}
    }
    
    assert save_manifest(test_data, manifest_path) is True
    assert manifest_path.exists()
    
    loaded = load_manifest(manifest_path)
    assert loaded["artifacts"]["data/sample.csv"]["hash"] == "abc123"
