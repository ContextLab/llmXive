"""
Tests for Task T003: Checksum computation and state update.
"""
import pytest
import os
import sys
import hashlib
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
code_dir = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(code_dir))

from update_state_checksum import compute_sha256, update_state_file

class TestT003Checksum:
    """Tests for the checksum logic used in T003."""

    def test_compute_sha256_on_sample_file(self, tmp_path):
        """Test that compute_sha256 returns the correct hash for a known file."""
        # Create a temporary file with known content
        test_file = tmp_path / "test_sample.h5"
        content = b"This is test content for checksum verification."
        test_file.write_bytes(content)
        
        # Compute hash
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(str(test_file))
        
        assert actual_hash == expected_hash, "SHA-256 hash mismatch."

    def test_update_state_file_creates_structure(self, tmp_path):
        """Test that update_state_file creates the nested structure if missing."""
        state_file = tmp_path / "state.yaml"
        file_path = tmp_path / "data.h5"
        file_path.write_bytes(b"dummy")
        
        hash_val = hashlib.sha256(b"dummy").hexdigest()
        
        # Call update
        update_state_file(str(state_file), "artifact_hashes.test_key", hash_val)
        
        assert state_file.exists(), "State file was not created."
        
        with open(state_file, 'r') as f:
            data = yaml.safe_load(f)
        
        assert "artifact_hashes" in data, "artifact_hashes key missing."
        assert data["artifact_hashes"]["test_key"] == hash_val, "Hash value incorrect."
        assert "updated_at" in data, "updated_at timestamp missing."

    def test_update_state_file_preserves_existing_data(self, tmp_path):
        """Test that update_state_file does not overwrite unrelated keys."""
        state_file = tmp_path / "state.yaml"
        initial_data = {
            "project_name": "Test Project",
            "version": 1.0,
            "artifact_hashes": {
                "existing_key": "old_hash_value"
            }
        }
        state_file.write_text(yaml.dump(initial_data))
        
        file_path = tmp_path / "data.h5"
        file_path.write_bytes(b"new_data")
        new_hash = hashlib.sha256(b"new_data").hexdigest()
        
        update_state_file(str(state_file), "artifact_hashes.new_key", new_hash)
        
        with open(state_file, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data["project_name"] == "Test Project", "Existing key overwritten."
        assert data["artifact_hashes"]["existing_key"] == "old_hash_value", "Existing hash overwritten."
        assert data["artifact_hashes"]["new_key"] == new_hash, "New hash not added."