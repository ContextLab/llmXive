"""
Tests for the versioning module.
"""
import os
import tempfile
import pytest
import yaml
from pathlib import Path

from code.versioning import hash_file, update_project_state
from code.config import DATA_PROCESSED_DIR

@pytest.fixture
def temp_artifact():
    """Creates a temporary file to act as an artifact for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Test artifact content for versioning")
        return f.name

@pytest.fixture
def clean_state_file():
    """Ensures the project state file exists as empty for clean testing."""
    state_file = os.path.join(DATA_PROCESSED_DIR, "project_state.yaml")
    # Backup if exists
    backup = None
    if os.path.exists(state_file):
        backup = state_file + ".bak"
        with open(state_file, "r") as f:
            backup_content = f.read()
        with open(backup, "w") as f:
            f.write(backup_content)
    
    # Ensure directory exists
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    
    # Clear state
    with open(state_file, "w") as f:
        f.write("")
        
    yield state_file
    
    # Restore backup
    if backup and os.path.exists(backup):
        with open(backup, "r") as f:
            restore_content = f.read()
        with open(state_file, "w") as f:
            f.write(restore_content)
        os.remove(backup)
    elif os.path.exists(state_file):
        os.remove(state_file)

def test_hash_file_content(temp_artifact):
    """Tests that hash_file calculates a valid SHA256 hash."""
    h = hash_file(temp_artifact)
    assert len(h) == 64  # SHA256 hex length
    assert all(c in '0123456789abcdef' for c in h)
    
    # Verify determinism
    h2 = hash_file(temp_artifact)
    assert h == h2

def test_hash_file_missing():
    """Tests that hash_file raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        hash_file("/nonexistent/path/file.txt")

def test_update_project_state(temp_artifact, clean_state_file):
    """Tests that update_project_state writes correct YAML entries."""
    artifact_path = temp_artifact
    description = "Test description"
    
    result = update_project_state(artifact_path, description)
    
    # Verify return value
    assert result["description"] == description
    assert result["artifact"] == os.path.abspath(artifact_path)
    assert "hash" in result
    assert "timestamp" in result
    
    # Verify file content
    assert os.path.exists(clean_state_file)
    with open(clean_state_file, "r") as f:
        data = yaml.safe_load(f)
        
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["description"] == description
    assert data[0]["artifact"] == os.path.abspath(artifact_path)
    assert data[0]["hash"] == result["hash"]

def test_update_project_state_append(temp_artifact, clean_state_file):
    """Tests that update_project_state appends to existing state."""
    # First entry
    update_project_state(temp_artifact, "First entry")
    
    # Second entry
    update_project_state(temp_artifact, "Second entry")
    
    with open(clean_state_file, "r") as f:
        data = yaml.safe_load(f)
        
    assert len(data) == 2
    assert data[0]["description"] == "First entry"
    assert data[1]["description"] == "Second entry"
    # Hashes should be identical since content is same
    assert data[0]["hash"] == data[1]["hash"]