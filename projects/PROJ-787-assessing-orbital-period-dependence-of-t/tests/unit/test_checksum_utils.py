import os
import json
import tempfile
from pathlib import Path
import pytest

# Import the functions to test
from code.utils.checksum_utils import (
    compute_file_checksum,
    save_checksum,
    verify_checksum,
    initialize_data_directories
)

class TestChecksumUtils:
    
    @pytest.fixture
    def temp_file(self, tmp_path):
        """Create a temporary file with known content."""
        file_path = tmp_path / "test_file.txt"
        content = "Hello, World! This is a test file for checksum verification."
        file_path.write_text(content)
        return file_path

    @pytest.fixture
    def temp_large_file(self, tmp_path):
        """Create a larger temporary file to test chunked reading."""
        file_path = tmp_path / "large_test_file.bin"
        # Create a file with repeated patterns
        content = (b"0123456789" * 1000) * 100  # 1MB of data
        file_path.write_bytes(content)
        return file_path

    def test_compute_file_checksum_valid_file(self, temp_file):
        """Test computing checksum for a valid file."""
        checksum = compute_file_checksum(str(temp_file))
        assert len(checksum) == 64  # SHA256 produces 64 hex characters
        assert all(c in '0123456789abcdef' for c in checksum)

    def test_compute_file_checksum_different_content_different_hash(self, tmp_path):
        """Test that different content produces different checksums."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content A")
        
        file2 = tmp_path / "file2.txt"
        file2.write_text("Content B")
        
        hash1 = compute_file_checksum(str(file1))
        hash2 = compute_file_checksum(str(file2))
        
        assert hash1 != hash2

    def test_compute_file_checksum_same_content_same_hash(self, tmp_path):
        """Test that same content produces same checksum."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Same content")
        
        file2 = tmp_path / "file2.txt"
        file2.write_text("Same content")
        
        hash1 = compute_file_checksum(str(file1))
        hash2 = compute_file_checksum(str(file2))
        
        assert hash1 == hash2

    def test_compute_file_checksum_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            compute_file_checksum("/nonexistent/path/file.txt")

    def test_save_checksum_creates_json(self, temp_file, tmp_path):
        """Test that save_checksum creates a valid JSON file."""
        checksum_path = tmp_path / "test.checksum.json"
        result_path = save_checksum(str(temp_file), str(checksum_path))
        
        assert result_path.exists()
        assert result_path == checksum_path
        
        with open(checksum_path, "r") as f:
            data = json.load(f)
        
        assert "checksum" in data
        assert "algorithm" in data
        assert data["algorithm"] == "sha256"
        assert len(data["checksum"]) == 64

    def test_verify_checksum_valid(self, temp_file, tmp_path):
        """Test verification of a valid checksum."""
        checksum_path = tmp_path / "test.checksum.json"
        save_checksum(str(temp_file), str(checksum_path))
        
        assert verify_checksum(str(temp_file), str(checksum_path)) is True

    def test_verify_checksum_invalid(self, temp_file, tmp_path):
        """Test verification fails when file content changes."""
        checksum_path = tmp_path / "test.checksum.json"
        save_checksum(str(temp_file), str(checksum_path))
        
        # Modify the file
        temp_file.write_text("Modified content")
        
        assert verify_checksum(str(temp_file), str(checksum_path)) is False

    def test_verify_checksum_missing_file(self, tmp_path):
        """Test verification fails when file is missing."""
        checksum_path = tmp_path / "missing.checksum.json"
        with open(checksum_path, "w") as f:
            json.dump({"checksum": "abc123", "algorithm": "sha256"}, f)
        
        assert verify_checksum(str(tmp_path / "nonexistent.txt"), str(checksum_path)) is False

    def test_verify_checksum_missing_checksum_file(self, temp_file):
        """Test verification fails when checksum file is missing."""
        assert verify_checksum(str(temp_file)) is False

    def test_initialize_data_directories_creates_structure(self, tmp_path):
        """Test that initialize_data_directories creates the required structure."""
        data_dir = tmp_path / "test_data"
        directories = initialize_data_directories(str(data_dir))
        
        assert "raw" in directories
        assert "processed" in directories
        assert "interim" in directories
        
        for name, path in directories.items():
            assert path.exists()
            assert path.is_dir()
            # Check that the path is under the base directory
            assert str(path).startswith(str(data_dir))

    def test_initialize_data_directories_idempotent(self, tmp_path):
        """Test that calling initialize_data_directories multiple times is safe."""
        data_dir = tmp_path / "test_data"
        
        # First call
        dirs1 = initialize_data_directories(str(data_dir))
        
        # Second call
        dirs2 = initialize_data_directories(str(data_dir))
        
        # Paths should be the same
        assert dirs1.keys() == dirs2.keys()
        for key in dirs1:
            assert dirs1[key] == dirs2[key]

    def test_large_file_checksum(self, temp_large_file):
        """Test checksum computation for large files (chunked reading)."""
        checksum = compute_file_checksum(str(temp_large_file))
        assert len(checksum) == 64
        # Verify consistency
        checksum2 = compute_file_checksum(str(temp_large_file))
        assert checksum == checksum2
