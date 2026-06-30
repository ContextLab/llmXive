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
    main
)

class TestChecksumUtils:
    def test_compute_file_sha256(self):
        """Test SHA256 computation for a known string."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name

        try:
            # "test content" sha256
            expected_hash = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
            result = compute_file_sha256(temp_path)
            assert result == expected_hash
        finally:
            os.unlink(temp_path)

    def test_load_state_file_creates_default(self):
        """Test that load_state_file creates a default structure if file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, "test_state.yaml")
            
            # File doesn't exist yet
            assert not os.path.exists(state_path)
            
            data = load_state_file(state_path)
            
            assert os.path.exists(state_path)
            assert "project_id" in data
            assert "updated_at" in data
            assert "artifact_hashes" in data
            assert isinstance(data["artifact_hashes"], dict)

    def test_update_artifact_hash(self):
        """Test updating the state file with an artifact hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy artifact
            artifact_path = os.path.join(tmpdir, "dummy_artifact.txt")
            with open(artifact_path, 'w') as f:
                f.write("dummy data")
            
            # Create state file path
            state_path = os.path.join(tmpdir, "state.yaml")
            
            # Update hash
            update_artifact_hash(state_path, artifact_path)
            
            # Verify state file content
            with open(state_path, 'r') as f:
                state_data = yaml.safe_load(f)
            
            assert "artifact_hashes" in state_data
            assert artifact_path in state_data["artifact_hashes"]
            assert "sha256" in state_data["artifact_hashes"][artifact_path]
            
            # Verify the hash is correct
            computed_hash = compute_file_sha256(artifact_path)
            assert state_data["artifact_hashes"][artifact_path]["sha256"] == computed_hash

    def test_update_artifact_hash_missing_file(self):
        """Test that update_artifact_hash raises error for missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, "state.yaml")
            missing_path = os.path.join(tmpdir, "nonexistent.txt")
            
            with pytest.raises(FileNotFoundError):
                update_artifact_hash(state_path, missing_path)

    def test_save_state_file(self):
        """Test saving state data to a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, "test_save.yaml")
            data = {
                "project_id": "test-proj",
                "updated_at": "2023-01-01",
                "artifact_hashes": {"file.txt": {"sha256": "abc123"}}
            }
            
            save_state_file(state_path, data)
            
            assert os.path.exists(state_path)
            
            with open(state_path, 'r') as f:
                loaded_data = yaml.safe_load(f)
            
            assert loaded_data == data
