import os
import tempfile
import yaml
from pathlib import Path
import pytest

from src.utils.checksum_utils import (
    compute_file_sha256,
    load_state_file,
    save_state_file,
    update_artifact_hash,
)


class TestChecksumUtils:
    def test_compute_file_sha256(self, tmp_path):
        """Test SHA256 computation on a simple file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        hash_val = compute_file_sha256(str(test_file))

        # Verify it's a valid hex string of correct length
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64  # SHA256 produces 64 hex chars
        assert all(c in "0123456789abcdef" for c in hash_val)

    def test_compute_file_sha256_nonexistent(self, tmp_path):
        """Test that computing hash on non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            compute_file_sha256(str(tmp_path / "nonexistent.txt"))

    def test_load_state_file_creates_default(self, tmp_path):
        """Test that load_state_file creates a default structure if missing."""
        state_file = tmp_path / "state.yaml"
        
        # Should create the file and return default structure
        data = load_state_file(str(state_file))
        
        assert state_file.exists()
        assert "project_id" in data
        assert "artifact_hashes" in data
        assert isinstance(data["artifact_hashes"], dict)

    def test_load_state_file_existing(self, tmp_path):
        """Test loading an existing state file."""
        state_file = tmp_path / "state.yaml"
        existing_data = {
            "project_id": "TEST-001",
            "artifact_hashes": {"file.txt": {"sha256": "abc123"}}
        }
        
        with open(state_file, "w") as f:
            yaml.dump(existing_data, f)
        
        loaded = load_state_file(str(state_file))
        
        assert loaded["project_id"] == "TEST-001"
        assert "file.txt" in loaded["artifact_hashes"]

    def test_save_state_file(self, tmp_path):
        """Test saving state data to file."""
        state_file = tmp_path / "state.yaml"
        data = {
            "project_id": "TEST-002",
            "artifact_hashes": {"test.txt": {"sha256": "def456"}}
        }
        
        save_state_file(str(state_file), data)
        
        assert state_file.exists()
        with open(state_file, "r") as f:
            loaded = yaml.safe_load(f)
        
        assert loaded["project_id"] == "TEST-002"
        assert loaded["artifact_hashes"]["test.txt"]["sha256"] == "def456"

    def test_update_artifact_hash(self, tmp_path):
        """Test updating an artifact hash in the state file."""
        state_file = tmp_path / "state.yaml"
        artifact_file = tmp_path / "artifact.txt"
        artifact_file.write_text("test content")
        
        hash_val = update_artifact_hash(str(state_file), str(artifact_file))
        
        # Verify hash is valid
        assert len(hash_val) == 64
        
        # Verify state file was updated
        state = load_state_file(str(state_file))
        assert str(artifact_file) in state["artifact_hashes"]
        assert state["artifact_hashes"][str(artifact_file)]["sha256"] == hash_val

    def test_update_artifact_hash_with_provided_hash(self, tmp_path):
        """Test updating hash with a pre-computed value."""
        state_file = tmp_path / "state.yaml"
        artifact_file = tmp_path / "artifact.txt"
        custom_hash = "0" * 64
        
        update_artifact_hash(str(state_file), str(artifact_file), custom_hash)
        
        state = load_state_file(str(state_file))
        assert state["artifact_hashes"][str(artifact_file)]["sha256"] == custom_hash
