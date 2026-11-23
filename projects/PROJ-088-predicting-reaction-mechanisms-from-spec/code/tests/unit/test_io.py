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
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)

        checksum = calculate_file_checksum(test_file)
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex length

    def test_md5_checksum(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test")
        checksum = calculate_file_checksum(test_file, algorithm='md5')
        assert isinstance(checksum, str)
        assert len(checksum) == 32  # MD5 hex length

    def test_file_not_found(self, tmp_path):
        non_existent = tmp_path / "does_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            calculate_file_checksum(non_existent)

    def test_unsupported_algorithm(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test")
        with pytest.raises(ValueError):
            calculate_file_checksum(test_file, algorithm='invalid_algo')


class TestEnsureDirectoryExists:
    def test_create_new_directory(self, tmp_path):
        new_dir = tmp_path / "new" / "nested" / "dir"
        result = ensure_directory_exists(new_dir)
        assert result.exists()
        assert result.is_dir()

    def test_existing_directory(self, tmp_path):
        result = ensure_directory_exists(tmp_path)
        assert result == tmp_path


class TestJsonFileOperations:
    def test_write_and_read_json(self, tmp_path):
        data = {"key": "value", "number": 42}
        file_path = tmp_path / "data.json"

        write_json_file(file_path, data)
        read_data = read_json_file(file_path)

        assert read_data == data

    def test_read_nonexistent_json(self, tmp_path):
        non_existent = tmp_path / "missing.json"
        with pytest.raises(FileNotFoundError):
            read_json_file(non_existent)

    def test_write_json_creates_directory(self, tmp_path):
        nested_path = tmp_path / "new_dir" / "data.json"
        write_json_file(nested_path, {"test": 1})
        assert nested_path.exists()


class TestTextFileOperations:
    def test_write_and_read_text(self, tmp_path):
        content = "Line 1\nLine 2"
        file_path = tmp_path / "text.txt"

        write_text_file(file_path, content)
        read_content = read_text_file(file_path)

        assert read_content == content

    def test_read_nonexistent_text(self, tmp_path):
        non_existent = tmp_path / "missing.txt"
        with pytest.raises(FileNotFoundError):
            read_text_file(non_existent)


class TestGetFileSize:
    def test_get_size(self, tmp_path):
        test_file = tmp_path / "size.txt"
        content = "12345"
        test_file.write_text(content)

        size = get_file_size(test_file)
        assert size == len(content.encode('utf-8'))

    def test_get_size_nonexistent(self, tmp_path):
        non_existent = tmp_path / "missing.txt"
        with pytest.raises(FileNotFoundError):
            get_file_size(non_existent)