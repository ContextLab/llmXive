"""
Tests for the state_manager module (Constitution Principle V).
"""
import os
import sys
import yaml
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from state_manager import (
    load_state,
    save_state,
    compute_file_hash,
    register_artifact,
    update_artifact,
    verify_artifact_integrity,
    get_artifact_history,
    list_all_artifacts
)

@pytest.fixture
def temp_state_dir():
    """Create a temporary directory for testing state management."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield Path(temp_dir)
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_file(temp_state_dir):
    """Create a sample file for testing."""
    file_path = temp_state_dir / "sample.txt"
    file_path.write_text("Hello, World!")
    return file_path

@pytest.fixture
def sample_artifact(temp_state_dir):
    """Create a sample artifact file."""
    artifact_path = temp_state_dir / "data" / "processed" / "test_artifact.csv"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("col1,col2\n1,2\n3,4\n")
    return artifact_path

def test_compute_file_hash(sample_file):
    """Test that file hash is computed correctly."""
    hash1 = compute_file_hash(sample_file)
    hash2 = compute_file_hash(sample_file)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length
    assert hash1.islower()

def test_compute_file_hash_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    non_existent = Path("non_existent_file.txt")
    with pytest.raises(FileNotFoundError):
        compute_file_hash(non_existent)

def test_load_state_empty(temp_state_dir):
    """Test loading state when file doesn't exist."""
    state = load_state()
    
    assert "metadata" in state
    assert "artifacts" in state
    assert state["metadata"]["project"] == "PROJ-334-predicting-avian-song-variation-with-cli"
    assert "created_at" in state["metadata"]

def test_load_state_existing(temp_state_dir):
    """Test loading state when file exists."""
    state_path = temp_state_dir / "state.yaml"
    initial_state = {
        "metadata": {
            "project": "test-project",
            "created_at": "2023-01-01T00:00:00",
            "last_updated": None
        },
        "artifacts": {
            "test.txt": {"path": "test.txt", "hash": "abc123"}
        }
    }
    
    with open(state_path, "w") as f:
        yaml.dump(initial_state, f)
    
    loaded = load_state(state_path)
    
    assert loaded["metadata"]["project"] == "test-project"
    assert "test.txt" in loaded["artifacts"]

def test_save_state(temp_state_dir):
    """Test saving state to file."""
    state_path = temp_state_dir / "state.yaml"
    test_state = {
        "metadata": {
            "project": "test",
            "created_at": "2023-01-01",
            "last_updated": None
        },
        "artifacts": {}
    }
    
    save_state(test_state, state_path)
    
    assert state_path.exists()
    
    with open(state_path, "r") as f:
        saved = yaml.safe_load(f)
    
    assert saved["metadata"]["project"] == "test"

def test_register_artifact(sample_artifact):
    """Test registering a new artifact."""
    entry = register_artifact(
        sample_artifact,
        artifact_type="csv",
        description="Test artifact",
        task_id="T008"
    )
    
    assert entry["path"] == str(sample_artifact.relative_to(Path.cwd()))
    assert entry["hash"] is not None
    assert entry["size_bytes"] > 0
    assert entry["type"] == "csv"
    assert entry["task_id"] == "T008"
    assert "created_at" in entry
    
    # Verify it's in the state file
    state = load_state()
    assert entry["path"] in state["artifacts"]

def test_register_artifact_not_found():
    """Test that FileNotFoundError is raised for missing artifacts."""
    with pytest.raises(FileNotFoundError):
        register_artifact(
            Path("non_existent.csv"),
            "csv",
            "Test",
            "T008"
        )

def test_update_artifact(sample_artifact):
    """Test updating an existing artifact."""
    # First register
    register_artifact(
        sample_artifact,
        "csv",
        "Test",
        "T008"
    )
    
    # Modify the file
    sample_artifact.write_text("col1,col2\n5,6\n7,8\n")
    
    # Update
    updated = update_artifact(sample_artifact)
    
    assert updated["path"] == str(sample_artifact.relative_to(Path.cwd()))
    assert "last_modified" in updated

def test_update_artifact_not_registered(temp_state_dir):
    """Test that KeyError is raised for unregistered artifacts."""
    file_path = temp_state_dir / "unregistered.txt"
    file_path.write_text("test")
    
    with pytest.raises(KeyError):
        update_artifact(file_path)

def test_verify_artifact_integrity(sample_artifact):
    """Test artifact integrity verification."""
    # Register
    register_artifact(
        sample_artifact,
        "csv",
        "Test",
        "T008"
    )
    
    # Verify should pass
    assert verify_artifact_integrity(sample_artifact) is True
    
    # Modify and verify should fail
    sample_artifact.write_text("modified")
    assert verify_artifact_integrity(sample_artifact) is False

def test_verify_artifact_not_found():
    """Test verification of non-existent file."""
    assert verify_artifact_integrity(Path("non_existent.txt")) is False

def test_get_artifact_history(sample_artifact):
    """Test retrieving artifact history."""
    register_artifact(
        sample_artifact,
        "csv",
        "Test",
        "T008"
    )
    
    history = get_artifact_history(sample_artifact)
    
    assert history is not None
    assert history["task_id"] == "T008"

def test_get_artifact_history_not_found():
    """Test retrieving history for unregistered artifact."""
    history = get_artifact_history(Path("non_existent.txt"))
    assert history is None

def test_list_all_artifacts(sample_artifact):
    """Test listing all artifacts."""
    register_artifact(
        sample_artifact,
        "csv",
        "Test",
        "T008"
    )
    
    artifacts = list_all_artifacts()
    
    assert len(artifacts) == 1
    assert artifacts[0]["task_id"] == "T008"

def test_list_all_artifacts_by_task_id(sample_artifact):
    """Test listing artifacts filtered by task ID."""
    register_artifact(
        sample_artifact,
        "csv",
        "Test",
        "T008"
    )
    
    # Register another with different task ID
    another_path = sample_artifact.parent / "another.csv"
    another_path.write_text("a,b\n1,2\n")
    register_artifact(
        another_path,
        "csv",
        "Another",
        "T009"
    )
    
    t008_artifacts = list_all_artifacts(task_id="T008")
    t009_artifacts = list_all_artifacts(task_id="T009")
    
    assert len(t008_artifacts) == 1
    assert len(t009_artifacts) == 1
    assert t008_artifacts[0]["task_id"] == "T008"
    assert t009_artifacts[0]["task_id"] == "T009"
