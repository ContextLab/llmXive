"""
Unit tests for checkpointing utilities.
"""

import os
import json
import tempfile
from pathlib import Path
import pytest

# Adjust import path for testing context
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.checkpointing import (
    save_checkpoint,
    load_checkpoint,
    has_checkpoint,
    delete_checkpoint,
    list_checkpoints,
    ensure_checkpoint_dir,
    compute_file_hash,
    save_state_snapshot,
    get_resume_info
)


@pytest.fixture
def temp_checkpoint_dir(tmp_path):
    """Create a temporary directory to simulate checkpoint storage."""
    # Override the global CHECKPOINT_DIR for testing
    import code.utils.checkpointing as cp_module
    original_dir = cp_module.CHECKPOINT_DIR
    cp_module.CHECKPOINT_DIR = tmp_path
    yield tmp_path
    cp_module.CHECKPOINT_DIR = original_dir


def test_save_and_load_checkpoint(temp_checkpoint_dir):
    """Test saving and loading a basic checkpoint."""
    run_id = "test_run_001"
    state = {"progress": 50, "items": [1, 2, 3]}
    metadata = {"config": "v1"}

    path = save_checkpoint(run_id, state, metadata=metadata)

    assert path.exists()
    assert has_checkpoint(run_id)

    loaded_state = load_checkpoint(run_id)
    assert loaded_state == state

    # Verify metadata is saved in the file structure
    with open(path, "r") as f:
        data = json.load(f)
    assert data["metadata"] == metadata
    assert data["run_id"] == run_id


def test_load_nonexistent_checkpoint(temp_checkpoint_dir):
    """Test loading a checkpoint that doesn't exist returns None."""
    assert load_checkpoint("fake_run") is None
    assert not has_checkpoint("fake_run")


def test_delete_checkpoint(temp_checkpoint_dir):
    """Test deleting a checkpoint."""
    run_id = "run_to_delete"
    save_checkpoint(run_id, {"key": "value"})

    assert has_checkpoint(run_id)
    assert delete_checkpoint(run_id)
    assert not has_checkpoint(run_id)

    # Deleting again should return False
    assert not delete_checkpoint(run_id)


def test_list_checkpoints(temp_checkpoint_dir):
    """Test listing available checkpoints."""
    save_checkpoint("run_a", {})
    save_checkpoint("run_b", {})
    # Create a non-json file to ensure it's ignored
    (temp_checkpoint_dir / "ignore_me.txt").touch()

    checkpoints = list_checkpoints()
    assert "run_a" in checkpoints
    assert "run_b" in checkpoints
    assert "ignore_me" not in checkpoints


def test_compute_file_hash(temp_checkpoint_dir):
    """Test SHA-256 hash computation."""
    test_file = temp_checkpoint_dir / "test.txt"
    test_file.write_text("Hello, World!")

    hash1 = compute_file_hash(test_file)
    hash2 = compute_file_hash(test_file)

    assert len(hash1) == 64  # SHA-256 hex length
    assert hash1 == hash2

    # Different content should yield different hash
    test_file.write_text("Different content")
    hash3 = compute_file_hash(test_file)
    assert hash1 != hash3


def test_save_state_snapshot(temp_checkpoint_dir):
    """Test the convenience snapshot function."""
    run_id = "snapshot_run"
    path = save_state_snapshot(
        run_id,
        current_step="filtering",
        processed_items=["dataset_1", "dataset_2"],
        errors=[{"msg": "Missing value"}],
        extra_state={"config_hash": "abc123"}
    )

    resume = get_resume_info(run_id)
    assert resume is not None
    assert resume["current_step"] == "filtering"
    assert resume["processed_items"] == ["dataset_1", "dataset_2"]
    assert len(resume["errors"]) == 1


def test_overwrite_checkpoint_false(temp_checkpoint_dir):
    """Test that saving without overwrite raises error if exists."""
    run_id = "overwrite_test"
    save_checkpoint(run_id, {"v": 1})

    with pytest.raises(FileExistsError):
        save_checkpoint(run_id, {"v": 2})

    # Verify overwrite works
    save_checkpoint(run_id, {"v": 2}, overwrite=True)
    assert load_checkpoint(run_id) == {"v": 2}
