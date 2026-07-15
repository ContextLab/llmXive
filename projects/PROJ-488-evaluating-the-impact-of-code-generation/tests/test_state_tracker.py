import pytest
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import yaml

# Adjust import path for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from state_tracker import (
    compute_file_hash,
    compute_directory_hash,
    load_state_file,
    save_state_file,
    update_state_with_artifact,
    update_state_timestamp,
    register_artifact_hash,
    get_artifact_state,
    verify_artifact_integrity,
    update_state_after_pipeline_stage,
    STATE_FILE_PATH,
    PROJECT_ROOT
)

@pytest.fixture
def temp_state_dir():
    """Create a temporary directory for state files during testing."""
    temp_dir = tempfile.mkdtemp()
    # Temporarily override STATE_FILE_PATH for testing
    original_path = STATE_FILE_PATH
    new_path = Path(temp_dir) / "test_state.yaml"
    # We can't easily mock the global variable, so we'll test with the real path
    # but ensure we clean up afterwards
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_compute_file_hash():
    """Test that file hash computation works correctly."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        temp_path = f.name
    
    try:
        hash1 = compute_file_hash(temp_path)
        hash2 = compute_file_hash(temp_path)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
    finally:
        os.unlink(temp_path)

def test_compute_directory_hash():
    """Test that directory hash computation works correctly."""
    temp_dir = tempfile.mkdtemp()
    try:
        # Create a test file
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("test content")
        
        hash1 = compute_directory_hash(temp_dir)
        hash2 = compute_directory_hash(temp_dir)
        assert hash1 == hash2
        assert len(hash1) == 64
    finally:
        shutil.rmtree(temp_dir)

def test_load_state_file_creates_new():
    """Test that load_state_file creates a new file if it doesn't exist."""
    # This test relies on the actual state file existing or being created
    state = load_state_file()
    assert "project_id" in state
    assert "created_at" in state
    assert "updated_at" in state
    assert "artifacts" in state
    assert "amendment_status" in state

def test_update_state_timestamp():
    """Test that update_state_timestamp updates the timestamp."""
    state_before = load_state_file()
    old_timestamp = state_before.get("updated_at")
    
    update_state_timestamp()
    
    state_after = load_state_file()
    new_timestamp = state_after.get("updated_at")
    
    # Parse timestamps to compare
    old_dt = datetime.fromisoformat(old_timestamp)
    new_dt = datetime.fromisoformat(new_timestamp)
    
    assert new_dt >= old_dt

def test_update_state_after_pipeline_stage():
    """Test that update_state_after_pipeline_stage updates state correctly."""
    stage_name = "test_stage"
    
    # Get state before
    state_before = load_state_file()
    
    # Update state
    update_state_after_pipeline_stage(stage_name)
    
    # Get state after
    state_after = load_state_file()
    
    # Verify updated_at changed
    old_dt = datetime.fromisoformat(state_before.get("updated_at"))
    new_dt = datetime.fromisoformat(state_after.get("updated_at"))
    assert new_dt >= old_dt
    
    # Verify pipeline stage was recorded
    assert "pipeline_stages" in state_after
    assert stage_name in state_after["pipeline_stages"]
    assert "completed_at" in state_after["pipeline_stages"][stage_name]

def test_update_state_with_artifact():
    """Test that update_state_with_artifact adds artifact to state."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(b"test artifact content")
        temp_file = f.name
    
    try:
        # Get state before
        state_before = load_state_file()
        artifacts_before = len(state_before.get("artifacts", {}))
        
        # Update state with artifact
        update_state_with_artifact(temp_file, "test_type")
        
        # Get state after
        state_after = load_state_file()
        artifacts_after = len(state_after.get("artifacts", {}))
        
        # Verify artifact was added
        assert artifacts_after == artifacts_before + 1
        
        # Find the artifact key
        artifact_key = None
        for key in state_after["artifacts"].keys():
            if key.endswith(".txt"):
                artifact_key = key
                break
        
        assert artifact_key is not None
        assert state_after["artifacts"][artifact_key]["type"] == "test_type"
        assert "hash" in state_after["artifacts"][artifact_key]
        assert "updated_at" in state_after["artifacts"][artifact_key]
    finally:
        os.unlink(temp_file)

def test_register_artifact_hash():
    """Test that register_artifact_hash registers artifact and returns hash."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(b"test content")
        temp_file = f.name
    
    try:
        registered_hash = register_artifact_hash(temp_file, "test_type")
        assert registered_hash is not None
        assert len(registered_hash) == 64
        
        # Verify it's in state
        state = load_state_file()
        artifact_key = str(Path(temp_file).relative_to(PROJECT_ROOT))
        assert artifact_key in state["artifacts"]
        assert state["artifacts"][artifact_key]["hash"] == registered_hash
    finally:
        os.unlink(temp_file)

def test_verify_artifact_integrity():
    """Test artifact integrity verification."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(b"test content")
        temp_file = f.name
    
    try:
        # Register the artifact
        register_artifact_hash(temp_file, "test_type")
        
        # Verify integrity (should be True)
        artifact_key = str(Path(temp_file).relative_to(PROJECT_ROOT))
        assert verify_artifact_integrity(artifact_key) is True
        
        # Modify the file
        Path(temp_file).write_text("modified content")
        
        # Verify integrity (should be False)
        assert verify_artifact_integrity(artifact_key) is False
    finally:
        os.unlink(temp_file)

def test_get_artifact_state():
    """Test retrieving artifact state."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(b"test content")
        temp_file = f.name
    
    try:
        # Register the artifact
        register_artifact_hash(temp_file, "test_type")
        
        # Get artifact state
        artifact_key = str(Path(temp_file).relative_to(PROJECT_ROOT))
        artifact_state = get_artifact_state(artifact_key)
        
        assert artifact_state is not None
        assert artifact_state["type"] == "test_type"
        assert "hash" in artifact_state
    finally:
        os.unlink(temp_file)