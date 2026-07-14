"""
Tests for checksum utilities.
"""
import json
import tempfile
from pathlib import Path
import pytest

from utils.checksums import (
    compute_sha256,
    compute_directory_checksums,
    load_state_file,
    update_state_file,
    verify_file_integrity,
    batch_update_state_files
)

def test_compute_sha256():
    """Test SHA-256 computation on a known file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        hash_result = compute_sha256(temp_path)
        assert len(hash_result) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in hash_result)
    finally:
        temp_path.unlink()

def test_compute_directory_checksums():
    """Test directory checksum computation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        
        checksums = compute_directory_checksums(tmp_path)
        
        assert len(checksums) == 2
        assert "file1.txt" in checksums
        assert "file2.txt" in checksums

def test_load_state_file_not_exists():
    """Test loading non-existent state file."""
    result = load_state_file(Path("/nonexistent/state.json"))
    assert result == {}

def test_update_state_file():
    """Test updating state file."""
    current = {"existing": {"checksums": {"a.txt": "hash1"}}}
    new_checksums = {"/new/dir": {"b.txt": "hash2"}}
    
    updated = update_state_file(current, new_checksums)
    
    assert "existing" in updated
    assert "/new/dir" in updated
    assert updated["/new/dir"]["checksums"]["b.txt"] == "hash2"

def test_update_and_save_state_file():
    """Test updating and saving state file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state.json"
        
        current = {"test": {"checksums": {"a.txt": "hash1"}}}
        new_checksums = {"/test/dir": {"b.txt": "hash2"}}
        
        updated = update_state_file(current, new_checksums, save=True, state_path=state_path)
        
        assert state_path.exists()
        
        with open(state_path) as f:
            saved = json.load(f)
        
        assert saved == updated

def test_verify_file_integrity():
    """Test file integrity verification."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        actual_hash = compute_sha256(temp_path)
        
        # Valid hash
        assert verify_file_integrity(temp_path, actual_hash)
        
        # Invalid hash
        assert not verify_file_integrity(temp_path, "wronghash")
        
        # Non-existent file
        assert not verify_file_integrity(Path("/nonexistent"), actual_hash)
    finally:
        temp_path.unlink()

def test_batch_update_state_files():
    """Test batch state file updates."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state1 = Path(tmpdir) / "state1.json"
        state2 = Path(tmpdir) / "state2.json"
        
        # Initialize state files
        state1.write_text("{}")
        state2.write_text("{}")
        
        new_checksums = {"/test": {"a.txt": "hash1"}}
        
        results = batch_update_state_files([state1, state2], new_checksums)
        
        assert results[str(state1)] is True
        assert results[str(state2)] is True
        assert state1.exists()
        assert state2.exists()