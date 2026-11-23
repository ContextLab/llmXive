import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Adjust imports based on project structure
# Assuming tests are in code/tests/unit and src is in code/src
import sys
from pathlib import Path
code_root = Path(__file__).resolve().parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.data.download_nist_juliet import (
    compute_sha256_file,
    extract_c_cpp_test_cases,
    generate_checksums,
    update_global_checksums
)

class TestDownloadNistJuliet:
    """Unit tests for the NIST Juliet download module."""

    def test_compute_sha256_file(self, tmp_path):
        """Test SHA256 computation on a temporary file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        checksum = compute_sha256_file(test_file)
        # Known SHA256 for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected

    def test_generate_checksums(self, tmp_path):
        """Test checksum generation for multiple files."""
        file1 = tmp_path / "file1.c"
        file1.write_text("int a = 1;")
        file2 = tmp_path / "file2.cpp"
        file2.write_text("int b = 2;")
        
        files = [file1, file2]
        checksums = generate_checksums(files)
        
        assert len(checksums) == 2
        assert "file1.c" in checksums
        assert "file2.cpp" in checksums
        assert checksums["file1.c"] == compute_sha256_file(file1)
        assert checksums["file2.cpp"] == compute_sha256_file(file2)

    def test_update_global_checksums_new_file(self, tmp_path):
        """Test updating checksums when the global file does not exist."""
        global_file = tmp_path / "checksums.json"
        new_checksums = {"test.c": "abc123"}
        
        update_global_checksums(new_checksums, global_file)
        
        assert global_file.exists()
        with open(global_file) as f:
            data = json.load(f)
        
        assert "juliet_c_cpp" in data
        assert data["juliet_c_cpp"]["test.c"] == "abc123"

    def test_update_global_checksums_existing_file(self, tmp_path):
        """Test updating checksums when the global file already exists."""
        global_file = tmp_path / "checksums.json"
        initial_data = {"existing": {"foo.c": "xyz789"}}
        with open(global_file, 'w') as f:
            json.dump(initial_data, f)
        
        new_checksums = {"test.c": "abc123"}
        update_global_checksums(new_checksums, global_file)
        
        with open(global_file) as f:
            data = json.load(f)
        
        # Original data should remain
        assert "existing" in data
        assert data["existing"]["foo.c"] == "xyz789"
        # New data should be added
        assert "juliet_c_cpp" in data
        assert data["juliet_c_cpp"]["test.c"] == "abc123"

    @patch('src.data.download_nist_juliet.os.walk')
    @patch('src.data.download_nist_juliet.shutil.copy2')
    def test_extract_c_cpp_test_cases(self, mock_copy, mock_walk, tmp_path):
        """Test extraction of C/C++ files from a mock directory structure."""
        # Setup mock directory structure
        mock_clone_dir = tmp_path / "clone"
        mock_clone_dir.mkdir()
        mock_c_cpp_dir = mock_clone_dir / "C_C++"
        mock_c_cpp_dir.mkdir()
        
        # Create a fake file
        fake_file = mock_c_cpp_dir / "test.c"
        fake_file.write_text("int x;")
        
        # Mock os.walk to return our fake structure
        mock_walk.return_value = [
            (str(mock_c_cpp_dir), [], ["test.c"])
        ]
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        result = extract_c_cpp_test_cases(mock_clone_dir, output_dir)
        
        # Verify copy was called
        assert mock_copy.called
        # Verify result contains the path to the copied file
        assert len(result) == 1
        assert result[0].name == "C_C++_test.c"
        assert result[0].exists()