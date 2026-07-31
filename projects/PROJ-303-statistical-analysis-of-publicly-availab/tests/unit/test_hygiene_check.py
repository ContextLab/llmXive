"""
Unit tests for the hygiene_check.py script.

These tests verify:
- SHA-256 computation for known files
- Directory scanning logic
- Manifest generation
"""
import os
import tempfile
import hashlib
import yaml
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the functions to test
from src.scripts.hygiene_check import compute_sha256, scan_raw_data_directory, write_manifest

class TestHygieneCheck:
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create subdirectories
            (tmp_path / "subdir1").mkdir()
            (tmp_path / "subdir2").mkdir()
            
            # Create test files with known content
            test_files = {
                "file1.txt": b"Hello, World!",
                "subdir1/file2.txt": b"Test content 1",
                "subdir2/file3.txt": b"Test content 2",
                ".hidden_file": b"Should be ignored"
            }
            
            for rel_path, content in test_files.items():
                file_path = tmp_path / rel_path
                file_path.write_bytes(content)
            
            yield tmp_path
    
    def test_compute_sha256(self, temp_dir):
        """Test SHA-256 computation against known values."""
        file_path = temp_dir / "file1.txt"
        expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
        
        computed_hash = compute_sha256(file_path)
        
        assert computed_hash == expected_hash
        assert len(computed_hash) == 64  # SHA-256 hex length
    
    def test_compute_sha256_empty_file(self, temp_dir):
        """Test SHA-256 computation on an empty file."""
        empty_file = temp_dir / "empty.txt"
        empty_file.write_bytes(b"")
        
        expected_hash = hashlib.sha256(b"").hexdigest()
        computed_hash = compute_sha256(empty_file)
        
        assert computed_hash == expected_hash
    
    def test_compute_sha256_nonexistent_file(self, temp_dir):
        """Test that computing hash of nonexistent file raises FileNotFoundError."""
        nonexistent = temp_dir / "does_not_exist.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_sha256(nonexistent)
    
    def test_scan_raw_data_directory(self, temp_dir):
        """Test directory scanning and hashing."""
        file_hashes = scan_raw_data_directory(temp_dir)
        
        # Should find 3 files (excluding hidden file)
        assert len(file_hashes) == 3
        
        # Check that all expected files are present
        file_paths = [f["file_path"] for f in file_hashes]
        assert any("file1.txt" in p for p in file_paths)
        assert any("file2.txt" in p for p in file_paths)
        assert any("file3.txt" in p for p in file_paths)
        
        # Verify no hidden files
        assert not any(".hidden_file" in p for p in file_paths)
        
        # Check that hashes are computed correctly
        for f in file_hashes:
            assert "sha256" in f
            assert len(f["sha256"]) == 64
            assert "size_bytes" in f
            assert "file_path" in f
    
    def test_scan_nonexistent_directory(self):
        """Test that scanning nonexistent directory raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            scan_raw_data_directory(Path("/nonexistent/path"))
    
    def test_scan_not_a_directory(self, temp_dir):
        """Test that scanning a file instead of directory raises NotADirectoryError."""
        file_path = temp_dir / "file1.txt"
        
        with pytest.raises(NotADirectoryError):
            scan_raw_data_directory(file_path)
    
    def test_write_manifest(self, temp_dir):
        """Test manifest generation and YAML writing."""
        # Create mock file hash data
        mock_hashes = [
            {
                "file_path": "test.txt",
                "absolute_path": str(temp_dir / "test.txt"),
                "size_bytes": 100,
                "sha256": "abc123",
                "last_modified": "2023-01-01T00:00:00"
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manifest.yaml"
            
            write_manifest(mock_hashes, output_path)
            
            # Verify file was created
            assert output_path.exists()
            
            # Verify YAML content
            with open(output_path, 'r') as f:
                manifest = yaml.safe_load(f)
            
            assert "metadata" in manifest
            assert "files" in manifest
            assert manifest["metadata"]["total_files"] == 1
            assert manifest["metadata"]["total_size_bytes"] == 100
            assert len(manifest["files"]) == 1
            assert manifest["files"][0]["file_path"] == "test.txt"
    
    def test_write_manifest_empty_list(self, temp_dir):
        """Test manifest generation with empty file list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty_manifest.yaml"
            
            write_manifest([], output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                manifest = yaml.safe_load(f)
            
            assert manifest["metadata"]["total_files"] == 0
            assert manifest["metadata"]["total_size_bytes"] == 0
            assert manifest["files"] == []
    
    def test_file_size_accuracy(self, temp_dir):
        """Test that reported file size matches actual file size."""
        file_path = temp_dir / "file1.txt"
        expected_size = file_path.stat().st_size
        
        file_hashes = scan_raw_data_directory(temp_dir)
        
        for f in file_hashes:
            if "file1.txt" in f["file_path"]:
                assert f["size_bytes"] == expected_size
                break
        else:
            pytest.fail("file1.txt not found in scan results")