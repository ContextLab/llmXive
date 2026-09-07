"""Unit tests for training checkpoint functionality."""
import json
import os
import tempfile
import numpy as np
import pytest

from modeling.train import load_checkpoint, save_checkpoint


class TestCheckpoint:
    """Test checkpoint save/load functionality."""

    def test_save_and_load_checkpoint(self, tmp_path):
        """Test that checkpoint can be saved and loaded."""
        checkpoint_path = tmp_path / "test_checkpoint.json"

        state = {
            "last_completed_fold": 2,
            "timestamp": 1234567890.0,
            "n_subjects": 100,
            "n_splits": 5
        }

        save_checkpoint(str(checkpoint_path), state)

        assert checkpoint_path.exists()

        loaded = load_checkpoint(str(checkpoint_path))

        assert loaded is not None
        assert loaded["last_completed_fold"] == 2
        assert loaded["n_subjects"] == 100
        assert loaded["n_splits"] == 5

    def test_load_nonexistent_checkpoint(self):
        """Test loading a checkpoint that doesn't exist returns None."""
        result = load_checkpoint("/nonexistent/path/checkpoint.json")
        assert result is None

    def test_checkpoint_with_missing_fields(self, tmp_path):
        """Test checkpoint with partial data."""
        checkpoint_path = tmp_path / "partial_checkpoint.json"

        state = {
            "last_completed_fold": 1
        }

        save_checkpoint(str(checkpoint_path), state)
        loaded = load_checkpoint(str(checkpoint_path))

        assert loaded["last_completed_fold"] == 1
        # Missing fields should not cause error, just be absent
        assert "timestamp" not in loaded