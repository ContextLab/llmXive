"""
Unit tests for src/utils/io.py utilities.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from src.utils.io import (
    calculate_file_checksum,
    ensure_directory_exists,
    write_json_file,
    read_json_file,
    write_text_file,
    read_text_file,
    get_file_size
)


class TestCalculateFileChecksum:
    def test_sha256_checksum(self, tmp_path):
        """Test SHA256 checksum calculation."""
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)
        
        checksum = calculate_file_checksum(test_file)
        
        # Known SHA256 for "Hello, World!"
        expected = "7f83b1657ff1fc53b92dc18148a1d65dfa61083216042d3e7f046047083d4251"
        assert checksum == expected
        
    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            calculate_file_checksum("/nonexistent/file.txt")
            
    def test_invalid_algorithm(self, tmp_path):
        """Test that ValueError is raised for unsupported algorithms."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        with pytest.raises(ValueError):
            calculate_file_checksum(test_file, algorithm="invalid_algo")


class TestEnsureDirectoryExists:
    def test_create_new_directory(self, tmp_path):
        """Test creation of a new directory."""
        new_dir = tmp_path / "subdir" / "nested"
        result = ensure_directory_exists(new_dir)
        
        assert result.exists()
        assert result.is_dir()
        
    def test_existing_directory(self, tmp_path):
        """Test that existing directory is not modified."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        
        result = ensure_directory_exists(existing_dir)
        
        assert result == existing_dir


class TestJsonFileOperations:
    def test_write_and_read_json(self, tmp_path):
        """Test writing and reading JSON files."""
        test_file = tmp_path / "data.json"
        data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        
        write_json_file(test_file, data)
        read_data = read_json_file(test_file)
        
        assert read_data == data
        
    def test_read_nonexistent_json(self, tmp_path):
        """Test reading a non-existent JSON file."""
        with pytest.raises(FileNotFoundError):
            read_json_file(tmp_path / "missing.json")
            
    def test_invalid_json(self, tmp_path):
        """Test reading an invalid JSON file."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("{ invalid json }")
        
        with pytest.raises(json.JSONDecodeError):
            read_json_file(test_file)


class TestTextFileOperations:
    def test_write_and_read_text(self, tmp_path):
        """Test writing and reading text files."""
        test_file = tmp_path / "text.txt"
        content = "Line 1\nLine 2\nLine 3"
        
        write_text_file(test_file, content)
        read_content = read_text_file(test_file)
        
        assert read_content == content
        
    def test_read_nonexistent_text(self, tmp_path):
        """Test reading a non-existent text file."""
        with pytest.raises(FileNotFoundError):
            read_text_file(tmp_path / "missing.txt")


class TestGetFileSize:
    def test_get_file_size(self, tmp_path):
        """Test getting file size."""
        test_file = tmp_path / "size.txt"
        content = "12345"  # 5 bytes
        test_file.write_text(content)
        
        size = get_file_size(test_file)
        
        assert size == 5
        
    def test_file_not_found_size(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            get_file_size("/nonexistent/file.txt")