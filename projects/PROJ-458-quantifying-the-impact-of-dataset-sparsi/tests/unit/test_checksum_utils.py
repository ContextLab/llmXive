"""
Unit tests for checksum_utils.py
"""
import hashlib
import tempfile
from pathlib import Path
import pytest

import sys
from pathlib import Path as PathLib
project_root = PathLib(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.checksum_utils import compute_sha256, write_checksum_file, generate_and_save_checksum


class TestComputeSha256:
    def test_compute_sha256_simple_file(self, tmp_path):
        """Test SHA-256 computation on a simple file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(test_file)
        
        assert actual_hash == expected_hash
        assert len(actual_hash) == 64  # SHA-256 hex length
        
    def test_compute_sha256_large_file(self, tmp_path):
        """Test SHA-256 computation on a larger file (chunked reading)."""
        test_file = tmp_path / "large.bin"
        # Create a 1MB file
        content = b"x" * (1024 * 1024)
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(test_file)
        
        assert actual_hash == expected_hash
        
    def test_compute_sha256_nonexistent_file(self, tmp_path):
        """Test that FileNotFoundError is raised for non-existent file."""
        non_existent = tmp_path / "does_not_exist.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_sha256(non_existent)


class TestWriteChecksumFile:
    def test_write_checksum_format(self, tmp_path):
        """Test that checksum file is written in correct format."""
        test_file = tmp_path / "test.csv"
        test_file.write_text("a,b,c\n1,2,3")
        
        checksum = hashlib.sha256(b"a,b,c\n1,2,3").hexdigest()
        output_file = tmp_path / "test.csv.sha256"
        
        write_checksum_file(checksum, output_file)
        
        assert output_file.exists()
        content = output_file.read_text()
        
        # Format: <hash>  <filename>\n
        expected_format = f"{checksum}  test.csv\n"
        assert content == expected_format
        
    def test_write_checksum_creates_parent_dirs(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        checksum = "a" * 64
        output_file = tmp_path / "subdir1" / "subdir2" / "test.csv.sha256"
        
        write_checksum_file(checksum, output_file)
        
        assert output_file.exists()


class TestGenerateAndSaveChecksum:
    def test_full_pipeline(self, tmp_path):
        """Test the complete pipeline: compute and save checksum."""
        test_file = tmp_path / "data.csv"
        content = b"col1,col2\nval1,val2"
        test_file.write_bytes(content)
        
        expected_checksum = hashlib.sha256(content).hexdigest()
        
        result = generate_and_save_checksum(test_file)
        
        assert result == expected_checksum
        
        checksum_file = tmp_path / "data.csv.sha256"
        assert checksum_file.exists()
        
        saved_content = checksum_file.read_text()
        expected_format = f"{expected_checksum}  data.csv\n"
        assert saved_content == expected_format
        
    def test_custom_output_dir(self, tmp_path):
        """Test saving checksum to a custom output directory."""
        test_file = tmp_path / "source" / "data.csv"
        test_file.parent.mkdir(parents=True)
        content = b"test"
        test_file.write_bytes(content)
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        result = generate_and_save_checksum(test_file, output_dir)
        
        assert len(result) == 64
        
        checksum_file = output_dir / "data.csv.sha256"
        assert checksum_file.exists()