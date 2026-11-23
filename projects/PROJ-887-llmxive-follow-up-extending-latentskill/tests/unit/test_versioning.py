"""
Unit tests for src/utils/versioning.py
"""
import os
import tempfile
from pathlib import Path
import hashlib
import pytest
import yaml

from src.utils.versioning import (
    compute_sha256,
    compute_directory_hash,
    update_state_file,
    verify_artifact,
    get_artifact_state,
    batch_compute_hashes
)


class TestComputeSha256:
    """Tests for compute_sha256 function."""
    
    def test_compute_sha256_known_value(self, tmp_path):
        """Test SHA256 computation against known value."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(test_file)
        
        assert actual_hash == expected_hash
        
    def test_compute_sha256_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            compute_sha256("/nonexistent/file.txt")
            
    def test_compute_sha256_directory(self, tmp_path):
        """Test that IsADirectoryError is raised for directories."""
        with pytest.raises(IsADirectoryError):
            compute_sha256(tmp_path)


class TestComputeDirectoryHash:
    """Tests for compute_directory_hash function."""
    
    def test_empty_directory(self, tmp_path):
        """Test hash of empty directory."""
        empty_hash = compute_directory_hash(tmp_path)
        expected_empty = hashlib.sha256(b"empty_directory").hexdigest()
        assert empty_hash == expected_empty
        
    def test_directory_hash_deterministic(self, tmp_path):
        """Test that directory hash is deterministic."""
        # Create some files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        
        hash1 = compute_directory_hash(tmp_path)
        hash2 = compute_directory_hash(tmp_path)
        
        assert hash1 == hash2
        
    def test_directory_hash_changes_with_content(self, tmp_path):
        """Test that hash changes when content changes."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("original")
        hash1 = compute_directory_hash(tmp_path)
        
        test_file.write_text("modified")
        hash2 = compute_directory_hash(tmp_path)
        
        assert hash1 != hash2
        
    def test_directory_not_found(self):
        """Test that FileNotFoundError is raised for missing directory."""
        with pytest.raises(FileNotFoundError):
            compute_directory_hash("/nonexistent/directory")


class TestUpdateStateFile:
    """Tests for update_state_file function."""
    
    def test_create_new_state_file(self, tmp_path, monkeypatch):
        """Test creation of new state file."""
        # Monkeypatch get_state_path to use tmp_path
        from src.utils import versioning
        original_get_state_path = versioning.get_state_path
        versioning.get_state_path = lambda: tmp_path
        
        try:
            test_file = tmp_path / "test_artifact.txt"
            test_file.write_text("test content")
            
            state = update_state_file("test-project", test_file)
            
            assert "artifacts" in state
            assert str(test_file) in state["artifacts"]
            
            artifact_info = state["artifacts"][str(test_file)]
            assert "sha256" in artifact_info
            assert "size_bytes" in artifact_info
            assert "updated_at" in artifact_info
            
            # Verify file was written
            state_file = tmp_path / "test-project.yaml"
            assert state_file.exists()
            
        finally:
            versioning.get_state_path = original_get_state_path
            
    def test_update_existing_state_file(self, tmp_path, monkeypatch):
        """Test updating an existing state file."""
        from src.utils import versioning
        original_get_state_path = versioning.get_state_path
        versioning.get_state_path = lambda: tmp_path
        
        try:
            # Create initial state file
            state_file = tmp_path / "test-project.yaml"
            initial_state = {
                "project_id": "test-project",
                "artifacts": {
                    "old_file.txt": {"sha256": "oldhash"}
                }
            }
            with open(state_file, "w") as f:
                yaml.dump(initial_state, f)
                
            # Add new artifact
            test_file = tmp_path / "new_artifact.txt"
            test_file.write_text("new content")
            
            state = update_state_file("test-project", test_file)
            
            assert "old_file.txt" in state["artifacts"]
            assert "new_artifact.txt" in state["artifacts"]
            
        finally:
            versioning.get_state_path = original_get_state_path
            
    def test_artifact_not_found(self, tmp_path, monkeypatch):
        """Test that ValueError is raised for non-existent artifact."""
        from src.utils import versioning
        original_get_state_path = versioning.get_state_path
        versioning.get_state_path = lambda: tmp_path
        
        try:
            with pytest.raises(ValueError):
                update_state_file("test-project", tmp_path / "nonexistent.txt")
        finally:
            versioning.get_state_path = original_get_state_path


