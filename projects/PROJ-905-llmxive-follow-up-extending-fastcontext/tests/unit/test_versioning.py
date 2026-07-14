"""
Unit tests for the versioning module.
"""
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from versioning import compute_sha256, scan_directory, update_state_file


def test_compute_sha256():
    """Test SHA-256 computation for a simple file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        hash_result = compute_sha256(temp_path)
        expected_hash = hashlib.sha256(b"test content").hexdigest()
        assert hash_result == expected_hash
    finally:
        os.unlink(temp_path)


def test_scan_directory_empty():
    """Test scanning an empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = scan_directory(Path(tmpdir))
        assert result == {}


def test_scan_directory_with_files():
    """Test scanning a directory with files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        # Create some files
        (tmppath / "file1.txt").write_text("content1")
        (tmppath / "file2.py").write_text("code")
        (tmppath / "subdir").mkdir()
        (tmppath / "subdir" / "file3.json").write_text("{}")
        
        # Create a file that should be ignored
        (tmppath / "ignore.bin").write_text("binary")
        
        result = scan_directory(tmppath)
        
        assert "file1.txt" in result
        assert "file2.py" in result
        assert "subdir/file3.json" in result
        assert "ignore.bin" not in result
        assert len(result) == 3


def test_update_state_file_creates_new():
    """Test that update_state_file creates a new state file if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        state_path = tmppath / "state.yaml"
        
        data_hashes = {"file.txt": "abc123"}
        code_hashes = {"code.py": "def456"}
        
        update_state_file(state_path, data_hashes, code_hashes)
        
        assert state_path.exists()
        
        with open(state_path, "r") as f:
            state = yaml.safe_load(f)
        
        assert "artifact_hashes" in state
        assert state["artifact_hashes"]["data"] == data_hashes
        assert state["artifact_hashes"]["code"] == code_hashes
        assert "updated_at" in state
        
        # Check timestamp format (ISO 8601)
        timestamp = state["updated_at"]
        # Should be parseable
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def test_update_state_file_updates_existing():
    """Test that update_state_file updates an existing state file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        state_path = tmppath / "state.yaml"
        
        # Create initial state
        initial_state = {
            "existing_key": "existing_value",
            "artifact_hashes": {"old": "hash"}
        }
        with open(state_path, "w") as f:
            yaml.dump(initial_state, f)
        
        data_hashes = {"new.txt": "xyz789"}
        code_hashes = {"new.py": "uvw012"}
        
        update_state_file(state_path, data_hashes, code_hashes)
        
        with open(state_path, "r") as f:
            state = yaml.safe_load(f)
        
        # Should preserve existing keys
        assert state["existing_key"] == "existing_value"
        
        # Should update artifact_hashes
        assert state["artifact_hashes"]["data"] == data_hashes
        assert state["artifact_hashes"]["code"] == code_hashes
        
        # Should update timestamp
        assert "updated_at" in state
        
        # Verify timestamp is newer than initial (by checking format)
        datetime.fromisoformat(state["updated_at"].replace("Z", "+00:00"))