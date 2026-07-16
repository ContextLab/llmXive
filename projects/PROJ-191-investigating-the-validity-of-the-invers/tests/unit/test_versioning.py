"""
Unit tests for the versioning utility.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

from code.utils.versioning import (
    VersionedState,
    create_state_manager,
    atomic_save_json,
    atomic_update_json,
)


@pytest.fixture
def temp_state_file():
    """Create a temporary state file for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "test_state.json"
        yield str(state_path)


class TestVersionedState:
    """Tests for the VersionedState class."""

    def test_initial_load_nonexistent_file(self, temp_state_file):
        """Loading a non-existent file returns empty dict."""
        manager = VersionedState(temp_state_file)
        state = manager.load()
        assert state == {}

    def test_save_and_load(self, temp_state_file):
        """Save and load preserves data."""
        manager = VersionedState(temp_state_file)
        test_data = {"key": "value", "number": 42}
        manager.save(test_data)

        loaded = manager.load()
        assert loaded["key"] == "value"
        assert loaded["number"] == 42
        assert "metadata" in loaded

    def test_version_increment(self, temp_state_file):
        """Each save increments the version number."""
        manager = VersionedState(temp_state_file)

        # Initial save
        manager.save({"data": 1})
        assert manager.get_version() == 1

        # Second save
        manager.save({"data": 2})
        assert manager.get_version() == 2

    def test_atomic_update(self, temp_state_file):
        """Update merges new values with existing state."""
        manager = VersionedState(temp_state_file)
        manager.save({"a": 1, "b": 2})

        updated = manager.update({"b": 20, "c": 3})
        assert updated["a"] == 1
        assert updated["b"] == 20
        assert updated["c"] == 3

    def test_checksum_integrity(self, temp_state_file):
        """Verify checksum matches after save."""
        manager = VersionedState(temp_state_file)
        manager.save({"test": "data"})

        assert manager.verify_integrity() is True

    def test_corrupted_checksum_detection(self, temp_state_file):
        """Detect when checksum doesn't match."""
        manager = VersionedState(temp_state_file)
        manager.save({"test": "data"})

        # Manually corrupt the file
        with open(temp_state_file, 'r') as f:
            content = f.read()

        # Modify content slightly
        corrupted = content.replace("data", "dAtA")
        with open(temp_state_file, 'w') as f:
            f.write(corrupted)

        assert manager.verify_integrity() is False

    def test_parent_directory_creation(self, temp_state_file):
        """Create parent directories if they don't exist."""
        deep_path = Path(temp_state_file).parent / "nested" / "path" / "state.json"
        manager = VersionedState(str(deep_path))
        manager.save({"test": "value"})

        assert deep_path.exists()


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_state_manager(self, temp_state_file):
        """create_state_manager returns a VersionedState instance."""
        manager = create_state_manager(temp_state_file)
        assert isinstance(manager, VersionedState)

    def test_atomic_save_json(self, temp_state_file):
        """atomic_save_json saves data correctly."""
        test_data = {"key": "value"}
        atomic_save_json(temp_state_file, test_data)

        with open(temp_state_file, 'r') as f:
            loaded = json.load(f)

        assert loaded["key"] == "value"

    def test_atomic_update_json(self, temp_state_file):
        """atomic_update_json updates data correctly."""
        atomic_save_json(temp_state_file, {"a": 1})
        result = atomic_update_json(temp_state_file, {"b": 2})

        assert result["a"] == 1
        assert result["b"] == 2
