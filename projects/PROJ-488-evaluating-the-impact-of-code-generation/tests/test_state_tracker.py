"""Tests for state tracking utilities."""

import os
from pathlib import Path
import tempfile
import pytest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.state_tracker import (
    compute_file_hash,
    compute_directory_hash,
    load_state_file,
    save_state_file,
    update_state_with_artifact,
    update_state_timestamp,
    register_artifact_hash,
    get_artifact_state,
    verify_artifact_integrity
)


class TestStateTracker:
    """Test suite for state tracking utilities."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.state_path = Path(self.temp_dir) / "test_state.yaml"
        self.test_file = Path(self.temp_dir) / "test_file.txt"
        self.test_file.write_text("test content")

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_compute_file_hash(self):
        """Test file hash computation."""
        file_hash = compute_file_hash(self.test_file)
        assert file_hash is not None
        assert len(file_hash) == 64  # SHA-256 hex string length

    def test_load_state_file_nonexistent(self):
        """Test loading non-existent state file."""
        state = load_state_file(Path(self.temp_dir) / "nonexistent.yaml")
        assert "state" in state

    def test_save_and_load_state_file(self):
        """Test saving and loading state file."""
        test_state = {"state": {"test": "value"}}
        save_state_file(self.state_path, test_state)
        assert self.state_path.exists()
        loaded = load_state_file(self.state_path)
        assert loaded["state"]["test"] == "value"

    def test_update_state_with_artifact(self):
        """Test updating state with artifact."""
        state = update_state_with_artifact(
            self.state_path,
            self.test_file,
            "test_artifact",
            {"description": "test"}
        )
        assert "state" in state
        assert "artifacts" in state["state"]
        assert "test_artifact" in state["state"]["artifacts"]
        assert "updated_at" in state["state"]["artifacts"]["test_artifact"]

    def test_update_state_timestamp(self):
        """Test updating state timestamp."""
        state = update_state_timestamp(self.state_path, {"action": "test"})
        assert "state" in state
        assert "updated_at" in state["state"]

    def test_register_artifact_hash(self):
        """Test registering artifact hash."""
        state = register_artifact_hash(self.state_path, self.test_file)
        assert "artifacts" in state["state"]
        assert self.test_file.name in state["state"]["artifacts"]

    def test_get_artifact_state(self):
        """Test getting artifact state."""
        update_state_with_artifact(self.state_path, self.test_file, "my_artifact")
        artifact_state = get_artifact_state(self.state_path, "my_artifact")
        assert artifact_state is not None
        assert artifact_state["path"] == str(self.test_file)

    def test_verify_artifact_integrity(self):
        """Test verifying artifact integrity."""
        update_state_with_artifact(self.state_path, self.test_file, "verify_test")
        is_valid = verify_artifact_integrity(self.state_path, "verify_test")
        assert is_valid is True

        # Modify file and verify fails
        self.test_file.write_text("modified content")
        is_valid = verify_artifact_integrity(self.state_path, "verify_test")
        assert is_valid is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
