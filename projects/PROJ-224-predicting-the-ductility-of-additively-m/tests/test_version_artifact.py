"""
Tests for the artifact versioning functionality.
"""
import os
import sys
import tempfile
import hashlib
import pytest
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.version_artifact import compute_sha256, ensure_state_file, save_state, version_artifact


class TestComputeSha256:
    """Tests for the compute_sha256 function."""

    def test_compute_sha256_basic(self, tmp_path):
        """Test basic SHA-256 computation."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(test_file)

        assert actual_hash == expected_hash
        assert len(actual_hash) == 64  # SHA-256 hex length

    def test_compute_sha256_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing files."""
        missing_file = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            compute_sha256(missing_file)

    def test_compute_sha256_large_file(self, tmp_path):
        """Test computation on a larger file to ensure chunking works."""
        test_file = tmp_path / "large.txt"
        # Write 1MB of data
        content = b"x" * (1024 * 1024)
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(test_file)

        assert actual_hash == expected_hash


class TestEnsureStateFile:
    """Tests for the ensure_state_file function."""

    def test_creates_new_file(self, tmp_path):
        """Test that a new state file is created if it doesn't exist."""
        state_file = tmp_path / "state.yaml"

        state_data = ensure_state_file(state_file)

        assert state_data == {"artifact_hashes": {}}
        assert state_file.exists()

    def test_loads_existing_file(self, tmp_path):
        """Test loading an existing state file."""
        state_file = tmp_path / "state.yaml"
        initial_data = {"artifact_hashes": {"key1": "hash1"}}

        # Write initial data
        import yaml
        with open(state_file, 'w') as f:
            yaml.dump(initial_data, f)

        state_data = ensure_state_file(state_file)

        assert state_data == initial_data

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        state_file = tmp_path / "sub" / "dir" / "state.yaml"

        state_data = ensure_state_file(state_file)

        assert state_file.exists()
        assert state_data == {"artifact_hashes": {}}

    def test_handles_empty_file(self, tmp_path):
        """Test handling of an empty YAML file."""
        state_file = tmp_path / "state.yaml"
        state_file.write_text("")

        state_data = ensure_state_file(state_file)

        assert state_data == {"artifact_hashes": {}}

    def test_handles_missing_artifact_hashes_key(self, tmp_path):
        """Test handling of a file missing the artifact_hashes key."""
        state_file = tmp_path / "state.yaml"
        import yaml
        with open(state_file, 'w') as f:
            yaml.dump({"other_key": "value"}, f)

        state_data = ensure_state_file(state_file)

        assert "artifact_hashes" in state_data
        assert state_data["artifact_hashes"] == {}


class TestSaveState:
    """Tests for the save_state function."""

    def test_saves_valid_data(self, tmp_path):
        """Test saving valid state data."""
        state_file = tmp_path / "state.yaml"
        state_data = {"artifact_hashes": {"key1": "hash1"}}

        save_state(state_file, state_data)

        assert state_file.exists()

        import yaml
        with open(state_file, 'r') as f:
            loaded_data = yaml.safe_load(f)

        assert loaded_data == state_data

    def test_overwrites_existing_file(self, tmp_path):
        """Test that save_state overwrites existing files."""
        state_file = tmp_path / "state.yaml"
        import yaml
        initial_data = {"artifact_hashes": {"old": "hash"}}
        with open(state_file, 'w') as f:
            yaml.dump(initial_data, f)

        new_data = {"artifact_hashes": {"new": "hash2"}}
        save_state(state_file, new_data)

        with open(state_file, 'r') as f:
            loaded_data = yaml.safe_load(f)

        assert loaded_data == new_data


class TestVersionArtifact:
    """Tests for the version_artifact function."""

    def test_versions_existing_file(self, tmp_path):
        """Test versioning an existing artifact."""
        artifact_file = tmp_path / "artifact.csv"
        state_file = tmp_path / "state.yaml"
        content = b"col1,col2\n1,2\n"
        artifact_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()

        actual_hash = version_artifact(artifact_file, state_file)

        assert actual_hash == expected_hash

        import yaml
        with open(state_file, 'r') as f:
            state_data = yaml.safe_load(f)

        assert state_data["artifact_hashes"][str(artifact_file)] == expected_hash

    def test_versions_with_custom_key(self, tmp_path):
        """Test versioning with a custom key name."""
        artifact_file = tmp_path / "artifact.csv"
        state_file = tmp_path / "state.yaml"
        content = b"data"
        artifact_file.write_bytes(content)

        custom_key = "my_custom_key"
        version_artifact(artifact_file, state_file, key_name=custom_key)

        import yaml
        with open(state_file, 'r') as f:
            state_data = yaml.safe_load(f)

        assert custom_key in state_data["artifact_hashes"]

    def test_raises_on_missing_artifact(self, tmp_path):
        """Test that FileNotFoundError is raised for missing artifacts."""
        missing_file = tmp_path / "missing.csv"
        state_file = tmp_path / "state.yaml"

        with pytest.raises(FileNotFoundError):
            version_artifact(missing_file, state_file)

    def test_updates_existing_hash(self, tmp_path):
        """Test that version_artifact updates an existing hash."""
        artifact_file = tmp_path / "artifact.csv"
        state_file = tmp_path / "state.yaml"

        # First version
        content1 = b"v1"
        artifact_file.write_bytes(content1)
        hash1 = version_artifact(artifact_file, state_file)

        # Change content
        content2 = b"v2"
        artifact_file.write_bytes(content2)
        hash2 = version_artifact(artifact_file, state_file)

        assert hash1 != hash2

        import yaml
        with open(state_file, 'r') as f:
            state_data = yaml.safe_load(f)

        assert state_data["artifact_hashes"][str(artifact_file)] == hash2

    def test_verification_failure(self, tmp_path, monkeypatch):
        """Test that ValueError is raised if verification fails."""
        artifact_file = tmp_path / "artifact.csv"
        state_file = tmp_path / "state.yaml"
        content = b"data"
        artifact_file.write_bytes(content)

        # Mock save_state to return a modified hash to simulate failure
        original_save_state = None
        import data.version_artifact as va_module

        def mock_save_state(path, data):
            # Corrupt the hash in the saved data
            if "artifact_hashes" in data:
                for k in data["artifact_hashes"]:
                    data["artifact_hashes"][k] = "corrupted_hash"

        monkeypatch.setattr(va_module, 'save_state', mock_save_state)

        with pytest.raises(ValueError, match="Hash verification failed"):
            version_artifact(artifact_file, state_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])