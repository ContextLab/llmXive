"""
Unit tests for the data_manager module (T005 implementation).
"""

import os
import json
import hashlib
import tempfile
from pathlib import Path
import pytest

from code.data_manager import (
    calculate_sha256,
    get_all_files_in_directory,
    generate_checksums_for_raw_data,
    save_checksums,
    verify_checksums,
)


class TestCalculateSha256:
    def test_calculate_sha256_known_value(self, tmp_path):
        """Test SHA-256 calculation with a known string."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        expected_hash = hashlib.sha256(test_content).hexdigest()
        actual_hash = calculate_sha256(test_file)
        
        assert actual_hash == expected_hash
    
    def test_calculate_sha256_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_sha256(Path("/nonexistent/file.txt"))

class TestGetAllFilesInDirectory:
    def test_get_all_files(self, tmp_path):
        """Test retrieving all files from a directory."""
        # Create nested directory structure
        subdir = tmp_path / "subdir" / "nested"
        subdir.mkdir(parents=True)
        
        file1 = tmp_path / "file1.txt"
        file2 = subdir / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        files = get_all_files_in_directory(tmp_path)
        
        assert len(files) == 2
        assert file1 in files
        assert file2 in files
    
    def test_get_all_files_empty_directory(self, tmp_path):
        """Test retrieving files from an empty directory."""
        files = get_all_files_in_directory(tmp_path)
        assert files == []
    
    def test_get_all_files_nonexistent_directory(self):
        """Test retrieving files from a nonexistent directory."""
        files = get_all_files_in_directory(Path("/nonexistent"))
        assert files == []

class TestGenerateChecksumsForRawData:
    def test_generate_checksums(self, tmp_path):
        """Test checksum generation for multiple files."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.csv"
        file1.write_text("content1")
        file2.write_text("content2")
        
        checksums = generate_checksums_for_raw_data(tmp_path)
        
        assert len(checksums) == 2
        assert "file1.txt" in checksums
        assert "file2.csv" in checksums
        
        # Verify checksums are correct
        expected_hash1 = hashlib.sha256(b"content1").hexdigest()
        expected_hash2 = hashlib.sha256(b"content2").hexdigest()
        
        assert checksums["file1.txt"] == expected_hash1
        assert checksums["file2.csv"] == expected_hash2
    
    def test_generate_checksums_excludes_checksums_json(self, tmp_path):
        """Test that checksums.json is excluded from generation."""
        checksums_file = tmp_path / "checksums.json"
        data_file = tmp_path / "data.csv"
        
        checksums_file.write_text("{}")
        data_file.write_text("data")
        
        checksums = generate_checksums_for_raw_data(tmp_path)
        
        assert "checksums.json" not in checksums
        assert "data.csv" in checksums
    
    def test_generate_checksums_nonexistent_directory(self):
        """Test that FileNotFoundError is raised for nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            generate_checksums_for_raw_data(Path("/nonexistent"))

class TestSaveChecksums:
    def test_save_checksums(self, tmp_path):
        """Test saving checksums to JSON file."""
        checksums = {
            "file1.txt": "abc123",
            "file2.csv": "def456"
        }
        output_path = tmp_path / "checksums.json"
        
        save_checksums(checksums, output_path)
        
        assert output_path.exists()
        
        with open(output_path, "r") as f:
            loaded_checksums = json.load(f)
        
        assert loaded_checksums == checksums
    
    def test_save_checksums_creates_parent_dirs(self, tmp_path):
        """Test that save_checksums creates parent directories."""
        checksums = {"file.txt": "abc123"}
        output_path = tmp_path / "nested" / "dir" / "checksums.json"
        
        save_checksums(checksums, output_path)
        
        assert output_path.exists()

class TestVerifyChecksums:
    def test_verify_checksums_all_valid(self, tmp_path):
        """Test verification when all files match."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("content")
        
        checksums = {"file1.txt": hashlib.sha256(b"content").hexdigest()}
        checksums_path = tmp_path / "checksums.json"
        save_checksums(checksums, checksums_path)
        
        is_valid, failed_files = verify_checksums(tmp_path, checksums_path)
        
        assert is_valid is True
        assert failed_files == []
    
    def test_verify_checksums_mismatch(self, tmp_path):
        """Test verification when file content changes."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("original content")
        
        checksums = {"file1.txt": hashlib.sha256(b"original content").hexdigest()}
        checksums_path = tmp_path / "checksums.json"
        save_checksums(checksums, checksums_path)
        
        # Change file content
        file1.write_text("new content")
        
        is_valid, failed_files = verify_checksums(tmp_path, checksums_path)
        
        assert is_valid is False
        assert len(failed_files) == 1
        assert "file1.txt" in failed_files[0]
        assert "CHECKSUM MISMATCH" in failed_files[0]
    
    def test_verify_checksums_file_missing(self, tmp_path):
        """Test verification when file is missing."""
        checksums = {"missing.txt": "abc123"}
        checksums_path = tmp_path / "checksums.json"
        save_checksums(checksums, checksums_path)
        
        is_valid, failed_files = verify_checksums(tmp_path, checksums_path)
        
        assert is_valid is False
        assert len(failed_files) == 1
        assert "missing.txt" in failed_files[0]
        assert "FILE NOT FOUND" in failed_files[0]
    
    def test_verify_checksums_nonexistent_checksums_file(self, tmp_path):
        """Test that FileNotFoundError is raised when checksums file is missing."""
        with pytest.raises(FileNotFoundError):
            verify_checksums(tmp_path, tmp_path / "nonexistent.json")
