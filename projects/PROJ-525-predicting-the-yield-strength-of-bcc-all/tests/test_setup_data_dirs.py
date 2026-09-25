import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_data_dirs import create_gitkeep, setup_data_directories, generate_checksums, verify_checksums
from config import set_base_path, get_base_path, ensure_dirs

class TestSetupDataDirs:
    @pytest.fixture(autouse=True)
    def setup_temp_base(self, tmp_path):
        """Setup a temporary base path for each test."""
        self.original_base = get_base_path()
        set_base_path(tmp_path)
        yield tmp_path
        # Restore original base path after test
        set_base_path(self.original_base)
        # Cleanup is handled by tmp_path fixture

    def test_setup_data_directories_creates_structure(self, setup_temp_base):
        """Test that setup_data_directories creates all required folders."""
        setup_data_directories()
        
        base = get_base_path()
        required_dirs = [
            base / "data" / "raw",
            base / "data" / "processed",
            base / "data" / "logs",
            base / "code",
            base / "tests",
            base / "reports",
            base / "state",
        ]

        for dir_path in required_dirs:
            assert dir_path.exists(), f"Directory {dir_path} was not created."
            assert dir_path.is_dir(), f"{dir_path} is not a directory."

    def test_gitkeep_created_in_data_subdirs(self, setup_temp_base):
        """Test that .gitkeep files are created in data subdirectories."""
        setup_data_directories()
        
        base = get_base_path()
        data_subdirs = [
            base / "data" / "raw",
            base / "data" / "processed",
            base / "data" / "logs",
        ]

        for dir_path in data_subdirs:
            gitkeep = dir_path / ".gitkeep"
            assert gitkeep.exists(), f".gitkeep not found in {dir_path}"
            assert gitkeep.is_file(), f".gitkeep in {dir_path} is not a file."

    def test_create_gitkeep_idempotent(self, setup_temp_base):
        """Test that create_gitkeep does not fail if file already exists."""
        test_dir = setup_temp_base / "test_dir"
        ensure_dirs(test_dir)
        
        create_gitkeep(test_dir)
        create_gitkeep(test_dir)  # Should not raise
        
        assert (test_dir / ".gitkeep").exists()

    def test_generate_and_verify_checksums(self, setup_temp_base):
        """Test checksum generation and verification."""
        setup_data_directories()
        
        # Create a test file
        test_file = get_base_path() / "data" / "raw" / "test.txt"
        test_file.write_text("test content")
        
        checksum_file = get_base_path() / "data" / ".checksums.json"
        
        # Generate checksums
        generate_checksums(checksum_file)
        assert checksum_file.exists()
        
        with open(checksum_file) as f:
            data = json.load(f)
        assert "test.txt" in data["raw"]
        
        # Verify checksums
        assert verify_checksums(checksum_file) is True
        
        # Corrupt file and verify failure
        test_file.write_text("corrupted content")
        assert verify_checksums(checksum_file) is False

    def test_verify_missing_file(self, setup_temp_base):
        """Test verification fails if a tracked file is missing."""
        setup_data_directories()
        
        # Create a test file and generate checksum
        test_file = get_base_path() / "data" / "raw" / "test.txt"
        test_file.write_text("content")
        checksum_file = get_base_path() / "data" / ".checksums.json"
        generate_checksums(checksum_file)
        
        # Remove file
        test_file.unlink()
        
        # Verification should fail
        assert verify_checksums(checksum_file) is False
