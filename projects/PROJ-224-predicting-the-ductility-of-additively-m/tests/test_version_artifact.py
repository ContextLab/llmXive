import os
import sys
import tempfile
import hashlib
import pytest
from pathlib import Path
import yaml

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.version_artifact import compute_sha256, ensure_state_file, save_state, version_artifact


class TestComputeSha256:
    def test_compute_sha256_valid_file(self, tmp_path):
        """Test hashing a valid file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(str(test_file))

        assert actual_hash == expected_hash

    def test_compute_sha256_missing_file(self):
        """Test that hashing a missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            compute_sha256("/nonexistent/path/file.txt")

    def test_compute_sha256_large_file(self, tmp_path):
        """Test hashing a larger file."""
        test_file = tmp_path / "large.txt"
        content = b"0" * 1024 * 1024  # 1MB
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(str(test_file))

        assert actual_hash == expected_hash


class TestEnsureStateFile:
    def test_creates_new_file(self, tmp_path):
        """Test that a new state file is created if it doesn't exist."""
        state_file = tmp_path / "state.yaml"
        state_data = ensure_state_file(state_file)

        assert state_file.exists()
        assert "artifact_hashes" in state_data
        assert state_data["artifact_hashes"] == {}

    def test_loads_existing_file(self, tmp_path):
        """Test that an existing state file is loaded correctly."""
        state_file = tmp_path / "state.yaml"
        initial_data = {
            "project_id": "TEST-001",
            "artifact_hashes": {"data/test.csv": "abc123"}
        }
        with open(state_file, "w") as f:
            yaml.dump(initial_data, f)

        loaded_data = ensure_state_file(state_file)

        assert loaded_data["project_id"] == "TEST-001"
        assert loaded_data["artifact_hashes"]["data/test.csv"] == "abc123"

    def test_handles_corrupted_file(self, tmp_path):
        """Test handling of a corrupted YAML file."""
        state_file = tmp_path / "state.yaml"
        state_file.write_text("invalid: yaml: content: [")

        with pytest.raises(yaml.YAMLError):
            ensure_state_file(state_file)


class TestVersionArtifact:
    def test_version_artifact_creates_file(self, tmp_path):
        """Test that versioning creates the state file if it doesn't exist."""
        artifact_file = tmp_path / "data" / "test.csv"
        artifact_file.parent.mkdir()
        artifact_file.write_text("col1,col2\n1,2")

        state_file = tmp_path / "state.yaml"

        version_artifact(str(artifact_file), str(state_file))

        assert state_file.exists()
        with open(state_file, "r") as f:
            state_data = yaml.safe_load(f)
            assert "artifact_hashes" in state_data

    def test_version_artifact_updates_hash(self, tmp_path):
        """Test that versioning updates the hash correctly."""
        artifact_file = tmp_path / "data" / "test.csv"
        artifact_file.parent.mkdir()
        content = b"col1,col2\n1,2"
        artifact_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        state_file = tmp_path / "state.yaml"

        version_artifact(str(artifact_file), str(state_file))

        with open(state_file, "r") as f:
            state_data = yaml.safe_load(f)
            assert state_data["artifact_hashes"][str(artifact_file)] == expected_hash

    def test_version_artifact_missing_file(self, tmp_path):
        """Test that versioning raises error for missing file."""
        state_file = tmp_path / "state.yaml"
        missing_file = tmp_path / "data" / "missing.csv"

        with pytest.raises(FileNotFoundError):
            version_artifact(str(missing_file), str(state_file))

    def test_version_artifact_verification_fails(self, tmp_path, monkeypatch):
        """Test that versioning raises error if verification fails."""
        artifact_file = tmp_path / "data" / "test.csv"
        artifact_file.parent.mkdir()
        artifact_file.write_text("data")

        state_file = tmp_path / "state.yaml"

        # Mock save_state to corrupt the saved hash
        original_save_state = save_state
        def mock_save_state(path, data):
            data["artifact_hashes"]["data/test.csv"] = "fake_hash"
            original_save_state(path, data)

        monkeypatch.setattr("code.data.version_artifact.save_state", mock_save_state)

        with pytest.raises(ValueError, match="Verification failed"):
            version_artifact(str(artifact_file), str(state_file))