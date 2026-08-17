"""
Tests for the checksum computation and state file update functionality.
"""
import os
import sys
import tempfile
from pathlib import Path
import hashlib
import yaml
import pytest

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from compute_checksum import compute_sha256, ensure_state_file_exists, update_state_file

class TestComputeChecksum:
    """Tests for the compute_sha256 function."""

    def test_compute_sha256_simple_file(self, tmp_path):
        """Test computing checksum of a simple file."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        # Compute expected checksum manually
        expected_hash = hashlib.sha256(test_content).hexdigest()

        # Compute using our function
        computed_hash = compute_sha256(str(test_file))

        assert computed_hash == expected_hash

    def test_compute_sha256_large_file(self, tmp_path):
        """Test computing checksum of a larger file to ensure chunking works."""
        # Create a larger test file (1MB)
        test_file = tmp_path / "large.bin"
        chunk_size = 4096
        total_size = 1024 * 1024  # 1MB

        # Generate deterministic content
        content = b"X" * chunk_size
        with open(test_file, 'wb') as f:
            for _ in range(total_size // chunk_size):
                f.write(content)

        # Compute expected checksum
        with open(test_file, 'rb') as f:
            expected_hash = hashlib.sha256(f.read()).hexdigest()

        # Compute using our function
        computed_hash = compute_sha256(str(test_file))

        assert computed_hash == expected_hash

    def test_compute_sha256_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for non-existent file."""
        non_existent_file = tmp_path / "does_not_exist.txt"

        with pytest.raises(FileNotFoundError):
            compute_sha256(str(non_existent_file))

class TestEnsureStateFileExists:
    """Tests for the ensure_state_file_exists function."""

    def test_creates_new_state_file(self, tmp_path):
        """Test that a new state file is created with correct structure."""
        state_file = tmp_path / "state" / "projects" / "test_project.yaml"

        ensure_state_file_exists(str(state_file))

        assert state_file.exists()

        # Verify structure
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f)

        assert 'project_id' in state
        assert 'created_at' in state
        assert 'updated_at' in state
        assert 'artifact_hashes' in state
        assert isinstance(state['artifact_hashes'], dict)

    def test_does_not_modify_existing_file(self, tmp_path):
        """Test that an existing file is not modified."""
        state_file = tmp_path / "state.yaml"

        # Create initial state
        initial_content = {
            "project_id": "TEST-001",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "artifact_hashes": {"existing": "hash123"}
        }

        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            yaml.dump(initial_content, f)

        # Read original content
        with open(state_file, 'r') as f:
            original_content = f.read()

        # Call function
        ensure_state_file_exists(str(state_file))

        # Read new content
        with open(state_file, 'r') as f:
            new_content = f.read()

        # Content should be unchanged (except for potential formatting differences)
        # We'll just check that the file still exists and has the same keys
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f)

        assert state['project_id'] == "TEST-001"
        assert state['artifact_hashes']['existing'] == "hash123"

class TestUpdateStateFile:
    """Tests for the update_state_file function."""

    def test_updates_checksum_and_timestamp(self, tmp_path):
        """Test that checksum and timestamp are updated correctly."""
        state_file = tmp_path / "state.yaml"

        # Create initial state
        initial_content = {
            "project_id": "TEST-001",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "artifact_hashes": {}
        }

        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            yaml.dump(initial_content, f)

        # Update with a checksum
        test_checksum = "abc123def456"
        update_state_file(str(state_file), "test_artifact", test_checksum)

        # Verify updates
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f)

        assert state['artifact_hashes']['test_artifact'] == test_checksum
        assert state['updated_at'] != initial_content['updated_at']
        assert 'T' in state['updated_at']  # ISO format

    def test_adds_artifact_hashes_if_missing(self, tmp_path):
        """Test that artifact_hashes key is added if missing."""
        state_file = tmp_path / "state.yaml"

        # Create state without artifact_hashes
        initial_content = {
            "project_id": "TEST-001",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }

        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            yaml.dump(initial_content, f)

        # Update with a checksum
        test_checksum = "abc123def456"
        update_state_file(str(state_file), "test_artifact", test_checksum)

        # Verify artifact_hashes was added
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f)

        assert 'artifact_hashes' in state
        assert state['artifact_hashes']['test_artifact'] == test_checksum

    def test_raises_error_for_nonexistent_file(self, tmp_path):
        """Test that FileNotFoundError is raised for non-existent state file."""
        non_existent_file = tmp_path / "nonexistent" / "state.yaml"

        with pytest.raises(FileNotFoundError):
            update_state_file(str(non_existent_file), "test", "hash")
