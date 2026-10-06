"""
Unit tests for the state_manager module.
"""
import os
import tempfile
from pathlib import Path
import pytest
import yaml

from code.utils.state_manager import (
    StateError,
    compute_sha256,
    load_state,
    save_state,
    update_artifact_state,
    compute_and_update_hash,
    verify_artifact
)


class TestStateManager:
    @pytest.fixture
    def temp_state_dir(self):
        """Create a temporary directory for state files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "project_state.yaml"
            yield str(state_path)

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for hashing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("col1,col2\nval1,val2\n")
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    def test_compute_sha256(self, temp_file):
        """Test SHA-256 computation."""
        hash_val = compute_sha256(temp_file)
        assert len(hash_val) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in hash_val)

    def test_compute_sha256_missing_file(self):
        """Test SHA-256 computation on missing file raises error."""
        with pytest.raises(StateError, match="File not found"):
            compute_sha256("/nonexistent/path/file.csv")

    def test_load_state_new(self, temp_state_dir):
        """Test loading a non-existent state file returns empty artifacts."""
        state = load_state(temp_state_dir)
        assert state == {"artifacts": {}}

    def test_load_state_existing(self, temp_state_dir, temp_file):
        """Test loading an existing state file."""
        # First, create a state
        state = {"artifacts": {"test.csv": {"hash": "abc123", "timestamp": "2026-01-01"}}}
        save_state(state, temp_state_dir)

        # Load it back
        loaded_state = load_state(temp_state_dir)
        assert loaded_state["artifacts"]["test.csv"]["hash"] == "abc123"

    def test_update_artifact_state(self):
        """Test updating artifact state in dictionary."""
        state = {"artifacts": {}}
        update_artifact_state(state, "test.csv", "hash123")

        assert "test.csv" in state["artifacts"]
        assert state["artifacts"]["test.csv"]["hash"] == "hash123"
        assert "timestamp" in state["artifacts"]["test.csv"]

    def test_compute_and_update_hash(self, temp_state_dir, temp_file):
        """Test computing hash and updating state file."""
        compute_and_update_hash(temp_file, temp_state_dir)

        state = load_state(temp_state_dir)
        assert temp_file in state["artifacts"]
        assert "hash" in state["artifacts"][temp_file]
        assert "timestamp" in state["artifacts"][temp_file]

    def test_verify_artifact_success(self, temp_state_dir, temp_file):
        """Test successful artifact verification."""
        # Compute and update hash
        compute_and_update_hash(temp_file, temp_state_dir)
        state = load_state(temp_state_dir)
        expected_hash = state["artifacts"][temp_file]["hash"]

        # Verify
        assert verify_artifact(temp_file, expected_hash, temp_state_dir) is True

    def test_verify_artifact_failure(self, temp_state_dir, temp_file):
        """Test failed artifact verification."""
        compute_and_update_hash(temp_file, temp_state_dir)
        state = load_state(temp_state_dir)
        expected_hash = state["artifacts"][temp_file]["hash"]

        # Corrupt the file
        with open(temp_file, 'w') as f:
            f.write("changed content")

        assert verify_artifact(temp_file, expected_hash, temp_state_dir) is False
