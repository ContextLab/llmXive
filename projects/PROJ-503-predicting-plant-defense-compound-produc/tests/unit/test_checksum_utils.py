import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the module functions
from code.checksum_utils import (
    calculate_sha256,
    generate_checksums,
    load_checksums,
    validate_checksums
)


class TestCalculateSha256:
    def test_calculate_sha256_empty_file(self, tmp_path):
        """Test SHA-256 calculation for an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.touch()
        
        expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        result = calculate_sha256(str(test_file))
        
        assert result == expected_hash

    def test_calculate_sha256_simple_content(self, tmp_path):
        """Test SHA-256 calculation for a file with simple content."""
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)
        
        # Known SHA-256 hash for "Hello, World!"
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        result = calculate_sha256(str(test_file))
        
        assert result == expected_hash

    def test_calculate_sha256_nonexistent_file(self):
        """Test that FileNotFoundError is raised for non-existent file."""
        with pytest.raises(FileNotFoundError):
            calculate_sha256("/nonexistent/path/file.txt")


class TestGenerateChecksums:
    def test_generate_checksums_single_file(self, tmp_path):
        """Test generating checksums for a single file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        output_file = tmp_path / "checksums.json"
        checksums = generate_checksums([str(test_file)], str(output_file))
        
        assert str(test_file) in checksums
        assert len(checksums) == 1
        assert output_file.exists()
        
        # Verify the saved checksum matches calculated
        with open(output_file, 'r') as f:
            saved_checksums = json.load(f)
        assert saved_checksums[str(test_file)] == checksums[str(test_file)]

    def test_generate_checksums_multiple_files(self, tmp_path):
        """Test generating checksums for multiple files."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        
        output_file = tmp_path / "checksums.json"
        checksums = generate_checksums([str(file1), str(file2)], str(output_file))
        
        assert len(checksums) == 2
        assert str(file1) in checksums
        assert str(file2) in checksums

    def test_generate_checksums_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised when a file is missing."""
        existing_file = tmp_path / "exists.txt"
        existing_file.write_text("Exists")
        
        with pytest.raises(FileNotFoundError):
            generate_checksums([str(existing_file), "/nonexistent/file.txt"], str(tmp_path / "out.json"))

    def test_generate_checksums_creates_directory(self, tmp_path):
        """Test that generate_checksums creates the output directory if it doesn't exist."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test")
        
        nested_output = tmp_path / "nested" / "dir" / "checksums.json"
        generate_checksums([str(test_file)], str(nested_output))
        
        assert nested_output.exists()


class TestLoadChecksums:
    def test_load_checksums_valid_file(self, tmp_path):
        """Test loading checksums from a valid JSON file."""
        checksums_data = {
            "/path/to/file1.txt": "hash1",
            "/path/to/file2.txt": "hash2"
        }
        checksum_file = tmp_path / "checksums.json"
        checksum_file.write_text(json.dumps(checksums_data))
        
        loaded = load_checksums(str(checksum_file))
        
        assert loaded == checksums_data

    def test_load_checksums_nonexistent_file(self, tmp_path):
        """Test that FileNotFoundError is raised for non-existent checksum file."""
        with pytest.raises(FileNotFoundError):
            load_checksums(str(tmp_path / "nonexistent.json"))

    def test_load_checksums_invalid_json(self, tmp_path):
        """Test that JSONDecodeError is raised for invalid JSON."""
        checksum_file = tmp_path / "bad.json"
        checksum_file.write_text("not valid json")
        
        with pytest.raises(json.JSONDecodeError):
            load_checksums(str(checksum_file))


class TestValidateChecksums:
    def test_validate_checksums_all_valid(self, tmp_path):
        """Test validation when all files match expected checksums."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content 1")
        
        checksums = {
            str(file1): calculate_sha256(str(file1))
        }
        
        valid, invalid = validate_checksums([str(file1)], checksums)
        
        assert len(valid) == 1
        assert len(invalid) == 0
        assert str(file1) in valid

    def test_validate_checksums_mismatch(self, tmp_path):
        """Test validation when checksums don't match."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content 1")
        
        wrong_hash = "0" * 64
        checksums = {
            str(file1): wrong_hash
        }
        
        valid, invalid = validate_checksums([str(file1)], checksums)
        
        assert len(valid) == 0
        assert len(invalid) == 1
        assert str(file1) in invalid
        assert invalid[str(file1)]["actual"] != wrong_hash

    def test_validate_checksums_missing_file(self, tmp_path):
        """Test validation when a file is missing."""
        existing_file = tmp_path / "exists.txt"
        existing_file.write_text("Exists")
        
        checksums = {
            str(existing_file): calculate_sha256(str(existing_file)),
            "/nonexistent/file.txt": "somehash"
        }
        
        valid, invalid = validate_checksums([str(existing_file), "/nonexistent/file.txt"], checksums)
        
        assert len(valid) == 1
        assert len(invalid) == 1
        assert "/nonexistent/file.txt" in invalid
        assert invalid["/nonexistent/file.txt"]["actual"] == "FILE_NOT_FOUND"

    def test_validate_checksums_no_expected(self, tmp_path, caplog):
        """Test validation when a file has no expected checksum."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content")
        
        checksums = {}
        
        valid, invalid = validate_checksums([str(file1)], checksums)
        
        assert len(valid) == 0
        assert len(invalid) == 0
        assert "No expected checksum found" in caplog.text