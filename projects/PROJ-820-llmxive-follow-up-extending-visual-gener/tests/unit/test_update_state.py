"""
Unit tests for update_state module.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.update_state import calculate_sha256, scan_directory, update_state_file

class TestCalculateSha256:
    def test_hash_consistency(self, tmp_path):
        """Test that same file produces same hash."""
        file_path = tmp_path / "test.txt"
        content = b"Hello, World!"
        file_path.write_bytes(content)
        
        hash1 = calculate_sha256(file_path)
        hash2 = calculate_sha256(file_path)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_hash_changes_with_content(self, tmp_path):
        """Test that different content produces different hash."""
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"
        
        file1.write_bytes(b"Content A")
        file2.write_bytes(b"Content B")
        
        hash1 = calculate_sha256(file1)
        hash2 = calculate_sha256(file2)
        
        assert hash1 != hash2

class TestScanDirectory:
    def test_scan_empty_directory(self, tmp_path):
        """Test scanning an empty directory."""
        hashes = scan_directory(tmp_path)
        assert hashes == {}

    def test_scan_with_files(self, tmp_path):
        """Test scanning a directory with files."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.json"
        
        file1.write_text("content1")
        file2.write_text("content2")
        
        hashes = scan_directory(tmp_path)
        
        assert "file1.txt" in hashes
        assert "file2.json" in hashes
        assert len(hashes) == 2

    def test_scan_with_extension_filter(self, tmp_path):
        """Test scanning with extension filter."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.json"
        
        file1.write_text("content1")
        file2.write_text("content2")
        
        hashes = scan_directory(tmp_path, extensions=[".txt"])
        
        assert "file1.txt" in hashes
        assert "file2.json" not in hashes
        assert len(hashes) == 1

    def test_scan_nonexistent_directory(self):
        """Test scanning a non-existent directory."""
        fake_path = Path("/nonexistent/path/that/does/not/exist")
        hashes = scan_directory(fake_path)
        assert hashes == {}

    def test_scan_nested_directories(self, tmp_path):
        """Test scanning nested directories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        file1 = tmp_path / "root.txt"
        file2 = subdir / "nested.txt"
        
        file1.write_text("root content")
        file2.write_text("nested content")
        
        hashes = scan_directory(tmp_path)
        
        assert "root.txt" in hashes
        assert "subdir/nested.txt" in hashes
        assert len(hashes) == 2

class TestUpdateStateFile:
    def test_create_new_state_file(self, tmp_path):
        """Test creating a new state file."""
        state_path = tmp_path / "state.json"
        hashes = {"test_dir": {"file.txt": "abc123"}}
        
        update_state_file(state_path, hashes)
        
        assert state_path.exists()
        
        with open(state_path, 'r') as f:
            state = json.load(f)
        
        assert "artifacts" in state
        assert "test_dir" in state["artifacts"]
        assert "file.txt" in state["artifacts"]["test_dir"]
        assert "last_updated" in state

    def test_update_existing_state_file(self, tmp_path):
        """Test updating an existing state file."""
        state_path = tmp_path / "state.json"
        
        # Create initial state
        initial_state = {"artifacts": {"old_dir": {"old.txt": "old_hash"}}}
        with open(state_path, 'w') as f:
            json.dump(initial_state, f)
        
        # Update with new hashes
        new_hashes = {"new_dir": {"new.txt": "new_hash"}}
        update_state_file(state_path, new_hashes)
        
        with open(state_path, 'r') as f:
            state = json.load(f)
        
        # Should have both old and new
        assert "old_dir" in state["artifacts"]
        assert "new_dir" in state["artifacts"]
        assert "last_updated" in state

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        state_path = tmp_path / "deep" / "nested" / "state.json"
        hashes = {"test": {"file.txt": "hash"}}
        
        update_state_file(state_path, hashes)
        
        assert state_path.exists()