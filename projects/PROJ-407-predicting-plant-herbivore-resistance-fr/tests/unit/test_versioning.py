"""
Unit tests for versioning module.
"""
import hashlib
import os
import tempfile
from pathlib import Path
import pytest
import yaml

from versioning import compute_file_sha256, hash_directory, update_state_file


def test_compute_file_sha256():
    """Test SHA256 computation for a file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        hash_result = compute_file_sha256(temp_path)
        expected = hashlib.sha256(b"test content").hexdigest()
        assert hash_result == expected
    finally:
        os.unlink(temp_path)


def test_hash_directory():
    """Test directory hashing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file2.txt").write_text("content2")
        
        hashes = hash_directory(tmp_path, tmp_path)
        
        assert len(hashes) == 2
        assert "file1.txt" in hashes
        assert "subdir/file2.txt" in hashes


def test_update_state_file_creates_new():
    """Test that update_state_file creates a new state file if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Temporarily change the state directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            project_id = "test-project"
            data_hashes = {"test.txt": "abc123"}
            code_hashes = {"main.py": "def456"}
            
            update_state_file(project_id, data_hashes, code_hashes)
            
            state_file = Path("state/projects") / f"{project_id}.yaml"
            assert state_file.exists()
            
            with open(state_file, "r") as f:
                state_data = yaml.safe_load(f)
            
            assert state_data["project_id"] == project_id
            assert state_data["artifact_hashes"]["data"] == data_hashes
            assert state_data["artifact_hashes"]["code"] == code_hashes
            assert state_data["updated_at"] is not None
        finally:
            os.chdir(original_cwd)


def test_update_state_file_updates_existing():
    """Test that update_state_file updates an existing state file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            project_id = "test-project"
            
            # Create initial state file
            state_dir = Path("state/projects")
            state_dir.mkdir(parents=True)
            state_file = state_dir / f"{project_id}.yaml"
            
            initial_data = {
                "project_id": project_id,
                "artifact_hashes": {"old": "hash"},
                "updated_at": "2023-01-01T00:00:00+00:00"
            }
            
            with open(state_file, "w") as f:
                yaml.dump(initial_data, f)
            
            # Update with new hashes
            new_data_hashes = {"new.txt": "xyz789"}
            new_code_hashes = {"script.py": "123abc"}
            
            update_state_file(project_id, new_data_hashes, new_code_hashes)
            
            with open(state_file, "r") as f:
                state_data = yaml.safe_load(f)
            
            # Verify update
            assert state_data["artifact_hashes"]["data"] == new_data_hashes
            assert state_data["artifact_hashes"]["code"] == new_code_hashes
            assert state_data["artifact_hashes"]["old"] is None  # Old data replaced
        finally:
            os.chdir(original_cwd)