class TestVerifyArtifact:
    """Tests for verify_artifact function."""
    
    def test_verify_correct_hash(self, tmp_path):
        """Test verification with correct hash."""
        test_file = tmp_path / "test.txt"
        content = b"test content"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        
        assert verify_artifact(test_file, expected_hash) is True
        
    def test_verify_incorrect_hash(self, tmp_path):
        """Test verification with incorrect hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        wrong_hash = "wronghash"
        
        assert verify_artifact(test_file, wrong_hash) is False
        
    def test_verify_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            verify_artifact("/nonexistent/file.txt", "somehash")


class TestGetArtifactState:
    """Tests for get_artifact_state function."""
    
    def test_get_all_artifacts(self, tmp_path, monkeypatch):
        """Test retrieving all artifacts for a project."""
        from src.utils import versioning
        original_get_state_path = versioning.get_state_path
        versioning.get_state_path = lambda: tmp_path
        
        try:
            # Create state file
            state_file = tmp_path / "test-project.yaml"
            state_data = {
                "artifacts": {
                    "file1.txt": {"sha256": "hash1"},
                    "file2.txt": {"sha256": "hash2"}
                }
            }
            with open(state_file, "w") as f:
                yaml.dump(state_data, f)
                
            result = get_artifact_state("test-project")
            
            assert "file1.txt" in result
            assert "file2.txt" in result
            
        finally:
            versioning.get_state_path = original_get_state_path
            
    def test_get_specific_artifact(self, tmp_path, monkeypatch):
        """Test retrieving a specific artifact."""
        from src.utils import versioning
        original_get_state_path = versioning.get_state_path
        versioning.get_state_path = lambda: tmp_path
        
        try:
            state_file = tmp_path / "test-project.yaml"
            state_data = {
                "artifacts": {
                    "file1.txt": {"sha256": "hash1"},
                    "file2.txt": {"sha256": "hash2"}
                }
            }
            with open(state_file, "w") as f:
                yaml.dump(state_data, f)
                
            result = get_artifact_state("test-project", "file1.txt")
            
            assert result["sha256"] == "hash1"
            
        finally:
            versioning.get_state_path = original_get_state_path
            
    def test_project_not_found(self, tmp_path, monkeypatch):
        """Test that None is returned for non-existent project."""
        from src.utils import versioning
        original_get_state_path = versioning.get_state_path
        versioning.get_state_path = lambda: tmp_path
        
        try:
            result = get_artifact_state("nonexistent-project")
            assert result is None
        finally:
            versioning.get_state_path = original_get_state_path


class TestBatchComputeHashes:
    """Tests for batch_compute_hashes function."""
    
    def test_batch_compute_hashes(self, tmp_path):
        """Test computing hashes for multiple files."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        file1.write_text("content1")
        file2.write_text("content2")
        
        hashes = batch_compute_hashes([file1, file2])
        
        assert len(hashes) == 2
        assert str(file1) in hashes
        assert str(file2) in hashes
        
        # Verify individual hashes
        expected1 = hashlib.sha256(b"content1").hexdigest()
        expected2 = hashlib.sha256(b"content2").hexdigest()
        
        assert hashes[str(file1)] == expected1
        assert hashes[str(file2)] == expected2
        
    def test_batch_compute_one_missing(self, tmp_path):
        """Test that FileNotFoundError is raised if any file is missing."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("content1")
        
        with pytest.raises(FileNotFoundError):
            batch_compute_hashes([file1, tmp_path / "missing.txt"])
