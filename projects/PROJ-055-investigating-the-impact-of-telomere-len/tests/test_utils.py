"""
Tests for the utils module.
"""
import os
import tempfile
import hashlib
from pathlib import Path
import pytest
import yaml

# Import the functions to test
from utils import generate_checksum, validate_file_exists, update_state_file


class TestGenerateChecksum:
    def test_checksum_calculation(self):
        """Test that SHA256 checksum is calculated correctly."""
        content = b"Hello, World!"
        expected_hash = hashlib.sha256(content).hexdigest()
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            actual_hash = generate_checksum(tmp_path)
            assert actual_hash == expected_hash
        finally:
            os.unlink(tmp_path)

    def test_checksum_chunked_reading(self):
        """Test that large files are read in chunks."""
        # Create a file larger than the chunk size (8192 bytes)
        chunk_size = 8192
        content = b"A" * (chunk_size * 3)
        expected_hash = hashlib.sha256(content).hexdigest()
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            actual_hash = generate_checksum(tmp_path)
            assert actual_hash == expected_hash
        finally:
            os.unlink(tmp_path)

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            generate_checksum("/nonexistent/path/file.txt")

    def test_io_error_handling(self):
        """Test that IOError is raised for unreadable files."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        # Make file unreadable (if not running as root)
        if os.geteuid() != 0:
            os.chmod(tmp_path, 0o000)
            try:
                with pytest.raises(IOError):
                    generate_checksum(tmp_path)
            finally:
                os.chmod(tmp_path, 0o644)
                os.unlink(tmp_path)
        else:
            os.unlink(tmp_path)


class TestValidateFileExists:
    def test_file_exists(self):
        """Test that True is returned for existing files."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            assert validate_file_exists(tmp_path) is True
        finally:
            os.unlink(tmp_path)

    def test_file_not_exists(self):
        """Test that False is returned for non-existing files."""
        assert validate_file_exists("/nonexistent/path/file.txt") is False

    def test_directory_not_file(self):
        """Test that False is returned for directories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            assert validate_file_exists(tmp_dir) is False


class TestUpdateStateFile:
    def test_update_state_creates_file(self):
        """Test that update_state_file creates the file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_path = Path(tmp_dir) / "state.yaml"
            hash_map = {"file1.txt": "abc123"}
            
            update_state_file(hash_map, str(state_path))
            
            assert state_path.exists()
            
            with open(state_path, "r") as f:
                loaded = yaml.safe_load(f)
            
            assert loaded == hash_map

    def test_update_state_overwrites(self):
        """Test that update_state_file overwrites existing content."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_path = Path(tmp_dir) / "state.yaml"
            
            # Create initial file
            with open(state_path, "w") as f:
                f.write("initial: data")
            
            new_hash_map = {"file2.txt": "def456"}
            update_state_file(new_hash_map, str(state_path))
            
            with open(state_path, "r") as f:
                loaded = yaml.safe_load(f)
            
            assert loaded == new_hash_map
            assert "initial" not in loaded

    def test_update_state_creates_directories(self):
        """Test that update_state_file creates parent directories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_path = Path(tmp_dir) / "subdir1" / "subdir2" / "state.yaml"
            hash_map = {"file.txt": "hash"}
            
            update_state_file(hash_map, str(state_path))
            
            assert state_path.exists()

    def test_update_state_sorts_keys(self):
        """Test that the output YAML has sorted keys."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_path = Path(tmp_dir) / "state.yaml"
            # Unsorted keys
            hash_map = {"z_file.txt": "z", "a_file.txt": "a"}
            
            update_state_file(hash_map, str(state_path))
            
            with open(state_path, "r") as f:
                content = f.read()
            
            # Check that 'a_file' appears before 'z_file'
            assert content.index("a_file") < content.index("z_file")