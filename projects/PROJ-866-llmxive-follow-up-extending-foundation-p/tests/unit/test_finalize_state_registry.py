import os
import tempfile
import hashlib
import yaml
from pathlib import Path
import pytest

# Import the module under test
# Adjust import path based on project structure
sys_path_backup = __import__('sys').path.copy()
try:
    __import__('sys').path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))
    from utils.finalize_state_registry import compute_sha256, collect_all_artifact_hashes, update_state_registry
finally:
    __import__('sys').path = sys_path_backup

def test_compute_sha256():
    """Test SHA-256 computation for a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)

    try:
        hash_result = compute_sha256(temp_path)
        # Expected hash for "test content"
        expected = hashlib.sha256(b"test content").hexdigest()
        assert hash_result == expected
    finally:
        temp_path.unlink()

def test_collect_all_artifact_hashes():
    """Test collection of hashes from a directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create test files
        file1 = tmp_path / "subdir" / "file1.txt"
        file1.parent.mkdir(parents=True, exist_ok=True)
        file1.write_text("content1")
        
        file2 = tmp_path / "file2.txt"
        file2.write_text("content2")

        artifacts = collect_all_artifact_hashes(tmp_path)
        
        assert len(artifacts) == 2
        assert "subdir/file1.txt" in artifacts
        assert "file2.txt" in artifacts
        
        # Verify hashes are correct
        expected_hash1 = hashlib.sha256(b"content1").hexdigest()
        expected_hash2 = hashlib.sha256(b"content2").hexdigest()
        
        assert artifacts["subdir/file1.txt"] == expected_hash1
        assert artifacts["file2.txt"] == expected_hash2

def test_update_state_registry_creates_new():
    """Test that update_state_registry creates a new file if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "state.yaml"
        artifacts = {"test.txt": "abc123"}
        
        update_state_registry(state_file, artifacts)
        
        assert state_file.exists()
        with open(state_file, "r") as f:
            data = yaml.safe_load(f)
        
        assert "artifact_hashes" in data
        assert data["artifact_hashes"] == artifacts
        assert "updated_at" in data

def test_update_state_registry_updates_existing():
    """Test that update_state_registry updates an existing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "state.yaml"
        
        # Create initial state
        initial_data = {
            "existing_key": "existing_value",
            "artifact_hashes": {"old.txt": "old_hash"}
        }
        with open(state_file, "w") as f:
            yaml.dump(initial_data, f)
        
        # Update with new artifacts
        new_artifacts = {"new.txt": "new_hash"}
        update_state_registry(state_file, new_artifacts)
        
        with open(state_file, "r") as f:
            data = yaml.safe_load(f)
        
        # Verify existing data is preserved
        assert data["existing_key"] == "existing_value"
        # Verify new artifacts replace old ones
        assert data["artifact_hashes"] == new_artifacts
        assert "updated_at" in data
        # Verify timestamp is updated (should be different from initial creation)
        assert data["updated_at"] != initial_data.get("updated_at", "")