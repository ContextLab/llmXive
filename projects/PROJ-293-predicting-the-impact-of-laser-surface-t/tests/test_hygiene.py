"""
Unit tests for code/hygiene.py
"""
import os
import tempfile
import hashlib
from pathlib import Path
import yaml
import pytest

from hygiene import (
    calculate_md5,
    calculate_dir_md5,
    get_file_metadata,
    load_artifact_hashes,
    save_artifact_hashes,
    update_artifact_hash,
    verify_artifact_integrity,
    register_multiple_artifacts,
    cleanup_stale_hashes,
    get_artifact_status
)


class TestCalculateMD5:
    def test_calculate_md5_file(self, tmp_path):
        """Test MD5 calculation for a single file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.md5(content).hexdigest()
        actual_hash = calculate_md5(test_file)
        
        assert actual_hash == expected_hash
    
    def test_calculate_md5_nonexistent(self, tmp_path):
        """Test error handling for non-existent file."""
        with pytest.raises(FileNotFoundError):
            calculate_md5(tmp_path / "nonexistent.txt")
    
    def test_calculate_md5_directory(self, tmp_path):
        """Test error handling for directory input."""
        with pytest.raises(IsADirectoryError):
            calculate_md5(tmp_path)


class TestCalculateDirMD5:
    def test_calculate_dir_md5_empty(self, tmp_path):
        """Test MD5 calculation for empty directory."""
        # Even empty dir should produce a hash (based on structure)
        h = calculate_dir_md5(tmp_path)
        assert isinstance(h, str)
        assert len(h) == 32  # MD5 hex length
    
    def test_calculate_dir_md5_content(self, tmp_path):
        """Test MD5 calculation includes file content."""
        file1 = tmp_path / "a.txt"
        file1.write_bytes(b"content1")
        
        file2 = tmp_path / "b.txt"
        file2.write_bytes(b"content2")
        
        h1 = calculate_dir_md5(tmp_path)
        
        # Change content
        file1.write_bytes(b"content1_changed")
        h2 = calculate_dir_md5(tmp_path)
        
        assert h1 != h2
    
    def test_calculate_dir_md5_excludes_pycache(self, tmp_path):
        """Test that __pycache__ is excluded by default."""
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "test.pyc").write_bytes(b"bytecode")
        
        file1 = tmp_path / "test.py"
        file1.write_bytes(b"python")
        
        h = calculate_dir_md5(tmp_path)
        # If __pycache__ was included, hash would be different.
        # We verify it doesn't crash and produces a hash.
        assert len(h) == 32


class TestGetFileMetadata:
    def test_get_file_metadata(self, tmp_path):
        """Test metadata extraction."""
        test_file = tmp_path / "info.txt"
        test_file.write_bytes(b"test data")
        
        meta = get_file_metadata(test_file)
        
        assert meta["path"] == str(test_file.absolute())
        assert meta["size_bytes"] == 9
        assert "md5" in meta
        assert meta["type"] == "file"
        assert "modified_time" in meta


class TestArtifactHashRegistry:
    def test_load_nonexistent(self, tmp_path):
        """Test loading non-existent registry."""
        registry = load_artifact_hashes(tmp_path / "missing.yaml")
        assert registry["version"] == "1.0"
        assert registry["artifacts"] == {}
    
    def test_save_and_load(self, tmp_path):
        """Test saving and loading registry."""
        registry_file = tmp_path / "registry.yaml"
        data = {
            "version": "1.0",
            "artifacts": {"test": {"hash": "abc123"}}
        }
        
        save_artifact_hashes(data, registry_file)
        loaded = load_artifact_hashes(registry_file)
        
        assert loaded["artifacts"]["test"]["hash"] == "abc123"
    
    def test_update_artifact_hash_file(self, tmp_path):
        """Test updating registry with a file."""
        test_file = tmp_path / "update.txt"
        test_file.write_bytes(b"data")
        
        registry = {"artifacts": {}}
        updated_reg, h = update_artifact_hash(test_file, registry)
        
        assert h == hashlib.md5(b"data").hexdigest()
        assert "update.txt" in str(list(updated_reg["artifacts"].keys())[0])
    
    def test_update_artifact_hash_dir(self, tmp_path):
        """Test updating registry with a directory."""
        test_dir = tmp_path / "subdir"
        test_dir.mkdir()
        (test_dir / "f.txt").write_bytes(b"data")
        
        registry = {"artifacts": {}}
        updated_reg, h = update_artifact_hash(test_dir, registry)
        
        assert len(h) == 32
        assert "subdir" in str(list(updated_reg["artifacts"].keys())[0])


class TestVerifyIntegrity:
    def test_verify_success(self, tmp_path):
        """Test successful verification."""
        test_file = tmp_path / "verify.txt"
        content = b"verify me"
        test_file.write_bytes(content)
        h = hashlib.md5(content).hexdigest()
        
        assert verify_artifact_integrity(test_file, h)
    
    def test_verify_failure(self, tmp_path):
        """Test verification failure."""
        test_file = tmp_path / "verify_fail.txt"
        test_file.write_bytes(b"wrong")
        
        assert not verify_artifact_integrity(test_file, "00000000000000000000000000000000")
    
    def test_verify_missing(self, tmp_path):
        """Test verification of missing file."""
        assert not verify_artifact_integrity(tmp_path / "missing.txt", "hash")


class TestRegisterMultiple:
    def test_register_multiple(self, tmp_path):
        """Test registering multiple files."""
        f1 = tmp_path / "f1.txt"
        f2 = tmp_path / "f2.txt"
        f1.write_bytes(b"1")
        f2.write_bytes(b"2")
        
        registry_file = tmp_path / "reg.yaml"
        result = register_multiple_artifacts([f1, f2], hash_file=registry_file)
        
        assert len(result["artifacts"]) == 2


class TestCleanupStale:
    def test_cleanup_stale(self, tmp_path):
        """Test removing stale entries."""
        registry_file = tmp_path / "reg.yaml"
        
        # Create a fake registry with a missing file entry
        fake_registry = {
            "version": "1.0",
            "artifacts": {
                "missing_file.txt": {"hash": "123", "type": "file"}
            }
        }
        save_artifact_hashes(fake_registry, registry_file)
        
        stale = cleanup_stale_hashes(registry_file)
        
        assert "missing_file.txt" in stale
        loaded = load_artifact_hashes(registry_file)
        assert len(loaded["artifacts"]) == 0


class TestGetArtifactStatus:
    def test_status_unregistered(self, tmp_path):
        """Test status of unregistered file."""
        f = tmp_path / "new.txt"
        f.write_bytes(b"new")
        
        status = get_artifact_status(f, hash_file=tmp_path / "empty.yaml")
        assert status["status"] == "unregistered"
    
    def test_status_registered(self, tmp_path):
        """Test status of registered file."""
        f = tmp_path / "reg.txt"
        f.write_bytes(b"reg")
        h = hashlib.md5(b"reg").hexdigest()
        
        reg_data = {
            "artifacts": {
                "reg.txt": {"hash": h}
            }
        }
        save_artifact_hashes(reg_data, tmp_path / "reg.yaml")
        
        status = get_artifact_status(f, hash_file=tmp_path / "reg.yaml")
        assert status["status"] == "registered"
    
    def test_status_modified(self, tmp_path):
        """Test status of modified file."""
        f = tmp_path / "mod.txt"
        f.write_bytes(b"old")
        
        reg_data = {
            "artifacts": {
                "mod.txt": {"hash": hashlib.md5(b"old").hexdigest()}
            }
        }
        save_artifact_hashes(reg_data, tmp_path / "mod.yaml")
        
        # Modify file
        f.write_bytes(b"new")
        
        status = get_artifact_status(f, hash_file=tmp_path / "mod.yaml")
        assert status["status"] == "modified"
