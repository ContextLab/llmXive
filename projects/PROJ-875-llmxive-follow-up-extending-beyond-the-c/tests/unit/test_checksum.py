"""
Unit tests for checksum utility.

Tests the functionality of utils/checksum.py including:
- SHA-256 calculation
- File discovery
- Manifest generation and saving
- Verification logic
"""
import os
import sys
import tempfile
import hashlib
from pathlib import Path
import pytest
import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "utils"))

from checksum import (
    calculate_sha256,
    get_files_to_checksum,
    generate_checksum_manifest,
    save_manifest,
    load_manifest,
    verify_checksums,
    SUPPORTED_EXTENSIONS,
    DATA_PROCESSED_DIR
)

class TestCalculateSha256:
    """Tests for SHA-256 calculation."""
    
    def test_calculate_sha256_known_value(self, tmp_path):
        """Test SHA-256 calculation with known input."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = calculate_sha256(test_file)
        
        assert actual_hash == expected_hash
    
    def test_calculate_sha256_empty_file(self, tmp_path):
        """Test SHA-256 calculation for empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = calculate_sha256(test_file)
        
        assert actual_hash == expected_hash
    
    def test_calculate_sha256_large_file(self, tmp_path):
        """Test SHA-256 calculation for large file (chunked reading)."""
        test_file = tmp_path / "large.bin"
        content = b"x" * (1024 * 1024)  # 1MB
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = calculate_sha256(test_file)
        
        assert actual_hash == expected_hash
    
    def test_calculate_sha256_nonexistent_file(self, tmp_path):
        """Test SHA-256 calculation for nonexistent file raises error."""
        nonexistent = tmp_path / "does_not_exist.txt"
        
        with pytest.raises(FileNotFoundError):
            calculate_sha256(nonexistent)

class TestGetFilesToChecksum:
    """Tests for file discovery."""
    
    def test_get_files_to_checksum_basic(self, tmp_path):
        """Test basic file discovery."""
        # Create test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.json").write_text("{}")
        (tmp_path / "file3.csv").write_text("a,b,c")
        (tmp_path / "file4.bin").write_bytes(b"binary")
        
        files = get_files_to_checksum(tmp_path)
        
        # Should find txt, json, csv but not bin
        assert len(files) == 3
        assert all(f.suffix in SUPPORTED_EXTENSIONS for f in files)
    
    def test_get_files_to_checksum_recursive(self, tmp_path):
        """Test recursive file discovery."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        (tmp_path / "file1.txt").write_text("content1")
        (subdir / "file2.txt").write_text("content2")
        (subdir / "file3.json").write_text("{}")
        
        files = get_files_to_checksum(tmp_path)
        
        assert len(files) == 3
    
    def test_get_files_to_checksum_empty_dir(self, tmp_path):
        """Test file discovery in empty directory."""
        files = get_files_to_checksum(tmp_path)
        assert files == []
    
    def test_get_files_to_checksum_nonexistent_dir(self, tmp_path):
        """Test file discovery in nonexistent directory."""
        nonexistent = tmp_path / "does_not_exist"
        files = get_files_to_checksum(nonexistent)
        assert files == []
    
    def test_get_files_to_checksum_custom_extensions(self, tmp_path):
        """Test file discovery with custom extensions."""
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.xyz").write_text("content2")
        
        files = get_files_to_checksum(tmp_path, extensions={".txt"})
        
        assert len(files) == 1
        assert files[0].suffix == ".txt"

class TestGenerateChecksumManifest:
    """Tests for manifest generation."""
    
    def test_generate_checksum_manifest_basic(self, tmp_path):
        """Test basic manifest generation."""
        # Create test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.json").write_text("{}")
        
        manifest = generate_checksum_manifest(tmp_path)
        
        assert manifest["file_count"] == 2
        assert "checksums" in manifest
        assert "sha256" in manifest["checksums"]["file1.txt"]
        assert "size_bytes" in manifest["checksums"]["file1.txt"]
        assert "last_modified" in manifest["checksums"]["file1.txt"]
    
    def test_generate_checksum_manifest_empty(self, tmp_path):
        """Test manifest generation for empty directory."""
        manifest = generate_checksum_manifest(tmp_path)
        
        assert manifest["file_count"] == 0
        assert manifest["checksums"] == {}
    
    def test_generate_checksum_manifest_nonexistent_dir(self, tmp_path):
        """Test manifest generation for nonexistent directory."""
        nonexistent = tmp_path / "does_not_exist"
        
        with pytest.raises(FileNotFoundError):
            generate_checksum_manifest(nonexistent)

class TestSaveAndLoadManifest:
    """Tests for manifest persistence."""
    
    def test_save_and_load_manifest(self, tmp_path):
        """Test saving and loading a manifest."""
        manifest = {
            "version": "1.0",
            "generated_at": "2024-01-01T00:00:00",
            "directory": "test",
            "algorithm": "sha256",
            "file_count": 1,
            "checksums": {
                "test.txt": {
                    "sha256": "abc123",
                    "size_bytes": 100,
                    "last_modified": "2024-01-01T00:00:00"
                }
            }
        }
        
        output_path = tmp_path / "checksums.yaml"
        saved_path = save_manifest(manifest, output_path)
        
        assert saved_path.exists()
        
        loaded = load_manifest(output_path)
        
        assert loaded == manifest
    
    def test_load_nonexistent_manifest(self, tmp_path):
        """Test loading a nonexistent manifest."""
        nonexistent = tmp_path / "does_not_exist.yaml"
        
        result = load_manifest(nonexistent)
        assert result is None

class TestVerifyChecksums:
    """Tests for checksum verification."""
    
    def test_verify_checksums_success(self, tmp_path):
        """Test successful verification."""
        # Create test file
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        
        # Create manifest
        manifest = {
            "version": "1.0",
            "generated_at": "2024-01-01T00:00:00",
            "directory": "test",
            "algorithm": "sha256",
            "file_count": 1,
            "checksums": {
                "test.txt": {
                    "sha256": expected_hash,
                    "size_bytes": len(content),
                    "last_modified": "2024-01-01T00:00:00"
                }
            }
        }
        
        manifest_path = tmp_path / "checksums.yaml"
        save_manifest(manifest, manifest_path)
        
        results = verify_checksums(manifest_path)
        
        assert results["status"] == "success"
        assert results["verified"] == 1
        assert results["failed"] == 0
        assert results["missing"] == 0
    
    def test_verify_checksums_mismatch(self, tmp_path):
        """Test verification with hash mismatch."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Original content")
        
        # Create manifest with wrong hash
        manifest = {
            "version": "1.0",
            "generated_at": "2024-01-01T00:00:00",
            "directory": "test",
            "algorithm": "sha256",
            "file_count": 1,
            "checksums": {
                "test.txt": {
                    "sha256": "wrong_hash",
                    "size_bytes": 100,
                    "last_modified": "2024-01-01T00:00:00"
                }
            }
        }
        
        manifest_path = tmp_path / "checksums.yaml"
        save_manifest(manifest, manifest_path)
        
        results = verify_checksums(manifest_path)
        
        assert results["status"] == "warning"
        assert results["verified"] == 0
        assert results["failed"] == 1
        assert results["missing"] == 0
    
    def test_verify_checksums_missing_file(self, tmp_path):
        """Test verification with missing file."""
        # Create manifest referencing non-existent file
        manifest = {
            "version": "1.0",
            "generated_at": "2024-01-01T00:00:00",
            "directory": "test",
            "algorithm": "sha256",
            "file_count": 1,
            "checksums": {
                "missing.txt": {
                    "sha256": "abc123",
                    "size_bytes": 100,
                    "last_modified": "2024-01-01T00:00:00"
                }
            }
        }
        
        manifest_path = tmp_path / "checksums.yaml"
        save_manifest(manifest, manifest_path)
        
        results = verify_checksums(manifest_path)
        
        assert results["status"] == "warning"
        assert results["verified"] == 0
        assert results["failed"] == 0
        assert results["missing"] == 1
    
    def test_verify_checksums_nonexistent_manifest(self, tmp_path):
        """Test verification with nonexistent manifest."""
        nonexistent = tmp_path / "does_not_exist.yaml"
        
        results = verify_checksums(nonexistent)
        
        assert results["status"] == "error"
        assert "not found" in results["message"].lower()

