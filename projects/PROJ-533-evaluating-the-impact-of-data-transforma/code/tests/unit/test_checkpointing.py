"""
Unit tests for the checkpointing utilities.
Verifies that save_state, load_state, and delete_checkpoint work as expected.
"""

import json
import os
from pathlib import Path

import pytest

# Import the functions under test
from code.utils.checkpointing import (
    save_state,
    load_state,
    delete_checkpoint,
    get_checkpoint_path,
)


@pytest.fixture
def temporary_run_id(tmp_path: Path) -> str:
    """
    Provides a unique run_id that points to a temporary checkpoint directory.
    The checkpoint utilities use the global `results/checkpoints` directory,
    so we monkey‑patch the environment variable that the utilities rely on
    (via the `RESULTS_DIR` constant) by temporarily changing the working
    directory to a temporary location.
    """
    # Change cwd to the temporary directory so that the utilities resolve
    # `results/checkpoints` relative to it.
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        yield "test_run"
    finally:
        # Clean up: ensure any leftover checkpoint is removed
        checkpoint_path = get_checkpoint_path("test_run")
        if checkpoint_path.exists():
            checkpoint_path.unlink()
        os.chdir(original_cwd)


def test_save_and_load_checkpoint(temporary_run_id: str):
    """Save a simple state dict and verify that it can be loaded correctly."""
    state = {"step": "download", "progress": 0.5, "details": {"files": 3}}

    # Save the state
    save_state(temporary_run_id, state)

    # Verify that the checkpoint file now exists
    checkpoint_path = get_checkpoint_path(temporary_run_id)
    assert checkpoint_path.exists(), "Checkpoint file was not created"

    # Load the state back
    loaded_state = load_state(temporary_run_id)
    assert loaded_state == state, "Loaded state does not match saved state"


def test_delete_checkpoint(temporary_run_id: str):
    """Create a checkpoint, delete it, and ensure it is gone."""
    state = {"dummy": True}
    save_state(temporary_run_id, state)
    checkpoint_path = get_checkpoint_path(temporary_run_id)
    assert checkpoint_path.exists()

    # Delete the checkpoint
    delete_checkpoint(temporary_run_id)
    assert not checkpoint_path.exists(), "Checkpoint file was not deleted"


def test_load_nonexistent_checkpoint_returns_none(tmp_path: Path):
    """Loading a checkpoint that does not exist should return None."""
    # Ensure we are in a temporary cwd so the default checkpoint dir is empty
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        assert load_state("nonexistent_run") is None
    finally:
        os.chdir(original_cwd)