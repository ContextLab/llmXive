"""
Tests for scripts/update_state_hashes.py functionality.
"""
import os
import sys
import tempfile
import yaml
from pathlib import Path
import hashlib

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.update_state_hashes import (
    get_sha256,
    get_git_hash,
    ensure_directory,
    STATE_FILE,
    PROJECT_ID
)

def test_get_sha256_existing_file():
    """Test SHA256 calculation on an existing file."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = b"test content for hashing"
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    try:
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = get_sha256(tmp_path)
        assert actual_hash == expected_hash, f"Hash mismatch: {actual_hash} != {expected_hash}"
    finally:
        tmp_path.unlink()

def test_get_sha256_missing_file():
    """Test SHA256 calculation on a missing file returns None."""
    missing_path = Path("/nonexistent/file.txt")
    result = get_sha256(missing_path)
    assert result is None, "Should return None for missing file"

def test_get_git_hash():
    """Test that git hash is a string (or 'no-git' if not in a repo)."""
    git_hash = get_git_hash()
    assert isinstance(git_hash, str), "Git hash should be a string"
    assert len(git_hash) > 0, "Git hash should not be empty"

def test_ensure_directory():
    """Test that ensure_directory creates the directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        new_dir = Path(tmpdir) / "subdir" / "nested"
        assert not new_dir.exists()
        ensure_directory(new_dir)
        assert new_dir.exists(), "Directory should be created"
        assert new_dir.is_dir(), "Path should be a directory"

def test_state_file_structure():
    """Verify the state file structure if it exists."""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            state = yaml.safe_load(f)
        
        assert "project_id" in state, "Missing project_id"
        assert state["project_id"] == PROJECT_ID, "Project ID mismatch"
        assert "git_hash" in state, "Missing git_hash"
        assert "data_source" in state, "Missing data_source"
        assert "checksums" in state, "Missing checksums"
        assert "raw" in state["checksums"], "Missing raw checksums"
        assert "processed" in state["checksums"], "Missing processed checksums"
    else:
        # If file doesn't exist, the test is skipped but valid
        print("State file not found, skipping structure test (expected if script not run yet)")

if __name__ == "__main__":
    # Run tests manually if executed as script
    test_get_sha256_existing_file()
    test_get_sha256_missing_file()
    test_get_git_hash()
    test_ensure_directory()
    test_state_file_structure()
    print("All tests passed.")