class TestIntegration:
    """Integration tests for the full checksum workflow."""
    
    def test_full_workflow(self, tmp_path):
        """Test complete workflow: generate, save, verify."""
        # Create test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.json").write_text('{"key": "value"}')
        
        # Generate manifest
        manifest = generate_checksum_manifest(tmp_path)
        assert manifest["file_count"] == 2
        
        # Save manifest
        manifest_path = tmp_path / "checksums.yaml"
        save_manifest(manifest, manifest_path)
        
        # Verify
        results = verify_checksums(manifest_path)
        assert results["status"] == "success"
        assert results["verified"] == 2
        assert results["failed"] == 0
        assert results["missing"] == 0
    
    def test_detect_modification(self, tmp_path):
        """Test that file modification is detected."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")
        
        # Generate and save manifest
        manifest = generate_checksum_manifest(tmp_path)
        manifest_path = tmp_path / "checksums.yaml"
        save_manifest(manifest, manifest_path)
        
        # Modify file
        test_file.write_text("modified content")
        
        # Verify should fail
        results = verify_checksums(manifest_path)
        assert results["status"] == "warning"
        assert results["failed"] == 1
        assert results["verified"] == 0
    
    def test_detect_new_file(self, tmp_path):
        """Test that new files are not in manifest (verification ignores them)."""
        test_file1 = tmp_path / "file1.txt"
        test_file1.write_text("content1")
        
        # Generate and save manifest
        manifest = generate_checksum_manifest(tmp_path)
        manifest_path = tmp_path / "checksums.yaml"
        save_manifest(manifest, manifest_path)
        
        # Add new file
        test_file2 = tmp_path / "file2.txt"
        test_file2.write_text("content2")
        
        # Verify should still succeed (new file not in manifest)
        results = verify_checksums(manifest_path)
        assert results["status"] == "success"
        assert results["verified"] == 1
        assert results["failed"] == 0
        assert results["missing"] == 0
