import os
import json
import tempfile
from pathlib import Path
import pytest

from code.utils.setup_dirs import (
    initialize_directories,
    compute_file_checksum,
    verify_checksum,
    save_checksum,
    load_checksum,
    verify_integrity,
    DIRECTORIES
)

class TestInitializeDirectories:
    def test_creates_required_directories(self, tmp_path):
        """Test that all required directories are created."""
        result = initialize_directories(tmp_path)
        
        # Check that all expected directories were created
        for dir_name in DIRECTORIES:
            expected_path = tmp_path / dir_name
            assert expected_path.exists(), f"Directory {dir_name} was not created"
            assert expected_path.is_dir(), f"{dir_name} exists but is not a directory"
            
        # Check return value
        assert len(result) == len(DIRECTORIES)
        for r in result:
            assert Path(r).exists()

    def test_does_not_fail_if_exists(self, tmp_path):
        """Test that the function doesn't fail if directories already exist."""
        # Create one directory manually
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "raw").mkdir()
        
        # Should not raise an exception
        result = initialize_directories(tmp_path)
        assert len(result) > 0

    def test_handles_nested_directories(self, tmp_path):
        """Test that nested directories are created correctly."""
        # Only create the root, ensure nested ones are created
        result = initialize_directories(tmp_path)
        
        # Check a nested directory
        nested = tmp_path / "code" / "analysis"
        assert nested.exists()
        assert nested.is_dir()


class TestComputeFileChecksum:
    def test_sha256_checksum(self, tmp_path):
        """Test SHA256 checksum computation."""
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)
        
        checksum = compute_file_checksum(test_file)
        
        # Verify it's a valid hex string of correct length
        assert len(checksum) == 64  # SHA256 produces 64 hex chars
        assert all(c in '0123456789abcdef' for c in checksum.lower())

    def test_different_content_different_checksum(self, tmp_path):
        """Test that different content produces different checksums."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        file1.write_text("Content A")
        file2.write_text("Content B")
        
        checksum1 = compute_file_checksum(file1)
        checksum2 = compute_file_checksum(file2)
        
        assert checksum1 != checksum2

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing files."""
        missing_file = tmp_path / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(missing_file)

    def test_unsupported_algorithm(self, tmp_path):
        """Test that ValueError is raised for unsupported algorithms."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        with pytest.raises(ValueError):
            compute_file_checksum(test_file, algorithm="invalid_algo")


class TestVerifyChecksum:
    def test_valid_checksum(self, tmp_path):
        """Test verification with a valid checksum."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        checksum = compute_file_checksum(test_file)
        
        assert verify_checksum(test_file, checksum)
        
    def test_invalid_checksum(self, tmp_path):
        """Test verification with an invalid checksum."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        assert not verify_checksum(test_file, "wrong_checksum")
        
    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            verify_checksum(tmp_path / "nonexistent.txt", "some_checksum")


class TestSaveAndLoadChecksum:
    def test_save_and_load_roundtrip(self, tmp_path):
        """Test that checksums can be saved and loaded correctly."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content for checksum")
        
        checksum_path = tmp_path / "test.txt.checksum.json"
        
        # Save checksum
        saved_checksum = save_checksum(test_file, checksum_path)
        
        # Verify file was created
        assert checksum_path.exists()
        
        # Load checksum
        loaded_data = load_checksum(checksum_path)
        
        # Verify content
        assert loaded_data["checksum"] == saved_checksum
        assert loaded_data["algorithm"] == "sha256"
        assert "file" in loaded_data
        assert "timestamp" in loaded_data

    def test_load_nonexistent(self, tmp_path):
        """Test that FileNotFoundError is raised when loading missing checksum."""
        with pytest.raises(FileNotFoundError):
            load_checksum(tmp_path / "nonexistent.checksum.json")


class TestVerifyIntegrity:
    def test_valid_integrity(self, tmp_path):
        """Test integrity verification with valid checksum."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Integrity test content")
        
        # Save checksum first
        save_checksum(test_file)
        
        # Verify integrity
        assert verify_integrity(test_file)

    def test_modified_file(self, tmp_path):
        """Test integrity verification fails when file is modified."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Original content")
        
        # Save checksum
        save_checksum(test_file)
        
        # Modify file
        test_file.write_text("Modified content")
        
        # Verify should fail
        assert not verify_integrity(test_file)

    def test_missing_checksum_file(self, tmp_path):
        """Test integrity verification returns False when checksum file is missing."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content")
        
        # No checksum file created
        assert not verify_integrity(test_file)

    def test_missing_data_file(self, tmp_path):
        """Test integrity verification returns False when data file is missing."""
        # Create a checksum file for a non-existent file
        checksum_data = {
            "file": str(tmp_path / "nonexistent.txt"),
            "algorithm": "sha256",
            "checksum": "abc123",
            "timestamp": "0"
        }
        checksum_file = tmp_path / "nonexistent.txt.checksum.json"
        checksum_file.write_text(json.dumps(checksum_data))
        
        # Verify should return False (file not found)
        assert not verify_integrity(tmp_path / "nonexistent.txt")
