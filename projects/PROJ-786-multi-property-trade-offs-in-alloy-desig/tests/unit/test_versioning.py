"""
Unit tests for the versioning module.
"""
import os
import sys
import tempfile
import yaml
import hashlib
import pytest
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from versioning import (
    compute_sha256,
    compute_directory_hash,
    load_state,
    save_state,
    update_version_state
)

class TestComputeSha256:
    def test_compute_sha256_file(self):
        """Test SHA-256 computation for a simple file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            hash_result = compute_sha256(temp_path)
            # Verify it's a valid hex string
            assert len(hash_result) == 64
            assert all(c in '0123456789abcdef' for c in hash_result)
            
            # Verify against known hash
            expected_hash = hashlib.sha256(b"test content").hexdigest()
            assert hash_result == expected_hash
        finally:
            os.unlink(temp_path)

    def test_compute_sha256_nonexistent_file(self):
        """Test that FileNotFoundError is raised for non-existent file."""
        with pytest.raises(FileNotFoundError):
            compute_sha256("/nonexistent/path/file.txt")

    def test_compute_sha256_empty_file(self):
        """Test SHA-256 computation for an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            hash_result = compute_sha256(temp_path)
            expected_hash = hashlib.sha256(b"").hexdigest()
            assert hash_result == expected_hash
        finally:
            os.unlink(temp_path)

class TestComputeDirectoryHash:
    def test_compute_directory_hash_single_file(self):
        """Test directory hash with a single file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("content1")
            
            dir_hash = compute_directory_hash(temp_dir)
            assert len(dir_hash) == 64

    def test_compute_directory_hash_multiple_files(self):
        """Test directory hash with multiple files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "file1.txt"
            file2 = Path(temp_dir) / "file2.txt"
            file1.write_text("content1")
            file2.write_text("content2")
            
            dir_hash = compute_directory_hash(temp_dir)
            assert len(dir_hash) == 64
            
            # Verify determinism
            dir_hash2 = compute_directory_hash(temp_dir)
            assert dir_hash == dir_hash2

    def test_compute_directory_hash_nonexistent(self):
        """Test that FileNotFoundError is raised for non-existent directory."""
        with pytest.raises(FileNotFoundError):
            compute_directory_hash("/nonexistent/directory")

    def test_compute_directory_hash_with_extension_filter(self):
        """Test directory hash with extension filter."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "file1.txt"
            file2 = Path(temp_dir) / "file2.py"
            file1.write_text("content1")
            file2.write_text("content2")
            
            # Hash only .py files
            py_hash = compute_directory_hash(temp_dir, extensions=['.py'])
            
            # Hash all files
            all_hash = compute_directory_hash(temp_dir)
            
            assert py_hash != all_hash

class TestLoadSaveState:
    def test_load_state_nonexistent(self):
        """Test loading a non-existent state file returns empty structure."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            os.unlink(temp_path)  # Delete the file
            state = load_state(temp_path)
            assert "projects" in state
            assert "last_updated" in state
            assert state["projects"] == {}
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_and_load_state(self):
        """Test saving and loading state."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            temp_path = f.name
        
        try:
            test_state = {
                "projects": {
                    "TEST-001": {
                        "artifact_hashes": {"code": "abc123"},
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                },
                "last_updated": "2024-01-01T00:00:00Z"
            }
            
            save_state(test_state, temp_path)
            
            loaded_state = load_state(temp_path)
            assert loaded_state == test_state
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

class TestUpdateVersionState:
    def test_update_version_state_creates_project(self):
        """Test that update_version_state creates a new project entry if it doesn't exist."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            temp_path = f.name
        
        try:
            os.unlink(temp_path)  # Start with no file
            
            with tempfile.TemporaryDirectory() as temp_code_dir:
                test_file = Path(temp_code_dir) / "test.py"
                test_file.write_text("print('hello')")
                
                state = update_version_state(
                    state_path=temp_path,
                    project_id="TEST-UPDATE-001",
                    artifacts_to_hash=[temp_code_dir]
                )
                
                assert "TEST-UPDATE-001" in state["projects"]
                assert "artifact_hashes" in state["projects"]["TEST-UPDATE-001"]
                assert "updated_at" in state["projects"]["TEST-UPDATE-001"]
                assert state["projects"]["TEST-UPDATE-001"]["version"] == 1
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_update_version_state_increments_version(self):
        """Test that update_version_state increments the version on subsequent calls."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            temp_path = f.name
        
        try:
            # Initial state
            initial_state = {
                "projects": {
                    "TEST-VERSION-001": {
                        "artifact_hashes": {},
                        "updated_at": "2024-01-01T00:00:00Z",
                        "version": 1
                    }
                }
            }
            save_state(initial_state, temp_path)
            
            with tempfile.TemporaryDirectory() as temp_code_dir:
                test_file = Path(temp_code_dir) / "test.py"
                test_file.write_text("print('hello')")
                
                # First update
                state1 = update_version_state(
                    state_path=temp_path,
                    project_id="TEST-VERSION-001",
                    artifacts_to_hash=[temp_code_dir]
                )
                
                assert state1["projects"]["TEST-VERSION-001"]["version"] == 2
                
                # Second update
                state2 = update_version_state(
                    state_path=temp_path,
                    project_id="TEST-VERSION-001",
                    artifacts_to_hash=[temp_code_dir]
                )
                
                assert state2["projects"]["TEST-VERSION-001"]["version"] == 3
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_update_version_state_skips_nonexistent_artifacts(self):
        """Test that update_version_state handles non-existent artifacts gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            temp_path = f.name
        
        try:
            os.unlink(temp_path)
            
            # Try to hash a non-existent directory
            state = update_version_state(
                state_path=temp_path,
                project_id="TEST-SKIP-001",
                artifacts_to_hash=["/nonexistent/path"]
            )
            
            # Should still create the project entry but with empty hashes
            assert "TEST-SKIP-001" in state["projects"]
            assert state["projects"]["TEST-SKIP-001"]["artifact_hashes"] == {}
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
