"""
tests/unit/test_generate_user_track_pairs.py

Unit tests for T029: generate_user_track_pairs.py
"""
import os
import tempfile
import pytest
import pandas as pd
from pathlib import Path
import yaml

# Mock the config and utils to avoid dependency on full project structure in tests
# We will test the logic functions directly if possible, or mock the dependencies.

# Since the script imports from `config` and `utils`, we need to ensure they are available
# or mock them. For simplicity, we assume the project is set up and these modules exist.
# We will test the core logic: checksum calculation and state update.

from generate_user_track_pairs import calculate_file_checksum, save_state_entry


class TestCalculateFileChecksum:
    def test_calculate_checksum(self, tmp_path):
        """Test that checksum is calculated correctly."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        checksum = calculate_file_checksum(test_file)
        assert len(checksum) == 64  # SHA256 hex length
        assert isinstance(checksum, str)

    def test_calculate_checksum_empty_file(self, tmp_path):
        """Test checksum for empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")

        checksum = calculate_file_checksum(test_file)
        assert checksum == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class TestSaveStateEntry:
    def test_save_state_entry_new(self, tmp_path):
        """Test saving a new entry to state.yaml."""
        state_file = tmp_path / "state.yaml"
        # Create a dummy file to checksum
        data_file = tmp_path / "data" / "test.parquet"
        data_file.parent.mkdir()
        data_file.write_bytes(b"test data")

        checksum = calculate_file_checksum(data_file)

        # Mock get_project_root to return tmp_path
        import generate_user_track_pairs as module
        original_get_project_root = module.get_project_root
        module.get_project_root = lambda: tmp_path

        try:
            save_state_entry(data_file, checksum)

            assert state_file.exists()
            with open(state_file, "r") as f:
                state = yaml.safe_load(f)

            relative_path = str(data_file.relative_to(tmp_path))
            assert relative_path in state
            assert state[relative_path]["checksum"] == checksum
            assert "size_bytes" in state[relative_path]
        finally:
            module.get_project_root = original_get_project_root

    def test_save_state_entry_update(self, tmp_path):
        """Test updating an existing entry in state.yaml."""
        state_file = tmp_path / "state.yaml"
        # Initial state
        initial_state = {"existing.txt": {"checksum": "old_checksum"}}
        with open(state_file, "w") as f:
            yaml.dump(initial_state, f)

        data_file = tmp_path / "new.parquet"
        data_file.write_bytes(b"new data")
        checksum = calculate_file_checksum(data_file)

        import generate_user_track_pairs as module
        original_get_project_root = module.get_project_root
        module.get_project_root = lambda: tmp_path

        try:
            save_state_entry(data_file, checksum)

            with open(state_file, "r") as f:
                state = yaml.safe_load(f)

            assert "existing.txt" in state
            assert "new.parquet" in state
            assert state["new.parquet"]["checksum"] == checksum
        finally:
            module.get_project_root = original_get_project_root