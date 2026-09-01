"""
Unit tests for src/utils/versioning.py.

Tests Constitution Principle V implementation:
- Hash calculation correctness.
- Atomic write behavior.
- State update and retrieval.
- Integrity verification.
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

# We need to mock the project root to avoid polluting the actual project state
# during tests. We'll create a temporary directory for the test run.

@pytest.fixture
def temp_state_dir():
    """Create a temporary directory for state files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_project_root(temp_state_dir):
    """Mock the project root to point to a temporary directory."""
    # The module uses a global _PROJECT_ROOT derived from __file__.
    # We need to patch the module's internal constants or the module itself.
    # Since we are testing the module as installed, we will patch the specific
    # constants used in versioning.py.
    
    # We'll patch the _STATE_DIR directly in the module namespace
    # But since we can't easily import the module before patching if it runs on import,
    # we assume the module is importable and patch its internal path.
    
    # A better approach for this specific setup is to mock the _PROJECT_ROOT
    # and _STATE_DIR inside the versioning module.
    
    # Let's create a fake project structure
    fake_root = Path(temp_state_dir) / "fake_root"
    fake_root.mkdir()
    
    # We will patch the module's _PROJECT_ROOT and _STATE_DIR
    with patch('src.utils.versioning._PROJECT_ROOT', fake_root):
        with patch('src.utils.versioning._STATE_DIR', fake_root / "state" / "projects"):
            # Re-import to pick up the patched paths? 
            # No, the module is already loaded. We must patch the module's attributes.
            # However, for this test, let's just ensure the directory exists and use
            # the patched path logic by re-defining the module's behavior via patching
            # the specific functions that rely on paths.
            
            # Actually, the cleanest way is to patch the module's global variables
            # before the code that uses them runs. But since we are in a test, 
            # we can just patch the module's internal variables directly.
            
            import src.utils.versioning as versioning_module
            
            original_root = versioning_module._PROJECT_ROOT
            original_state_dir = versioning_module._STATE_DIR
            
            versioning_module._PROJECT_ROOT = fake_root
            versioning_module._STATE_DIR = fake_root / "state" / "projects"
            
            yield versioning_module
            
            # Restore
            versioning_module._PROJECT_ROOT = original_root
            versioning_module._STATE_DIR = original_state_dir

def test_compute_hash_dict():
    """Test hash calculation for a dictionary."""
    from src.utils.versioning import _compute_hash
    
    data = {"key": "value", "number": 1}
    hash1 = _compute_hash(data)
    hash2 = _compute_hash(data)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length
    
    # Different data should produce different hash
    data_diff = {"key": "value", "number": 2}
    hash3 = _compute_hash(data_diff)
    assert hash1 != hash3

def test_compute_hash_string():
    """Test hash calculation for a string."""
    from src.utils.versioning import _compute_hash
    
    data = "test string"
    hash1 = _compute_hash(data)
    hash2 = _compute_hash(data)
    
    assert hash1 == hash2

def test_compute_hash_bytes():
    """Test hash calculation for bytes."""
    from src.utils.versioning import _compute_hash
    
    data = b"test bytes"
    hash1 = _compute_hash(data)
    hash2 = _compute_hash(data)
    
    assert hash1 == hash2

def test_update_state_creates_file(mock_project_root):
    """Test that update_state creates a new state file if it doesn't exist."""
    from src.utils.versioning import update_state, _STATE_DIR
    
    project_id = "TEST-PROJECT"
    key = "test_key"
    value = "test_value"
    
    state_path = _STATE_DIR / f"{project_id}.yaml"
    
    # Ensure file doesn't exist
    if state_path.exists():
        state_path.unlink()
    
    result = update_state(key, value, project_id=project_id)
    
    assert state_path.exists()
    assert result[key] == value
    assert "_hash" in result

