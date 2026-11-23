import os
import json
import tempfile
import pytest
import hashlib

from loaders import compute_file_hash, load_checksums, save_checksums, verify_checksum

class TestChecksums:
    """Unit tests for checksumming functionality in loaders.py"""

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file with known content."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Hello, World!")
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for checksum file."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        import shutil
        shutil.rmtree(temp_dir)

    def test_compute_file_hash(self, temp_file):
        """Test that file hash is computed correctly."""
        expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
        actual_hash = compute_file_hash(temp_file)
        assert actual_hash == expected_hash

    def test_verify_checksum_match(self, temp_file):
        """Test verification when hash matches."""
        h = compute_file_hash(temp_file)
        assert verify_checksum(temp_file, h) is True

    def test_verify_checksum_mismatch(self, temp_file):
        """Test verification when hash does not match."""
        wrong_hash = "a" * 64
        assert verify_checksum(temp_file, wrong_hash) is False

    def test_verify_checksum_missing_file(self):
        """Test verification when file does not exist."""
        assert verify_checksum("/nonexistent/file.txt", "hash") is False

    def test_save_and_load_checksums(self, temp_dir, temp_file):
        """Test saving and loading checksums to/from JSON."""
        checksums_path = os.path.join(temp_dir, "checksums.json")
        h = compute_file_hash(temp_file)
        checksums = {temp_file: h}
        
        save_checksums(checksums, checksums_path)
        loaded = load_checksums(checksums_path)
        
        assert loaded == checksums
        assert loaded[temp_file] == h

    def test_load_checksums_missing_file(self, temp_dir):
        """Test loading checksums when file does not exist."""
        checksums_path = os.path.join(temp_dir, "nonexistent.json")
        loaded = load_checksums(checksums_path)
        assert loaded == {}

    def test_compute_file_hash_nonexistent(self):
        """Test that compute_file_hash raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            compute_file_hash("/nonexistent/file.txt")
