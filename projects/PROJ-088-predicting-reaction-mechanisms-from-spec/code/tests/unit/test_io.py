"""
Unit tests for src/utils/io.py
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
    get_file_size,
)


class TestCalculateFileChecksum:
    def test_sha256_checksum(self, tmp_path):
        """Test that SHA256 checksum is calculated correctly."""
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)

        checksum = calculate_file_checksum(test_file)

        # Known SHA256 for "Hello, World!"
        expected = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
        assert checksum == expected

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_file_checksum("/nonexistent/file.txt")

    def test_unsupported_algorithm(self, tmp_path):
        """Test that ValueError is raised for unsupported algorithm."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("data")
        with pytest.raises(ValueError):
            calculate_file_checksum(test_file, algorithm="invalid_algo")


class TestEnsureDirectoryExists:
    def test_creates_new_directory(self, tmp_path):
        """Test that a new directory is created."""
        new_dir = tmp_path / "new" / "sub" / "dir"
        result = ensure_directory_exists(new_dir)
        assert result.exists()
        assert result.is_dir()

    def test_existing_directory(self, tmp_path):
        """Test that existing directory is returned unchanged."""
        result = ensure_directory_exists(tmp_path)
        assert result == tmp_path

    def test_path_is_file(self, tmp_path):
        """Test that NotADirectoryError is raised if path is a file."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("data")
        with pytest.raises(NotADirectoryError):
            ensure_directory_exists(test_file)


class TestJsonFileOperations:
    def test_write_and_read_json(self, tmp_path):
        """Test writing and reading JSON data."""
        data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        file_path = tmp_path / "data.json"

        write_json_file(data, file_path)
        assert file_path.exists()

        read_data = read_json_file(file_path)
        assert read_data == data

    def test_read_nonexistent_json(self, tmp_path):
        """Test that FileNotFoundError is raised for missing JSON."""
        with pytest.raises(FileNotFoundError):
            read_json_file(tmp_path / "missing.json")

    def test_invalid_json(self, tmp_path):
        """Test that JSONDecodeError is raised for invalid JSON."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("{ invalid json }")
        with pytest.raises(json.JSONDecodeError):
            read_json_file(file_path)


class TestTextFileOperations:
    def test_write_and_read_text(self, tmp_path):
        """Test writing and reading text data."""
        content = "Line 1\nLine 2\nLine 3"
        file_path = tmp_path / "text.txt"

        write_text_file(content, file_path)
        assert file_path.exists()

        read_content = read_text_file(file_path)
        assert read_content == content

    def test_read_nonexistent_text(self, tmp_path):
        """Test that FileNotFoundError is raised for missing text file."""
        with pytest.raises(FileNotFoundError):
            read_text_file(tmp_path / "missing.txt")


class TestGetFileSize:
    def test_get_size(self, tmp_path):
        """Test getting file size."""
        test_file = tmp_path / "size_test.txt"
        content = "12345"  # 5 bytes
        test_file.write_text(content)

        size = get_file_size(test_file)
        assert size == 5

    def test_size_nonexistent_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            get_file_size(tmp_path / "missing.txt")