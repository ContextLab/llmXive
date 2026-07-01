"""
Unit tests for checkpointing functionality.
"""

import json
import os
import shutil
from pathlib import Path
import tempfile
import pytest

# We need to mock the CHECKPOINT_DIR for testing
# We'll use a temporary directory during tests
import code.utils.checkpointing as checkpointing_module


@pytest.fixture
def temp_checkpoint_dir():
    """Create a temporary directory for checkpoint tests."""
    temp_dir = tempfile.mkdtemp()
    original_dir = checkpointing_module.CHECKPOINT_DIR
    checkpointing_module.CHECKPOINT_DIR = temp_dir
    yield temp_dir
    # Cleanup
    checkpointing_module.CHECKPOINT_DIR = original_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestCheckpointing:
    def test_save_and_load_checkpoint(self, temp_checkpoint_dir):
        """Test saving and loading a checkpoint."""
        run_id = "test_run_123"
        state = {"processed_datasets": 5, "current_step": "filtering"}
        metadata = {"version": "1.0", "timestamp": "2024-01-01"}

        # Save
        path = checkpointing_module.save_checkpoint(run_id, state, metadata)
        assert path.exists()

        # Load
        loaded = checkpointing_module.load_checkpoint(run_id)
        assert loaded is not None
        assert loaded["run_id"] == run_id
        assert loaded["state"] == state
        assert loaded["metadata"] == metadata

    def test_load_nonexistent_checkpoint(self, temp_checkpoint_dir):
        """Test loading a checkpoint that doesn't exist returns None."""
        result = checkpointing_module.load_checkpoint("nonexistent_run")
        assert result is None

    def test_delete_checkpoint(self, temp_checkpoint_dir):
        """Test deleting a checkpoint."""
        run_id = "to_delete"
        checkpointing_module.save_checkpoint(run_id, {"data": "test"})

        # Verify exists
        assert checkpointing_module.load_checkpoint(run_id) is not None

        # Delete
        deleted = checkpointing_module.delete_checkpoint(run_id)
        assert deleted is True

        # Verify gone
        assert checkpointing_module.load_checkpoint(run_id) is None

    def test_delete_nonexistent_checkpoint(self, temp_checkpoint_dir):
        """Test deleting a non-existent checkpoint returns False."""
        result = checkpointing_module.delete_checkpoint("nonexistent")
        assert result is False

    def test_compute_state_hash_determinism(self, temp_checkpoint_dir):
        """Test that state hash is deterministic."""
        state1 = {"a": 1, "b": [2, 3]}
        state2 = {"b": [2, 3], "a": 1}  # Same content, different order

        hash1 = checkpointing_module.compute_state_hash(state1)
        hash2 = checkpointing_module.compute_state_hash(state2)

        assert hash1 == hash2

    def test_compute_state_hash_uniqueness(self, temp_checkpoint_dir):
        """Test that different states produce different hashes."""
        state1 = {"a": 1}
        state2 = {"a": 2}

        hash1 = checkpointing_module.compute_state_hash(state1)
        hash2 = checkpointing_module.compute_state_hash(state2)

        assert hash1 != hash2

    def test_get_all_checkpoint_ids(self, temp_checkpoint_dir):
        """Test retrieving all checkpoint IDs."""
        checkpointing_module.save_checkpoint("run_a", {})
        checkpointing_module.save_checkpoint("run_b", {})
        checkpointing_module.save_checkpoint("run_c", {})

        ids = checkpointing_module.get_all_checkpoint_ids()
        assert set(ids) == {"run_a", "run_b", "run_c"}

    def test_update_checkpoint(self, temp_checkpoint_dir):
        """Test updating an existing checkpoint."""
        run_id = "update_test"
        initial_state = {"step": 1}
        checkpointing_module.save_checkpoint(run_id, initial_state)

        # Update
        new_state = {"step": 2, "extra": "data"}
        path = checkpointing_module.update_checkpoint(run_id, new_state)

        assert path is not None
        loaded = checkpointing_module.load_checkpoint(run_id)
        assert loaded["state"]["step"] == 2
        assert loaded["state"]["extra"] == "data"

    def test_update_nonexistent_checkpoint(self, temp_checkpoint_dir):
        """Test updating a non-existent checkpoint returns None."""
        result = checkpointing_module.update_checkpoint("nonexistent", {"data": "test"})
        assert result is None

    def test_checkpoint_with_special_characters_in_run_id(self, temp_checkpoint_dir):
        """Test that run IDs with slashes are handled safely."""
        run_id = "dataset/with/slashes"
        state = {"test": True}

        path = checkpointing_module.save_checkpoint(run_id, state)
        # The path should exist and be valid
        assert path.exists()

        # Should be loadable with the same ID
        loaded = checkpointing_module.load_checkpoint(run_id)
        assert loaded is not None
        assert loaded["state"] == state