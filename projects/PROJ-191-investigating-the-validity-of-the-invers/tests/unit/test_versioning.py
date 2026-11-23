"""
Unit tests for the versioning utility.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from utils.versioning import VersionedState, atomic_save_json, atomic_update_json


class TestVersionedState:
    def test_init_creates_file(self, tmp_path):
        state_path = tmp_path / "state.json"
        manager = VersionedState(state_path)
        
        assert state_path.exists()
        assert manager.version == 0
        assert manager.state == {}

    def test_update_increments_version(self, tmp_path):
        state_path = tmp_path / "state.json"
        manager = VersionedState(state_path)
        
        manager.update({"key": "value"})
        
        assert manager.version == 1
        assert manager.get("key") == "value"
        assert manager.state["key"] == "value"

    def test_set_state_replaces_all(self, tmp_path):
        state_path = tmp_path / "state.json"
        manager = VersionedState(state_path)
        
        manager.update({"keep": "me"})
        manager.set_state({"replace": "all"})
        
        assert manager.version == 2
        assert manager.get("keep") is None
        assert manager.get("replace") == "all"

    def test_checksum_changes_on_update(self, tmp_path):
        state_path = tmp_path / "state.json"
        manager = VersionedState(state_path)
        
        checksum1 = manager._data["checksum"]
        manager.update({"new": "data"})
        checksum2 = manager._data["checksum"]
        
        assert checksum1 != checksum2

    def test_load_existing_state(self, tmp_path):
        state_path = tmp_path / "state.json"
        initial_data = {
            "version": 5,
            "last_updated": "2023-01-01T00:00:00",
            "checksum": "abc123",
            "state": {"existing": "value"}
        }
        
        with open(state_path, 'w') as f:
            json.dump(initial_data, f)
        
        manager = VersionedState(state_path)
        
        assert manager.version == 5
        assert manager.get("existing") == "value"

    def test_atomic_save_preserves_integrity(self, tmp_path):
        state_path = tmp_path / "test.json"
        data = {"test": "data", "number": 123}
        
        atomic_save_json(state_path, data)
        
        assert state_path.exists()
        with open(state_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == data

    def test_atomic_save_creates_parents(self, tmp_path):
        state_path = tmp_path / "deep" / "nested" / "state.json"
        data = {"nested": True}
        
        atomic_save_json(state_path, data)
        
        assert state_path.exists()

class TestAtomicUpdateJson:
    def test_update_function(self, tmp_path):
        state_path = tmp_path / "state.json"
        
        def increment_counter(current):
            current["counter"] = current.get("counter", 0) + 1
            return current
        
        atomic_update_json(state_path, increment_counter)
        atomic_update_json(state_path, increment_counter)
        
        with open(state_path, 'r') as f:
            data = json.load(f)
        
        assert data["counter"] == 2

    def test_create_if_not_exists(self, tmp_path):
        state_path = tmp_path / "new_state.json"
        
        def init_state(current):
            if not current:
                return {"initialized": True}
            return current
        
        atomic_update_json(state_path, init_state)
        
        assert state_path.exists()
        with open(state_path, 'r') as f:
            data = json.load(f)
        
        assert data["initialized"] is True