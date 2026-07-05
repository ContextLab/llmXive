"""
Unit tests for code/utils/io.py
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from code.utils.io import (
    compute_sha256,
    write_json,
    read_json,
    ensure_directory,
    update_state,
    verify_checksum,
    safe_copy
)


class TestSha256:
    def test_compute_sha256_known_value(self, tmp_path):
        """Test SHA256 against a known string."""
        content = b"hello world"
        file_path = tmp_path / "test.txt"
        file_path.write_bytes(content)
        
        checksum = compute_sha256(file_path)
        # SHA256 of "hello world"
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert checksum == expected

    def test_compute_sha256_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            compute_sha256("/nonexistent/path/file.txt")


class TestJsonIO:
    def test_write_and_read_json(self, tmp_path):
        """Test round-trip JSON write and read."""
        data = {"key": "value", "number": 42}
        file_path = tmp_path / "data.json"
        
        write_json(data, file_path)
        assert file_path.exists()
        
        read_data = read_json(file_path)
        assert read_data == data

    def test_read_json_not_found(self):
        """Test error handling for missing JSON file."""
        with pytest.raises(FileNotFoundError):
            read_json("/nonexistent/file.json")


class TestEnsureDirectory:
    def test_create_new_directory(self, tmp_path):
        """Test creation of a new directory."""
        new_dir = tmp_path / "sub" / "nested"
        result = ensure_directory(new_dir)
        assert result.exists()
        assert result.is_dir()

    def test_existing_directory(self, tmp_path):
        """Test handling of existing directory."""
        result = ensure_directory(tmp_path)
        assert result.exists()


class TestUpdateState:
    def test_create_new_state_file(self, tmp_path):
        """Test creating a new state file."""
        state_file = tmp_path / "state.json"
        update_state(state_file, "run_id", 123)
        
        state = read_json(state_file)
        assert state["run_id"] == 123

    def test_update_existing_state(self, tmp_path):
        """Test updating an existing state file."""
        state_file = tmp_path / "state.json"
        write_json({"run_id": 1}, state_file)
        
        update_state(state_file, "step", 2)
        
        state = read_json(state_file)
        assert state["run_id"] == 1
        assert state["step"] == 2

    def test_update_state_with_checksum(self, tmp_path):
        """Test state update with automatic checksum calculation."""
        state_file = tmp_path / "state.json"
        data_file = tmp_path / "data.txt"
        data_file.write_text("test content")
        
        update_state(state_file, "data_path", str(data_file), checksum_file=True)
        
        state = read_json(state_file)
        assert "data_path" in state
        assert "data_path_checksum" in state
        assert verify_checksum(data_file, state["data_path_checksum"])


class TestVerifyChecksum:
    def test_verify_success(self, tmp_path):
        """Test successful checksum verification."""
        content = b"verify me"
        file_path = tmp_path / "verify.txt"
        file_path.write_bytes(content)
        
        checksum = compute_sha256(file_path)
        assert verify_checksum(file_path, checksum)

    def test_verify_failure(self, tmp_path):
        """Test failed checksum verification."""
        file_path = tmp_path / "verify.txt"
        file_path.write_bytes(b"wrong content")
        
        assert not verify_checksum(file_path, "wrong_checksum")


class TestSafeCopy:
    def test_copy_file(self, tmp_path):
        """Test copying a file."""
        src = tmp_path / "src.txt"
        dst = tmp_path / "dst" / "dst.txt"
        src.write_text("content")
        
        result = safe_copy(src, dst)
        assert result.exists()
        assert result.read_text() == "content"

    def test_copy_file_not_found(self, tmp_path):
        """Test error handling for missing source."""
        src = tmp_path / "missing.txt"
        dst = tmp_path / "dst.txt"
        
        with pytest.raises(FileNotFoundError):
            safe_copy(src, dst)