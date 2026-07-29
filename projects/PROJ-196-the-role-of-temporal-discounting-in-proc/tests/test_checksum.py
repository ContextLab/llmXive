"""
Tests for the checksum verification utility (T009).
"""
import os
import tempfile
import yaml
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.checksum import (
    ensure_state_file,
    calculate_file_hash,
    update_artifact_hash,
    verify_artifacts,
    update_all_artifacts_in_directory,
    get_state,
    clear_artifact_hashes,
    PROJECT_ROOT
)

@pytest.fixture
def temp_state_dir(tmp_path):
    """Create a temporary directory structure mimicking the project state."""
    state_dir = tmp_path / "state" / "projects"
    state_dir.mkdir(parents=True)
    return state_dir

@pytest.fixture
def sample_artifact(tmp_path):
    """Create a sample artifact file."""
    artifact_path = tmp_path / "test_data.csv"
    content = "id,value\n1,10\n2,20\n"
    with open(artifact_path, "w") as f:
        f.write(content)
    return artifact_path

def test_calculate_file_hash(sample_artifact):
    """Test that hash is calculated correctly and consistently."""
    hash1 = calculate_file_hash(str(sample_artifact))
    hash2 = calculate_file_hash(str(sample_artifact))
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length
    assert all(c in '0123456789abcdef' for c in hash1)

def test_calculate_file_hash_nonexistent():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        calculate_file_hash("/nonexistent/path/file.csv")

def test_update_artifact_hash_integration(tmp_path, monkeypatch):
    """Test updating the state file with a new artifact hash."""
    # Setup temporary state file location
    state_file = tmp_path / "state.yaml"
    monkeypatch.setattr("code.utils.checksum.STATE_FILE", str(state_file))
    monkeypatch.setattr("code.utils.checksum.PROJECT_ROOT", str(tmp_path))
    
    # Create artifact
    artifact = tmp_path / "data" / "test.csv"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("col1,col2\n1,2\n")
    
    # Update hash
    update_artifact_hash(str(artifact), "Test artifact")
    
    # Verify state file content
    assert state_file.exists()
    with open(state_file, "r") as f:
        state = yaml.safe_load(f)
    
    assert "artifact_hashes" in state
    assert "data/test.csv" in state["artifact_hashes"]
    assert "hash" in state["artifact_hashes"]["data/test.csv"]
    assert state["artifact_hashes"]["data/test.csv"]["description"] == "Test artifact"

def test_verify_artifacts(tmp_path, monkeypatch):
    """Test artifact verification logic."""
    state_file = tmp_path / "state.yaml"
    monkeypatch.setattr("code.utils.checksum.STATE_FILE", str(state_file))
    monkeypatch.setattr("code.utils.checksum.PROJECT_ROOT", str(tmp_path))
    
    # Create artifact
    artifact = tmp_path / "data" / "verify_test.csv"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("x\n1\n")
    
    # Add to state manually
    update_artifact_hash(str(artifact))
    
    # Verify - should be True
    results = verify_artifacts()
    assert results.get("data/verify_test.csv") is True
    
    # Modify file
    artifact.write_text("x\n999\n")
    
    # Verify - should be False
    results = verify_artifacts()
    assert results.get("data/verify_test.csv") is False

def test_update_all_artifacts_in_directory(tmp_path, monkeypatch):
    """Test batch updating of artifacts in a directory."""
    state_file = tmp_path / "state.yaml"
    monkeypatch.setattr("code.utils.checksum.STATE_FILE", str(state_file))
    monkeypatch.setattr("code.utils.checksum.PROJECT_ROOT", str(tmp_path))
    
    # Create directory with multiple files
    data_dir = tmp_path / "data" / "raw"
    data_dir.mkdir(parents=True)
    (data_dir / "file1.csv").write_text("1")
    (data_dir / "file2.csv").write_text("2")
    (data_dir / "file3.txt").write_text("3") # Should be ignored if pattern is csv
    
    count = update_all_artifacts_in_directory("data/raw", "*.csv")
    
    assert count == 2
    
    state = get_state()
    assert "data/raw/file1.csv" in state["artifact_hashes"]
    assert "data/raw/file2.csv" in state["artifact_hashes"]
    assert "data/raw/file3.txt" not in state["artifact_hashes"]

def test_clear_artifact_hashes(tmp_path, monkeypatch):
    """Test clearing all hashes."""
    state_file = tmp_path / "state.yaml"
    monkeypatch.setattr("code.utils.checksum.STATE_FILE", str(state_file))
    monkeypatch.setattr("code.utils.checksum.PROJECT_ROOT", str(tmp_path))
    
    # Add some data
    artifact = tmp_path / "test.csv"
    artifact.write_text("1")
    update_artifact_hash(str(artifact))
    
    # Clear
    clear_artifact_hashes()
    
    state = get_state()
    assert state["artifact_hashes"] == {}
    assert state["status"] == "cleared"
