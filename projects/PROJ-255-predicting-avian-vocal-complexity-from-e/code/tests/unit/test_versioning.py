"""
Unit tests for the versioning module (T039).
"""
import os
import sys
import tempfile
import json
import hashlib
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.versioning import calculate_file_hash, get_files_to_hash, generate_hashes, save_hashes

class TestVersioning:
    def test_calculate_file_hash(self, tmp_path):
        """Test that calculate_file_hash returns correct SHA-256."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = calculate_file_hash(test_file)
        
        assert actual_hash == expected_hash
        assert len(actual_hash) == 64  # SHA-256 hex length

    def test_calculate_file_hash_large_file(self, tmp_path):
        """Test hashing with a larger file."""
        test_file = tmp_path / "large.bin"
        # Create a 1MB file
        content = os.urandom(1024 * 1024)
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = calculate_file_hash(test_file)
        
        assert actual_hash == expected_hash

    def test_get_files_to_hash_directory(self, tmp_path):
        """Test get_files_to_hash with a directory pattern."""
        # Create subdirectory structure
        (tmp_path / "sub1").mkdir()
        (tmp_path / "sub2").mkdir()
        (tmp_path / "file1.txt").touch()
        (tmp_path / "sub1" / "file2.txt").touch()
        
        files = get_files_to_hash(tmp_path, "*")
        
        # Should find all files
        assert len(files) == 2
        assert any("file1.txt" in str(f) for f in files)
        assert any("file2.txt" in str(f) for f in files)

    def test_get_files_to_hash_specific_file(self, tmp_path):
        """Test get_files_to_hash with a specific file path."""
        test_file = tmp_path / "specific.txt"
        test_file.touch()
        
        files = get_files_to_hash(tmp_path, "specific.txt")
        
        assert len(files) == 1
        assert files[0] == test_file

    def test_save_hashes(self, tmp_path):
        """Test that save_hashes creates a valid JSON file."""
        test_hashes = {
            "data/file1.csv": "abc123...",
            "data/file2.json": "def456..."
        }
        output_path = tmp_path / "hashes.json"
        
        result_path = save_hashes(test_hashes, output_path)
        
        assert result_path.exists()
        assert result_path == output_path
        
        with open(result_path, "r") as f:
            data = json.load(f)
        
        assert "hashes" in data
        assert data["hashes"] == test_hashes
        assert data["project"] == "PROJ-255-predicting-avian-vocal-complexity-from-e"