"""
Tests for checksum utilities in code/utils/checksums.py
"""
import os
import json
import tempfile
import pytest
from pathlib import Path

from code.utils.checksums import (
    compute_file_checksum,
    generate_checksum_file,
    verify_checksums,
    verify_single_file,
    setup_data_directories
)


class TestComputeFileChecksum:
    def test_compute_sha256_known_value(self, tmp_path):
        """Test checksum of a file with known content."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = compute_file_checksum(str(test_file))
        # SHA-256 of "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected
    
    def test_compute_checksum_nonexistent_file(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            compute_file_checksum("/nonexistent/path/file.txt")
    
    def test_compute_checksum_large_file(self, tmp_path):
        """Test checksum computation on a larger file."""
        test_file = tmp_path / "large.txt"
        content = b"X" * (1024 * 1024)  # 1MB
        test_file.write_bytes(content)
        
        checksum = compute_file_checksum(str(test_file))
        assert len(checksum) == 64  # SHA-256 hex length
        assert all(c in "0123456789abcdef" for c in checksum)


class TestGenerateChecksumFile:
    def test_generate_manifest_single_file(self, tmp_path):
        """Test generating checksum manifest for a single file."""
        test_file = tmp_path / "data.txt"
        test_file.write_text("test content")
        
        manifest = generate_checksum_file(str(tmp_path))
        
        assert "data.txt" in manifest["files"]
        assert len(manifest["files"]["data.txt"]) == 64
        assert manifest["checksum_algorithm"] == "sha256"
    
    def test_generate_manifest_nested_dirs(self, tmp_path):
        """Test checksum generation with nested directories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        file1 = tmp_path / "file1.txt"
        file2 = subdir / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        manifest = generate_checksum_file(str(tmp_path))
        
        assert "file1.txt" in manifest["files"]
        assert "subdir/file2.txt" in manifest["files"]
    
    def test_generate_checksum_file_output(self, tmp_path):
        """Test generating checksum file to disk."""
        test_file = tmp_path / "data.txt"
        test_file.write_text("test")
        
        output_path = tmp_path / "checksums.json"
        result_path = generate_checksum_file(str(tmp_path), str(output_path))
        
        assert result_path == str(output_path)
        assert output_path.exists()
        
        with open(output_path, "r") as f:
            manifest = json.load(f)
        assert "files" in manifest


class TestVerifyChecksums:
    def test_verify_all_valid(self, tmp_path):
        """Test verification when all files match."""
        test_file = tmp_path / "data.txt"
        test_file.write_text("test content")
        
        manifest_path = tmp_path / "checksums.json"
        generate_checksum_file(str(tmp_path), str(manifest_path))
        
        results = verify_checksums(str(manifest_path))
        assert results["data.txt"] is True
    
    def test_verify_modified_file(self, tmp_path):
        """Test verification when a file is modified."""
        test_file = tmp_path / "data.txt"
        test_file.write_text("original content")
        
        manifest_path = tmp_path / "checksums.json"
        generate_checksum_file(str(tmp_path), str(manifest_path))
        
        # Modify the file
        test_file.write_text("modified content")
        
        results = verify_checksums(str(manifest_path))
        assert results["data.txt"] is False
    
    def test_verify_missing_file(self, tmp_path):
        """Test verification when a file is missing."""
        test_file = tmp_path / "data.txt"
        test_file.write_text("test")
        
        manifest_path = tmp_path / "checksums.json"
        generate_checksum_file(str(tmp_path), str(manifest_path))
        
        # Delete the file
        test_file.unlink()
        
        results = verify_checksums(str(manifest_path))
        assert results["data.txt"] is False


class TestVerifySingleFile:
    def test_verify_single_file_match(self, tmp_path):
        """Test single file verification with matching checksum."""
        test_file = tmp_path / "data.txt"
        test_file.write_text("test")
        
        checksum = compute_file_checksum(str(test_file))
        result = verify_single_file(str(test_file), checksum)
        assert result is True
    
    def test_verify_single_file_mismatch(self, tmp_path):
        """Test single file verification with wrong checksum."""
        test_file = tmp_path / "data.txt"
        test_file.write_text("test")
        
        wrong_checksum = "0" * 64
        result = verify_single_file(str(test_file), wrong_checksum)
        assert result is False


class TestSetupDataDirectories:
    def test_setup_creates_directories(self, tmp_path):
        """Test that setup_data_directories creates the expected structure."""
        data_dir = tmp_path / "data"
        setup_data_directories(str(data_dir))
        
        assert (data_dir / "raw").exists()
        assert (data_dir / "processed").exists()
        assert (data_dir / "analysis").exists()
        assert (data_dir / ".gitkeep").exists()
        assert (data_dir / "raw" / ".gitkeep").exists()
        assert (data_dir / "processed" / ".gitkeep").exists()
        assert (data_dir / "analysis" / ".gitkeep").exists()
    
    def test_setup_idempotent(self, tmp_path):
        """Test that calling setup multiple times doesn't cause errors."""
        data_dir = tmp_path / "data"
        setup_data_directories(str(data_dir))
        setup_data_directories(str(data_dir))  # Should not raise
        
        assert (data_dir / "raw").exists()
        assert (data_dir / "processed").exists()
        assert (data_dir / "analysis").exists()
    
    def test_setup_creates_gitkeep(self, tmp_path):
        """Test that .gitkeep files are created."""
        data_dir = tmp_path / "data"
        setup_data_directories(str(data_dir))
        
        for subdir in ["raw", "processed", "analysis"]:
            gitkeep = data_dir / subdir / ".gitkeep"
            assert gitkeep.exists()
            content = gitkeep.read_text()
            assert "llmXive" in content
