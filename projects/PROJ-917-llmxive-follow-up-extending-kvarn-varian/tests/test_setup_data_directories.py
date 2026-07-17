import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the module under test
# Assuming the test runner adds code/ to sys.path or we import relative to project root
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.setup_data_directories import (
    create_directories,
    compute_file_checksum,
    record_checksum,
    verify_integrity,
    DIRECTORY_STRUCTURE
)

class TestDataDirectorySetup:
    @pytest.fixture
    def temp_data_root(self):
        """Create a temporary directory to act as the data root."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_create_directories_structure(self, temp_data_root):
        """Test that the full directory tree is created correctly."""
        paths = create_directories(temp_data_root)
        
        # Check top-level directories exist
        for dir_name in DIRECTORY_STRUCTURE.keys():
            assert (temp_data_root / dir_name).exists()
            assert (temp_data_root / dir_name).is_dir()
        
        # Check sub-directories exist
        for dir_name, sub_dirs in DIRECTORY_STRUCTURE.items():
            for sub_dir in sub_dirs:
                sub_path = temp_data_root / dir_name / sub_dir
                assert sub_path.exists()
                assert sub_path.is_dir()

    def test_compute_file_checksum(self, temp_data_root):
        """Test SHA-256 checksum computation."""
        test_file = temp_data_root / "test_file.txt"
        content = "Hello, World!"
        test_file.write_text(content)
        
        checksum = compute_file_checksum(test_file)
        
        # Verify length of SHA-256 hex string
        assert len(checksum) == 64
        # Verify it's a valid hex string
        int(checksum, 16)

    def test_record_and_verify_checksum(self, temp_data_root):
        """Test the full cycle of recording and verifying checksums."""
        test_file = temp_data_root / "immutable_data.json"
        test_file.write_text(json.dumps({"key": "value"}))
        
        # Record checksum
        record_checksum(test_file)
        
        # Manifest should exist
        manifest_path = test_file.with_suffix(test_file.suffix + ".checksum.json")
        assert manifest_path.exists()
        
        # Verify integrity
        assert verify_integrity(test_file) is True

    def test_verify_integrity_fails_on_modification(self, temp_data_root):
        """Test that verification fails if file content changes."""
        test_file = temp_data_root / "mutable_data.txt"
        test_file.write_text("Original Content")
        
        record_checksum(test_file)
        
        # Modify file
        test_file.write_text("Modified Content")
        
        # Verification should fail
        assert verify_integrity(test_file) is False

    def test_verify_integrity_missing_manifest(self, temp_data_root):
        """Test behavior when checksum manifest is missing."""
        test_file = temp_data_root / "no_manifest.txt"
        test_file.write_text("Content")
        
        # Should return False without raising an exception
        assert verify_integrity(test_file) is False

    def test_record_checksum_missing_file_raises(self, temp_data_root):
        """Test that recording checksum for non-existent file raises error."""
        fake_file = temp_data_root / "does_not_exist.txt"
        
        with pytest.raises(FileNotFoundError):
            record_checksum(fake_file)