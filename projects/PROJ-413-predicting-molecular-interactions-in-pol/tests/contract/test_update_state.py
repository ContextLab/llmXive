"""
Contract test for updating project state with curated dataset hash.

Verifies that the update logic correctly computes a hash and updates the state file.
"""
import os
import sys
import tempfile
import hashlib
from pathlib import Path
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.hash_state import compute_sha256, update_state_yaml
from utils.exceptions import DataError

def test_compute_sha256():
    """Test that SHA256 computation is deterministic and correct."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = Path(f.name)

    try:
        hash1 = compute_sha256(temp_path)
        hash2 = compute_sha256(temp_path)
        assert hash1 == hash2, "Hash computation should be deterministic"
        assert len(hash1) == 64, "SHA256 hex digest should be 64 characters"
    finally:
        temp_path.unlink()

def test_update_state_yaml():
    """Test that state YAML is created and updated correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "state.yaml"
        artifact_name = "test_artifact.csv"
        fake_hash = "a" * 64

        # Update non-existent file
        update_state_yaml(state_file, artifact_name, fake_hash)

        assert state_file.exists(), "State file should be created"

        with open(state_file, 'r') as f:
            data = yaml.safe_load(f)

        assert "artifacts" in data, "State should contain 'artifacts' key"
        assert artifact_name in data["artifacts"], f"State should contain entry for {artifact_name}"
        assert data["artifacts"][artifact_name] == fake_hash, "Hash should match input"

def test_update_state_yaml_existing():
    """Test that existing state is preserved and updated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "state.yaml"
        
        # Initialize with some data
        initial_data = {
            "project": "test",
            "artifacts": {
                "old_artifact.csv": "old_hash_value"
            }
        }
        with open(state_file, 'w') as f:
            yaml.dump(initial_data, f)

        new_artifact = "new_artifact.csv"
        new_hash = "b" * 64

        update_state_yaml(state_file, new_artifact, new_hash)

        with open(state_file, 'r') as f:
            data = yaml.safe_load(f)

        assert data["project"] == "test", "Existing top-level keys should be preserved"
        assert "old_artifact.csv" in data["artifacts"], "Existing artifacts should be preserved"
        assert data["artifacts"]["old_artifact.csv"] == "old_hash_value", "Existing hashes should be preserved"
        assert new_artifact in data["artifacts"], "New artifact should be added"
        assert data["artifacts"][new_artifact] == new_hash, "New hash should be set"
