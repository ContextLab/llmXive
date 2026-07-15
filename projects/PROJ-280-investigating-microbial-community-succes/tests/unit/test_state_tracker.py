"""
Unit tests for the state tracking mechanism.
"""
import os
import tempfile
import yaml
from pathlib import Path
import pytest
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from state_tracker import (
    calculate_file_hash,
    update_artifact_hash,
    get_artifact_hash,
    verify_artifact_integrity,
    list_all_artifacts,
    _load_state,
    _save_state,
    STATE_FILE_PATH
)

@pytest.fixture
def temp_state_file():
    """Create a temporary state file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        initial_state = {
            "project_id": "TEST-PROJECT",
            "artifacts": {},
            "last_updated": None
        }
        yaml.dump(initial_state, f, default_flow_style=False)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_artifact_file():
    """Create a temporary artifact file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test content for hashing")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_calculate_file_hash(temp_artifact_file):
    """Test SHA256 hash calculation."""
    hash1 = calculate_file_hash(temp_artifact_file)
    hash2 = calculate_file_hash(temp_artifact_file)
    
    assert len(hash1) == 64  # SHA256 hex length
    assert hash1 == hash2
    assert all(c in '0123456789abcdef' for c in hash1)

def test_calculate_file_hash_different_content():
    """Test that different content produces different hashes."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f1:
        f1.write("Content A")
        path1 = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f2:
        f2.write("Content B")
        path2 = f2.name
    
    hash1 = calculate_file_hash(path1)
    hash2 = calculate_file_hash(path2)
    
    assert hash1 != hash2
    
    os.unlink(path1)
    os.unlink(path2)

def test_update_and_get_artifact_hash(temp_state_file, temp_artifact_file):
    """Test updating and retrieving artifact hash."""
    # Temporarily override STATE_FILE_PATH for testing
    import state_tracker
    original_path = state_tracker.STATE_FILE_PATH
    state_tracker.STATE_FILE_PATH = temp_state_file
    
    try:
        # Update the artifact
        update_artifact_hash(temp_artifact_file, "Test artifact")
        
        # Get the hash
        stored_hash = get_artifact_hash(temp_artifact_file)
        
        assert stored_hash is not None
        assert len(stored_hash) == 64
        
        # Verify the hash matches the file
        actual_hash = calculate_file_hash(temp_artifact_file)
        assert stored_hash == actual_hash
    finally:
        state_tracker.STATE_FILE_PATH = original_path

def test_verify_artifact_integrity(temp_state_file, temp_artifact_file):
    """Test artifact integrity verification."""
    import state_tracker
    original_path = state_tracker.STATE_FILE_PATH
    state_tracker.STATE_FILE_PATH = temp_state_file
    
    try:
        # Initially should fail as artifact is not tracked
        assert verify_artifact_integrity(temp_artifact_file) == False
        
        # Update the artifact
        update_artifact_hash(temp_artifact_file, "Test artifact")
        
        # Now should pass
        assert verify_artifact_integrity(temp_artifact_file) == True
        
        # Modify the file
        with open(temp_artifact_file, 'w') as f:
            f.write("Modified content")
        
        # Should fail now
        assert verify_artifact_integrity(temp_artifact_file) == False
    finally:
        state_tracker.STATE_FILE_PATH = original_path

def test_list_all_artifacts(temp_state_file, temp_artifact_file):
    """Test listing all artifacts."""
    import state_tracker
    original_path = state_tracker.STATE_FILE_PATH
    state_tracker.STATE_FILE_PATH = temp_state_file
    
    try:
        # Initially empty
        artifacts = list_all_artifacts()
        assert len(artifacts) == 0
        
        # Add an artifact
        update_artifact_hash(temp_artifact_file, "Test artifact")
        
        # Should have one artifact
        artifacts = list_all_artifacts()
        assert len(artifacts) == 1
        assert temp_artifact_file in artifacts
        assert 'hash' in artifacts[temp_artifact_file]
        assert 'description' in artifacts[temp_artifact_file]
    finally:
        state_tracker.STATE_FILE_PATH = original_path

def test_state_file_creation():
    """Test that state file is created if it doesn't exist."""
    import state_tracker
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_state_path = Path(temp_dir) / "test_state.yaml"
        
        # Override the state path
        original_path = state_tracker.STATE_FILE_PATH
        state_tracker.STATE_FILE_PATH = temp_state_path
        
        try:
            # Load state should create the file
            state = _load_state()
            
            assert temp_state_path.exists()
            assert state['project_id'] == "TEST-PROJECT"
            assert 'artifacts' in state
            assert state['artifacts'] == {}
        finally:
            state_tracker.STATE_FILE_PATH = original_path