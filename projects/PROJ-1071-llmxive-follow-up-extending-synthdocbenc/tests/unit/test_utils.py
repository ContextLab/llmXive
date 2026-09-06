"""
Unit tests for code/utils.py utilities.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
import torch

from code.utils import (
    compute_directory_checksum,
    compute_file_checksum,
    load_state_json,
    pin_random_seed,
    update_state_json,
    validate_checksum,
)


class TestPinRandomSeed:
    def test_seed_python(self):
        """Test that Python random seed is pinned."""
        pin_random_seed(123)
        val1 = [random.random() for _ in range(3)]
        
        pin_random_seed(123)
        val2 = [random.random() for _ in range(3)]
        
        assert val1 == val2

    def test_seed_numpy(self):
        """Test that NumPy random seed is pinned."""
        pin_random_seed(456)
        val1 = np.random.rand(3)
        
        pin_random_seed(456)
        val2 = np.random.rand(3)
        
        np.testing.assert_array_equal(val1, val2)

    def test_seed_torch(self):
        """Test that PyTorch random seed is pinned."""
        pin_random_seed(789)
        val1 = torch.rand(3)
        
        pin_random_seed(789)
        val2 = torch.rand(3)
        
        torch.testing.assert_close(val1, val2)


class TestFileChecksum:
    def test_compute_sha256(self, tmp_path):
        """Test SHA256 checksum computation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        checksum = compute_file_checksum(test_file)
        assert len(checksum) == 64  # SHA256 hex length
        assert all(c in "0123456789abcdef" for c in checksum)

    def test_compute_md5(self, tmp_path):
        """Test MD5 checksum computation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        checksum = compute_file_checksum(test_file, algorithm="md5")
        assert len(checksum) == 32  # MD5 hex length

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            compute_file_checksum("/nonexistent/file.txt")

    def test_invalid_algorithm(self, tmp_path):
        """Test that ValueError is raised for invalid algorithm."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        with pytest.raises(ValueError):
            compute_file_checksum(test_file, algorithm="invalid_algo")


class TestDirectoryChecksum:
    def test_directory_checksum_deterministic(self, tmp_path):
        """Test that directory checksum is deterministic."""
        # Create files in non-alphabetical order
        (tmp_path / "z.txt").write_text("z")
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "m.txt").write_text("m")
        
        checksum1 = compute_directory_checksum(tmp_path)
        checksum2 = compute_directory_checksum(tmp_path)
        
        assert checksum1 == checksum2

    def test_directory_checksum_content_dependent(self, tmp_path):
        """Test that checksum changes with content."""
        (tmp_path / "test.txt").write_text("content1")
        checksum1 = compute_directory_checksum(tmp_path)
        
        (tmp_path / "test.txt").write_text("content2")
        checksum2 = compute_directory_checksum(tmp_path)
        
        assert checksum1 != checksum2

    def test_not_a_directory(self):
        """Test that NotADirectoryError is raised."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name
        
        try:
            with pytest.raises(NotADirectoryError):
                compute_directory_checksum(temp_path)
        finally:
            os.unlink(temp_path)


class TestUpdateStateJson:
    def test_create_new_file(self, tmp_path):
        """Test creating a new state file."""
        state_path = tmp_path / "state.json"
        updates = {"key": "value"}
        
        update_state_json(state_path, updates)
        
        assert state_path.exists()
        with open(state_path) as f:
            state = json.load(f)
        assert state == {"key": "value"}

    def test_update_existing_file(self, tmp_path):
        """Test updating an existing state file."""
        state_path = tmp_path / "state.json"
        
        # Initial state
        state_path.write_text('{"a": 1}')
        
        # Update
        update_state_json(state_path, {"b": 2})
        
        with open(state_path) as f:
            state = json.load(f)
        assert state == {"a": 1, "b": 2}

    def test_deep_merge(self, tmp_path):
        """Test deep merge of nested dictionaries."""
        state_path = tmp_path / "state.json"
        
        # Initial state
        state_path.write_text('{"outer": {"a": 1, "b": 2}}')
        
        # Update
        update_state_json(state_path, {"outer": {"b": 3, "c": 4}})
        
        with open(state_path) as f:
            state = json.load(f)
        assert state == {"outer": {"a": 1, "b": 3, "c": 4}}

    def test_backup_creation(self, tmp_path):
        """Test that backup is created when requested."""
        state_path = tmp_path / "state.json"
        state_path.write_text('{"a": 1}')
        
        update_state_json(state_path, {"b": 2}, backup=True)
        
        assert state_path.with_suffix(".json.bak").exists()

    def test_no_backup(self, tmp_path):
        """Test that no backup is created when disabled."""
        state_path = tmp_path / "state.json"
        state_path.write_text('{"a": 1}')
        
        update_state_json(state_path, {"b": 2}, backup=False)
        
        assert not state_path.with_suffix(".json.bak").exists()

    def test_invalid_json(self, tmp_path):
        """Test that JSONDecodeError is raised for invalid JSON."""
        state_path = tmp_path / "state.json"
        state_path.write_text("not valid json")
        
        with pytest.raises(json.JSONDecodeError):
            update_state_json(state_path, {"key": "value"})


class TestLoadStateJson:
    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON state file."""
        state_path = tmp_path / "state.json"
        state_path.write_text('{"key": "value", "number": 42}')
        
        state = load_state_json(state_path)
        assert state == {"key": "value", "number": 42}

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised."""
        with pytest.raises(FileNotFoundError):
            load_state_json(tmp_path / "nonexistent.json")


class TestValidateChecksum:
    def test_valid_checksum(self, tmp_path):
        """Test validation with correct checksum."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        checksum = compute_file_checksum(test_file)
        assert validate_checksum(test_file, checksum) is True

    def test_invalid_checksum(self, tmp_path):
        """Test validation with incorrect checksum."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        assert validate_checksum(test_file, "wrongchecksum") is False
