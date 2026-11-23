"""
Unit tests for the NIST Juliet dataset download module.
"""
import os
import sys
import tempfile
import json
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.download_nist_juliet import (
    compute_sha256_file,
    generate_checksums,
    update_global_checksums
)

class TestChecksumFunctions:
    def test_compute_sha256_file(self, tmp_path):
        """Test SHA256 computation on a known file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        # Expected hash
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        result = compute_sha256_file(test_file)
        assert result == expected_hash

    def test_compute_sha256_file_nonexistent(self, tmp_path):
        """Test that computing hash on non-existent file raises error."""
        non_existent = tmp_path / "does_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            compute_sha256_file(non_existent)

class TestChecksumGeneration:
    def test_generate_checksums(self, tmp_path):
        """Test checksum generation for a directory."""
        # Create test files
        (tmp_path / "subdir").mkdir()
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "subdir" / "file2.txt"
        
        content1 = b"Content 1"
        content2 = b"Content 2"
        
        file1.write_bytes(content1)
        file2.write_bytes(content2)
        
        checksum_file = tmp_path / "checksums.json"
        result = generate_checksums(tmp_path, checksum_file)
        
        # Verify result
        assert "file1.txt" in result
        assert "subdir/file2.txt" in result
        assert result["file1.txt"] == hashlib.sha256(content1).hexdigest()
        assert result["subdir/file2.txt"] == hashlib.sha256(content2).hexdigest()
        
        # Verify file was written
        assert checksum_file.exists()
        with open(checksum_file, 'r') as f:
            saved_checksums = json.load(f)
        assert saved_checksums == result

class TestGlobalChecksumsUpdate:
    def test_update_global_checksums_new(self, tmp_path):
        """Test updating global checksums when file doesn't exist."""
        global_file = tmp_path / "global_checksums.json"
        new_checksums = {"file1.txt": "hash1"}
        
        update_global_checksums(new_checksums, global_file)
        
        assert global_file.exists()
        with open(global_file, 'r') as f:
            data = json.load(f)
        assert data == {"juliet_c/file1.txt": "hash1"}

    def test_update_global_checksums_merge(self, tmp_path):
        """Test merging new checksums with existing ones."""
        global_file = tmp_path / "global_checksums.json"
        
        # Create existing checksums
        existing = {"other/file.txt": "old_hash"}
        with open(global_file, 'w') as f:
            json.dump(existing, f)
        
        new_checksums = {"juliet_file.txt": "new_hash"}
        update_global_checksums(new_checksums, global_file)
        
        with open(global_file, 'r') as f:
            data = json.load(f)
        
        assert data == {
            "other/file.txt": "old_hash",
            "juliet_c/juliet_file.txt": "new_hash"
        }

class TestIntegration:
    @patch('src.data.download_nist_juliet.subprocess.run')
    @patch('src.data.download_nist_juliet.shutil.rmtree')
    @patch('src.data.download_nist_juliet.shutil.copy2')
    def test_clone_and_extract_logic(self, mock_copy, mock_rmtree, mock_run, tmp_path):
        """Test the logic of cloning and extracting without actually running git."""
        from src.data.download_nist_juliet import clone_juliet_repo, extract_c_cpp_test_cases
        
        # Mock subprocess.run to avoid actual git clone
        mock_run.return_value = MagicMock(returncode=0)
        
        # Create a mock directory structure
        mock_clone_dir = tmp_path / "mock_clone"
        mock_clone_dir.mkdir()
        (mock_clone_dir / "c").mkdir()
        (mock_clone_dir / "c" / "cwe_119").mkdir()
        test_file = mock_clone_dir / "c" / "cwe_119" / "test.c"
        test_file.write_text("int x = 0;")
        
        # Test clone
        clone_juliet_repo(mock_clone_dir)
        mock_run.assert_called_once()
        
        # Test extract
        output_dir = tmp_path / "output"
        result_dir = extract_c_cpp_test_cases(mock_clone_dir, output_dir)
        
        assert result_dir.exists()
        # Verify file was copied
        copied_file = result_dir / "cwe_119" / "test.c"
        assert copied_file.exists()
        assert copied_file.read_text() == "int x = 0;"