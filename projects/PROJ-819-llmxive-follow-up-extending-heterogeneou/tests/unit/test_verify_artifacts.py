"""
Unit tests for verify_artifacts.py
"""
import json
import hashlib
import tempfile
from pathlib import Path
import pytest
import sys
import os

# Add parent directory to path to import verify_artifacts
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from verify_artifacts import calculate_sha256, load_manifest, verify_artifacts

class TestCalculateSha256:
    def test_calculate_sha256_valid_file(self, tmp_path):
        """Test SHA256 calculation on a valid file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = calculate_sha256(test_file)
        
        assert actual_hash == expected_hash
    
    def test_calculate_sha256_nonexistent_file(self, tmp_path):
        """Test SHA256 calculation on a non-existent file."""
        nonexistent = tmp_path / "does_not_exist.txt"
        assert calculate_sha256(nonexistent) is None
    
    def test_calculate_sha256_empty_file(self, tmp_path):
        """Test SHA256 calculation on an empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_bytes(b"")
        
        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = calculate_sha256(empty_file)
        
        assert actual_hash == expected_hash

class TestLoadManifest:
    def test_load_manifest_valid(self, tmp_path):
        """Test loading a valid manifest."""
        manifest_file = tmp_path / "manifest.json"
        test_manifest = {
            "files": [
                {"path": "data/test.txt", "sha256": "abc123"}
            ]
        }
        manifest_file.write_text(json.dumps(test_manifest))
        
        loaded = load_manifest(manifest_file)
        assert loaded == test_manifest
    
    def test_load_manifest_nonexistent(self, tmp_path):
        """Test loading a non-existent manifest raises error."""
        nonexistent = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            load_manifest(nonexistent)

class TestVerifyArtifacts:
    def test_verify_all_present_and_matching(self, tmp_path):
        """Test verification when all files are present and match."""
        # Create derived directory structure
        derived_dir = tmp_path / "data" / "derived"
        derived_dir.mkdir(parents=True)
        
        # Create test files
        file1 = derived_dir / "file1.txt"
        file1.write_text("content1")
        file2 = derived_dir / "file2.txt"
        file2.write_text("content2")
        
        # Create manifest with correct hashes
        hash1 = hashlib.sha256(b"content1").hexdigest()
        hash2 = hashlib.sha256(b"content2").hexdigest()
        
        manifest = {
            "files": [
                {"path": "data/derived/file1.txt", "sha256": hash1},
                {"path": "data/derived/file2.txt", "sha256": hash2}
            ]
        }
        
        missing, mismatches, verified = verify_artifacts(derived_dir, manifest)
        
        assert len(missing) == 0
        assert len(mismatches) == 0
        assert len(verified) == 2
        assert "data/derived/file1.txt" in verified
        assert "data/derived/file2.txt" in verified
    
    def test_verify_missing_file(self, tmp_path):
        """Test verification when a file is missing."""
        derived_dir = tmp_path / "data" / "derived"
        derived_dir.mkdir(parents=True)
        
        # Create only one file
        file1 = derived_dir / "file1.txt"
        file1.write_text("content1")
        
        # Manifest expects two files
        manifest = {
            "files": [
                {"path": "data/derived/file1.txt", "sha256": "hash1"},
                {"path": "data/derived/file2.txt", "sha256": "hash2"}
            ]
        }
        
        missing, mismatches, verified = verify_artifacts(derived_dir, manifest)
        
        assert len(missing) == 1
        assert "data/derived/file2.txt" in missing
        assert len(verified) == 1
    
    def test_verify_hash_mismatch(self, tmp_path):
        """Test verification when a file hash doesn't match."""
        derived_dir = tmp_path / "data" / "derived"
        derived_dir.mkdir(parents=True)
        
        # Create file with content
        file1 = derived_dir / "file1.txt"
        file1.write_text("actual content")
        
        # Manifest expects different hash
        wrong_hash = hashlib.sha256(b"wrong content").hexdigest()
        manifest = {
            "files": [
                {"path": "data/derived/file1.txt", "sha256": wrong_hash}
            ]
        }
        
        missing, mismatches, verified = verify_artifacts(derived_dir, manifest)
        
        assert len(missing) == 0
        assert len(mismatches) == 1
        assert mismatches[0]["path"] == "data/derived/file1.txt"
        assert len(verified) == 0
    
    def test_verify_ignores_non_derived_files(self, tmp_path):
        """Test that verification only checks data/derived/ files."""
        derived_dir = tmp_path / "data" / "derived"
        derived_dir.mkdir(parents=True)
        
        # Create a file in derived
        file1 = derived_dir / "file1.txt"
        file1.write_text("content1")
        
        # Manifest has a file outside derived (should be ignored)
        manifest = {
            "files": [
                {"path": "data/raw/something.txt", "sha256": "hash1"},
                {"path": "code/main.py", "sha256": "hash2"}
            ]
        }
        
        missing, mismatches, verified = verify_artifacts(derived_dir, manifest)
        
        assert len(missing) == 0
        assert len(mismatches) == 0
        assert len(verified) == 0
    
    def test_verify_empty_manifest(self, tmp_path):
        """Test verification with an empty manifest."""
        derived_dir = tmp_path / "data" / "derived"
        derived_dir.mkdir(parents=True)
        
        manifest = {"files": []}
        
        missing, mismatches, verified = verify_artifacts(derived_dir, manifest)
        
        assert len(missing) == 0
        assert len(mismatches) == 0
        assert len(verified) == 0