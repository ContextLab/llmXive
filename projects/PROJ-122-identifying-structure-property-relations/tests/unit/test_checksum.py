"""
Unit tests for checksum utilities.
"""
import pytest
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.checksum import compute_file_checksum, compute_directory_checksums, save_checksums, load_checksums

class TestChecksumUtilities:
    """Unit tests for checksum operations."""

    def test_compute_file_checksum(self):
        """Test file checksum computation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            checksum = compute_file_checksum(temp_path)
            assert checksum is not None
            assert len(checksum) == 64  # SHA-256 hex length
        finally:
            Path(temp_path).unlink()

    def test_compute_directory_checksums(self):
        """Test directory checksum computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "file1.txt").write_text("content1")
            (Path(tmpdir) / "file2.txt").write_text("content2")
            
            checksums = compute_directory_checksums(Path(tmpdir))
            assert checksums is not None
            assert len(checksums) == 2

    def test_save_and_load_checksums(self):
        """Test saving and loading checksums."""
        with tempfile.TemporaryDirectory() as tmpdir:
          checksums_path = Path(tmpdir) / "checksums.json"
          
          test_checksums = {
              "file1.txt": "abc123",
              "file2.txt": "def456"
          }
          
          save_checksums(test_checksums, str(checksums_path))
          loaded = load_checksums(str(checksums_path))
          
          assert loaded == test_checksums