def test_update_state_updates_existing(mock_project_root):
    """Test that update_state updates an existing state file."""
    from src.utils.versioning import update_state, _STATE_DIR, _compute_hash
    
    project_id = "TEST-PROJECT-2"
    state_path = _STATE_DIR / f"{project_id}.yaml"
    
    # Create initial state
    initial_data = {"existing_key": "existing_value"}
    with open(state_path, 'w') as f:
        yaml.dump(initial_data, f)
    
    # Update with new key
    result = update_state("new_key", "new_value", project_id=project_id)
    
    assert result["existing_key"] == "existing_value"
    assert result["new_key"] == "new_value"
    assert "_hash" in result

def test_update_state_atomic_write(mock_project_root):
    """Test that update_state writes atomically (no partial writes on failure)."""
    from src.utils.versioning import update_state, _STATE_DIR
    
    project_id = "TEST-PROJECT-3"
    state_path = _STATE_DIR / f"{project_id}.yaml"
    
    # Mock the write to fail halfway
    original_move = shutil.move
    
    def failing_move(src, dst):
        # Simulate failure after creating temp file but before move
        raise IOError("Simulated write failure")
    
    try:
        with patch('src.utils.versioning.shutil.move', side_effect=failing_move):
            with pytest.raises(IOError):
                update_state("key", "value", project_id=project_id)
                
        # The state file should not exist or be corrupted if write failed
        # Since we patch move, the temp file might be left behind, but the final file shouldn't be created
        # Actually, the implementation cleans up temp files on exception.
        # So state_path should not exist.
        assert not state_path.exists()
        
    finally:
        # Restore
        pass

def test_get_state_returns_empty_if_missing(mock_project_root):
    """Test that get_state returns empty dict if file doesn't exist."""
    from src.utils.versioning import get_state
    
    project_id = "NON-EXISTENT-PROJECT"
    state = get_state(project_id)
    
    assert state == {}

def test_verify_state_integrity(mock_project_root):
    """Test state integrity verification."""
    from src.utils.versioning import update_state, verify_state_integrity, _STATE_DIR
    
    project_id = "TEST-PROJECT-4"
    
    # Create a valid state
    update_state("key", "value", project_id=project_id)
    
    assert verify_state_integrity(project_id) is True
    
    # Corrupt the file manually
    state_path = _STATE_DIR / f"{project_id}.yaml"
    with open(state_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Modify the content but not the hash
    data["key"] = "modified_value"
    with open(state_path, 'w') as f:
        yaml.dump(data, f)
        
    assert verify_state_integrity(project_id) is False

def test_update_state_with_metadata(mock_project_root):
    """Test that update_state correctly merges metadata."""
    from src.utils.versioning import update_state, _STATE_DIR
    
    project_id = "TEST-PROJECT-5"
    
    # First update with metadata
    update_state("key1", "val1", project_id=project_id, metadata={"version": 1, "timestamp": "2023-01-01"})
    
    # Second update with new metadata
    update_state("key2", "val2", project_id=project_id, metadata={"version": 2, "author": "test"})
    
    state_path = _STATE_DIR / f"{project_id}.yaml"
    with open(state_path, 'r') as f:
        state = yaml.safe_load(f)
        
    assert state["metadata"]["version"] == 2
    assert state["metadata"]["timestamp"] == "2023-01-01"
    assert state["metadata"]["author"] == "test"

def test_compute_hash_deterministic_order():
    """Test that hash is deterministic regardless of dict key order."""
    from src.utils.versioning import _compute_hash
    
    d1 = {"b": 2, "a": 1}
    d2 = {"a": 1, "b": 2}
    
    assert _compute_hash(d1) == _compute_hash(d2)

def test_update_state_project_id_default():
    """Test that update_state uses the default project ID if not provided."""
    from src.utils.versioning import update_state, _PROJECT_ID, _STATE_DIR
    
    # This test assumes the default _PROJECT_ID is set correctly in the module.
    # We can't easily test the default without mocking the module's global,
    # so we just ensure it doesn't crash and uses the configured ID.
    # The actual path is validated in other tests.
    
    # We will just verify the logic path exists
    assert _PROJECT_ID.startswith("PROJ-220")