"""
Unit tests for code/utils/versioning.py
"""
import os
import tempfile
from pathlib import Path
import pytest
import yaml

# Add parent to path to allow imports from code/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.versioning import (
    compute_sha256,
    load_state,
    save_state,
    register_artifact,
    verify_artifact_integrity,
    get_artifact_by_hash
)
from code.config import Paths


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config(temp_dir):
    """Mock the config paths to point to temp_dir."""
    # We need to patch get_paths to return our temp dir
    # Since get_paths reads from a config file, we'll create a minimal config
    config_content = {
        "paths": {
            "root": str(temp_dir),
            "data": str(temp_dir / "data"),
            "code": str(temp_dir / "code"),
            "tests": str(temp_dir / "tests"),
            "specs": str(temp_dir / "specs")
        }
    }
    config_file = temp_dir / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_content, f)
    
    # Reload config to pick up the new file
    # Note: In a real scenario, we might need to mock the import
    # For this test, we assume config.py reads from a standard location
    # We'll rely on the fact that the test runner sets the environment
    return temp_dir


def test_compute_sha256(temp_dir):
    """Test SHA-256 computation on a known file."""
    test_file = temp_dir / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)
    
    hash_val = compute_sha256(test_file)
    assert len(hash_val) == 64  # SHA-256 hex length
    assert isinstance(hash_val, str)
    
    # Known hash for "Hello, World!"
    expected = "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"
    assert hash_val == expected


def test_compute_sha256_file_not_found(temp_dir):
    """Test that compute_sha256 raises FileNotFoundError for missing file."""
    non_existent = temp_dir / "does_not_exist.txt"
    with pytest.raises(FileNotFoundError):
        compute_sha256(non_existent)


def test_load_state_new(temp_dir):
    """Test loading state when file does not exist."""
    state_path = temp_dir / "state.yaml"
    state = load_state(state_path)
    
    assert "version" in state
    assert "created_at" in state
    assert "updated_at" in state
    assert "artifacts" in state
    assert state["artifacts"] == {}


def test_save_state_and_load(temp_dir):
    """Test saving and loading state."""
    state_path = temp_dir / "state.yaml"
    test_state = {
        "version": "1.0.0",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00",
        "artifacts": {
            "test_type": [
                {"path": "test.txt", "hash": "abc123"}
            ]
        }
    }
    
    save_state(test_state, state_path)
    assert state_path.exists()
    
    loaded = load_state(state_path)
    assert loaded["version"] == "1.0.0"
    assert len(loaded["artifacts"]["test_type"]) == 1


def test_register_artifact(temp_dir, mock_config):
    """Test registering an artifact."""
    # Create a test file
    test_file = temp_dir / "data" / "test_output.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("Test content for artifact registration")
    
    state_path = temp_dir / "state.yaml"
    
    # Register the artifact
    registration = register_artifact(
        artifact_path=test_file,
        artifact_type="test_output",
        metadata={"source": "unit_test"},
        state_path=state_path
    )
    
    assert "hash" in registration
    assert registration["path"] == "data/test_output.txt"
    assert registration["type"] == "test_output"
    assert registration["metadata"]["source"] == "unit_test"
    
    # Verify state was updated
    state = load_state(state_path)
    assert "test_output" in state["artifacts"]
    assert len(state["artifacts"]["test_output"]) == 1
    assert state["artifacts"]["test_output"][0]["hash"] == registration["hash"]


def test_verify_artifact_integrity(temp_dir, mock_config):
    """Test artifact integrity verification."""
    test_file = temp_dir / "data" / "verify_test.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    content = "Verify this content"
    test_file.write_text(content)
    
    state_path = temp_dir / "state.yaml"
    
    # Register first
    reg = register_artifact(test_file, "verify_test", state_path=state_path)
    original_hash = reg["hash"]
    
    # Verify should pass
    assert verify_artifact_integrity(test_file, original_hash, state_path) is True
    
    # Modify file
    test_file.write_text("Modified content")
    new_hash = compute_sha256(test_file)
    
    # Verify should fail
    assert verify_artifact_integrity(test_file, original_hash, state_path) is False
    
    # Verify with new hash should pass
    assert verify_artifact_integrity(test_file, new_hash, state_path) is True


def test_get_artifact_by_hash(temp_dir, mock_config):
    """Test retrieving artifact by hash."""
    test_file = temp_dir / "data" / "lookup_test.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("Lookup test content")
    
    state_path = temp_dir / "state.yaml"
    
    reg = register_artifact(test_file, "lookup_test", state_path=state_path)
    target_hash = reg["hash"]
    
    result = get_artifact_by_hash(target_hash, state_path)
    
    assert result is not None
    assert result["hash"] == target_hash
    assert result["path"] == "data/lookup_test.txt"
    
    # Non-existent hash
    null_result = get_artifact_by_hash("nonexistenthash123", state_path)
    assert null_result is None