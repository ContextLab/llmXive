"""
Unit tests for state management utilities.

Tests Constitution Principle IV: Audit Trail & Reproducibility.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import yaml
import shutil

# Import the functions to test
from code.state_utils import (
    ensure_state_structure,
    compute_file_checksum,
    load_project_state,
    save_project_state,
    register_artifact,
    verify_artifact_integrity,
    get_artifact_summary,
    PROJECT_ID,
    STATE_DIR,
    PROJECTS_DIR
)

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    # Create necessary directories
    Path("code").mkdir()
    Path("data").mkdir()
    
    yield temp_dir
    
    # Cleanup
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_ensure_state_structure(temp_project_dir):
    """Test that state directory structure is created."""
    ensure_state_structure()
    
    assert STATE_DIR.exists()
    assert PROJECTS_DIR.exists()
    assert STATE_DIR.is_dir()
    assert PROJECTS_DIR.is_dir()

def test_compute_file_checksum(temp_project_dir):
    """Test checksum computation for a file."""
    # Create a test file
    test_file = Path("data/test_file.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_content = "Hello, World!"
    test_file.write_text(test_content)
    
    checksum = compute_file_checksum(test_file)
    
    # Verify checksum is a valid SHA-256 hash (64 hex characters)
    assert len(checksum) == 64
    assert all(c in '0123456789abcdef' for c in checksum)
    
    # Verify same content produces same checksum
    checksum2 = compute_file_checksum(test_file)
    assert checksum == checksum2

def test_compute_file_checksum_missing_file(temp_project_dir):
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_file_checksum(Path("nonexistent.txt"))

def test_load_project_state_new(temp_project_dir):
    """Test loading state for a new project."""
    state = load_project_state()
    
    assert state["project_id"] == PROJECT_ID
    assert "created_at" in state
    assert "updated_at" in state
    assert "version" in state
    assert state["checksums"] == {}
    assert state["artifacts"] == []
    assert "metadata" in state

def test_save_and_load_project_state(temp_project_dir):
    """Test saving and loading project state."""
    state = load_project_state()
    state["test_key"] = "test_value"
    
    save_project_state(state)
    
    # Reload and verify
    loaded_state = load_project_state()
    assert loaded_state["test_key"] == "test_value"
    assert "updated_at" in loaded_state
    assert loaded_state["updated_at"] != loaded_state["created_at"]

def test_register_artifact(temp_project_dir):
    """Test artifact registration."""
    ensure_state_structure()
    
    # Create a test artifact
    artifact_path = Path("data/test_data.csv")
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("col1,col2\n1,2\n3,4")
    
    # Register the artifact
    result = register_artifact(
        artifact_path,
        artifact_type="data",
        description="Test data file",
        metadata={"source": "test"}
    )
    
    assert result["path"] == str(artifact_path)
    assert result["type"] == "data"
    assert len(result["checksum"]) == 64
    assert "size_bytes" in result
    assert "registered_at" in result
    assert result["description"] == "Test data file"
    
    # Verify artifact is in state
    state = load_project_state()
    assert len(state["artifacts"]) == 1
    assert state["artifacts"][0]["path"] == str(artifact_path)

def test_register_artifact_missing_file(temp_project_dir):
    """Test that FileNotFoundError is raised for missing artifact."""
    with pytest.raises(FileNotFoundError):
        register_artifact(
            Path("nonexistent.csv"),
            artifact_type="data"
        )

def test_verify_artifact_integrity_valid(temp_project_dir):
    """Test integrity verification for valid artifact."""
    ensure_state_structure()
    
    artifact_path = Path("data/test_integrity.csv")
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("test,data")
    
    register_artifact(artifact_path, artifact_type="data")
    
    assert verify_artifact_integrity(artifact_path) is True

def test_verify_artifact_integrity_modified(temp_project_dir):
    """Test integrity verification for modified artifact."""
    ensure_state_structure()
    
    artifact_path = Path("data/test_modified.csv")
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("original,content")
    
    register_artifact(artifact_path, artifact_type="data")
    
    # Modify the file
    artifact_path.write_text("modified,content")
    
    assert verify_artifact_integrity(artifact_path) is False

def test_verify_artifact_integrity_missing(temp_project_dir):
    """Test integrity verification for missing artifact."""
    ensure_state_structure()
    
    artifact_path = Path("data/test_missing.csv")
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Register then delete
    artifact_path.write_text("temp")
    register_artifact(artifact_path, artifact_type="data")
    artifact_path.unlink()
    
    assert verify_artifact_integrity(artifact_path) is False

def test_get_artifact_summary(temp_project_dir):
    """Test artifact summary retrieval."""
    ensure_state_structure()
    
    # Register multiple artifacts
    for i in range(3):
        artifact_path = Path(f"data/artifact_{i}.csv")
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(f"content_{i}")
        register_artifact(artifact_path, artifact_type="data")
    
    summary = get_artifact_summary()
    
    assert len(summary) == 3
    for i, entry in enumerate(summary):
        assert entry["path"] == f"data/artifact_{i}.csv"
        assert entry["type"] == "data"

def test_state_yaml_structure(temp_project_dir):
    """Test that the state YAML file has correct structure."""
    ensure_state_structure()
    
    # Create and register an artifact
    artifact_path = Path("data/test.yaml_structure.csv")
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("test")
    register_artifact(artifact_path, artifact_type="data")
    
    # Load the YAML file directly
    state_file = PROJECTS_DIR / f"{PROJECT_ID}.yaml"
    with open(state_file, 'r') as f:
        yaml_content = yaml.safe_load(f)
    
    # Verify structure
    assert "project_id" in yaml_content
    assert "created_at" in yaml_content
    assert "updated_at" in yaml_content
    assert "version" in yaml_content
    assert "checksums" in yaml_content
    assert "artifacts" in yaml_content
    assert "metadata" in yaml_content
    
    # Verify artifact entry structure
    assert len(yaml_content["artifacts"]) > 0
    artifact_entry = yaml_content["artifacts"][0]
    assert "path" in artifact_entry
    assert "type" in artifact_entry
    assert "checksum" in artifact_entry
    assert "size_bytes" in artifact_entry
    assert "registered_at" in artifact_entry
    assert "description" in artifact_entry
    assert "metadata" in artifact_entry