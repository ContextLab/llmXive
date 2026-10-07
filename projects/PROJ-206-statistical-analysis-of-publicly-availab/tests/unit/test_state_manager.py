"""
Unit tests for the state_manager module.
"""
import os
import tempfile
import hashlib
from pathlib import Path
import pytest
import yaml
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.state_manager import (
    compute_file_hash,
    get_state_file_path,
    load_state,
    update_state_artifact,
    verify_artifact_integrity
)
from src.utils.config import get_project_root

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_compute_file_hash(temp_dir):
    """Test SHA-256 hash computation."""
    test_file = temp_dir / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)
    
    expected_hash = hashlib.sha256(test_content).hexdigest()
    actual_hash = compute_file_hash(test_file)
    
    assert actual_hash == expected_hash
    assert len(actual_hash) == 64  # SHA-256 hex length

def test_compute_file_hash_nonexistent():
    """Test hash computation on non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        compute_file_hash(Path("/nonexistent/file.txt"))

def test_get_state_file_path(temp_dir, monkeypatch):
    """Test state file path generation."""
    # Mock the state root
    monkeypatch.setattr("src.utils.state_manager.get_state_root", lambda: temp_dir)
    
    state_path = get_state_file_path("TEST-PROJECT")
    assert state_path == temp_dir / "TEST-PROJECT.yaml"

def test_load_state_empty(temp_dir, monkeypatch):
    """Test loading non-existent state file."""
    monkeypatch.setattr("src.utils.state_manager.get_state_root", lambda: temp_dir)
    monkeypatch.setattr("src.utils.state_manager.get_project_root", lambda: temp_dir)
    
    state = load_state()
    
    assert "project_id" in state
    assert "artifacts" in state
    assert isinstance(state["artifacts"], dict)

def test_load_state_existing(temp_dir, monkeypatch):
    """Test loading existing state file."""
    monkeypatch.setattr("src.utils.state_manager.get_state_root", lambda: temp_dir)
    monkeypatch.setattr("src.utils.state_manager.get_project_root", lambda: temp_dir)
    
    # Create a state file
    state_file = temp_dir / "TEST-PROJECT.yaml"
    initial_state = {
        "project_id": "TEST-PROJECT",
        "artifacts": {"existing.txt": {"path": "existing.txt", "type": "txt"}}
    }
    with open(state_file, "w") as f:
        yaml.dump(initial_state, f)
    
    state = load_state(state_file)
    
    assert state["artifacts"]["existing.txt"]["type"] == "txt"

def test_update_state_artifact(temp_dir, monkeypatch):
    """Test updating state with a new artifact."""
    monkeypatch.setattr("src.utils.state_manager.get_state_root", lambda: temp_dir)
    monkeypatch.setattr("src.utils.state_manager.get_project_root", lambda: temp_dir)
    
    # Create a test artifact
    artifact_file = temp_dir / "data" / "test.csv"
    artifact_file.parent.mkdir(parents=True, exist_ok=True)
    artifact_file.write_text("col1,col2\n1,2\n")
    
    # Update state
    state = update_state_artifact(artifact_file, "csv")
    
    artifact_key = str(artifact_file.relative_to(temp_dir))
    assert artifact_key in state["artifacts"]
    assert state["artifacts"][artifact_key]["type"] == "csv"
    assert "sha256" in state["artifacts"][artifact_key]
    assert "size_bytes" in state["artifacts"][artifact_key]

def test_update_state_artifact_missing_file(temp_dir):
    """Test updating state with non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        update_state_artifact(Path("/nonexistent/file.csv"), "csv")

def test_verify_artifact_integrity_success(temp_dir, monkeypatch):
    """Test successful artifact verification."""
    monkeypatch.setattr("src.utils.state_manager.get_state_root", lambda: temp_dir)
    monkeypatch.setattr("src.utils.state_manager.get_project_root", lambda: temp_dir)
    
    # Create and hash a file
    artifact_file = temp_dir / "verify_test.txt"
    content = b"Verification test"
    artifact_file.write_bytes(content)
    
    expected_hash = hashlib.sha256(content).hexdigest()
    
    result = verify_artifact_integrity(artifact_file, expected_hash)
    assert result is True

def test_verify_artifact_integrity_failure(temp_dir, monkeypatch):
    """Test failed artifact verification with wrong hash."""
    monkeypatch.setattr("src.utils.state_manager.get_state_root", lambda: temp_dir)
    monkeypatch.setattr("src.utils.state_manager.get_project_root", lambda: temp_dir)
    
    artifact_file = temp_dir / "verify_test2.txt"
    artifact_file.write_text("Test content")
    
    result = verify_artifact_integrity(artifact_file, "wrong_hash_value")
    assert result is False
