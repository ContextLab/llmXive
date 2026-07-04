import os
import tempfile
import hashlib
from pathlib import Path
import pytest
import yaml

# Import the functions to test
from src.utils.state_manager import (
    compute_file_hash,
    get_state_file_path,
    load_state,
    update_state_artifact,
    verify_artifact_integrity
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # We need to simulate the project root structure temporarily
        # or mock the paths. For this test, we'll create a real temp structure
        # and patch the functions or run in a controlled env.
        # Since the functions use relative paths, we'll create a temp root
        # and change directory if necessary, or just test the logic that doesn't rely on global paths.
        # However, update_state_artifact relies on 'state/projects/'.
        # Let's create a temp dir and set an env var or just create the structure there.
        # To keep it simple and robust, we will create the necessary dirs in the temp dir.
        # But the code uses relative paths. 
        # Strategy: Create the temp structure, cd into it, run tests, cd out.
        # Or better: The test runner might handle this. 
        # Let's assume the test runs from project root or we mock the path generation.
        # For this implementation, we will rely on the fact that we can create 'state' dir
        # in the temp directory and change cwd.
        
        original_cwd = os.getcwd()
        os.chdir(tempdir)
        
        # Create necessary dirs
        Path("state").mkdir()
        Path("state/projects").mkdir()
        
        yield tempdir
        
        os.chdir(original_cwd)

def test_compute_file_hash(temp_dir):
    """Test SHA-256 hash computation."""
    test_file = Path("test_file.txt")
    content = b"Hello, World!"
    test_file.write_bytes(content)
    
    expected_hash = hashlib.sha256(content).hexdigest()
    computed_hash = compute_file_hash(test_file)
    
    assert computed_hash == expected_hash
    
    # Test non-existent file
    non_existent = Path("does_not_exist.txt")
    assert compute_file_hash(non_existent) is None

def test_get_state_file_path(temp_dir):
    """Test state file path generation."""
    path = get_state_file_path("TEST-001")
    assert path == Path("state/projects/TEST-001.yaml")
    assert path.parent.exists()

def test_load_state_empty(temp_dir):
    """Test loading state when file doesn't exist."""
    state = load_state("NEW-PROJ")
    assert state == {}

def test_load_state_existing(temp_dir):
    """Test loading state when file exists."""
    state_path = get_state_file_path("EXISTING-PROJ")
    initial_state = {"project_id": "EXISTING-PROJ", "artifacts": {}}
    with open(state_path, "w") as f:
        yaml.dump(initial_state, f)
    
    loaded = load_state("EXISTING-PROJ")
    assert loaded["project_id"] == "EXISTING-PROJ"

def test_update_state_artifact(temp_dir):
    """Test updating state with a new artifact hash."""
    # Create a dummy artifact
    artifact_path = Path("data/processed/test_data.csv")
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("col1,col2\n1,2\n")
    
    success = update_state_artifact(artifact_path, "TEST-PROJ")
    assert success is True
    
    # Verify state file content
    state_path = get_state_file_path("TEST-PROJ")
    assert state_path.exists()
    
    with open(state_path, "r") as f:
        state = yaml.safe_load(f)
    
    assert "artifacts" in state
    assert "derived_data" in state["artifacts"]
    assert str(artifact_path) in state["artifacts"]["derived_data"]
    
    entry = state["artifacts"]["derived_data"][str(artifact_path)]
    assert "hash" in entry
    assert "updated_at" in entry
    assert "size_bytes" in entry

def test_verify_artifact_integrity_success(temp_dir):
    """Test verification when hash matches."""
    artifact_path = Path("data/processed/verify_test.csv")
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    content = b"test content"
    artifact_path.write_bytes(content)
    
    # Update state first
    update_state_artifact(artifact_path, "VERIFY-PROJ")
    
    # Verify
    assert verify_artifact_integrity(artifact_path, "VERIFY-PROJ") is True

def test_verify_artifact_integrity_failure(temp_dir):
    """Test verification when hash mismatches."""
    artifact_path = Path("data/processed/mismatch_test.csv")
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("original")
    
    # Update state
    update_state_artifact(artifact_path, "MISMATCH-PROJ")
    
    # Modify file
    artifact_path.write_text("modified")
    
    # Verify should fail
    assert verify_artifact_integrity(artifact_path, "MISMATCH-PROJ") is False
