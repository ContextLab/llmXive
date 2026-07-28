"""
Unit tests for the checksum utility module.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add the project root to the path to allow imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.checksums import (
    compute_file_sha256,
    load_checksums,
    save_checksums,
    update_checksum_for_file,
    verify_file_integrity,
    ChecksumError,
    CHECKSUM_REGISTRY_PATH
)


class TestChecksums:
    """Test suite for checksum utilities."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Use a temporary directory for the data folder during tests
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        # Create a temporary data directory structure
        self.temp_data_path = Path(self.temp_dir) / "data"
        self.temp_data_path.mkdir(parents=True, exist_ok=True)
        
        # Temporarily override the global registry path
        global CHECKSUM_REGISTRY_PATH
        self.original_registry_path = CHECKSUM_REGISTRY_PATH
        CHECKSUM_REGISTRY_PATH = self.temp_data_path / "checksums.json"
        
        os.chdir(self.temp_dir)
        yield

        # Restore original state
        os.chdir(self.original_cwd)
        CHECKSUM_REGISTRY_PATH = self.original_registry_path
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_compute_file_sha256(self):
        """Test that we can compute a SHA-256 hash for a file."""
        test_file = Path(self.temp_dir) / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        hash_result = compute_file_sha256(test_file)
        
        # Verify it's a valid hex string of correct length
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in hash_result)

    def test_compute_file_sha256_file_not_found(self):
        """Test that computing hash for non-existent file raises error."""
        with pytest.raises(ChecksumError, match="File not found"):
            compute_file_sha256(Path("non_existent_file.txt"))

    def test_load_checksums_empty(self):
        """Test loading checksums when registry doesn't exist."""
        # Ensure the file doesn't exist
        if CHECKSUM_REGISTRY_PATH.exists():
            CHECKSUM_REGISTRY_PATH.unlink()

        result = load_checksums()
        assert result == {"files": {}}

    def test_load_checksums_with_data(self):
        """Test loading checksums when registry exists."""
        # Create a mock registry
        mock_data = {"files": {"test.txt": {"hash": "abc123", "algorithm": "sha256"}}}
        with open(CHECKSUM_REGISTRY_PATH, "w") as f:
            json.dump(mock_data, f)

        result = load_checksums()
        assert result == mock_data

    def test_update_checksum_for_file(self):
        """Test updating a checksum for a file."""
        test_file = Path(self.temp_dir) / "update_test.txt"
        test_file.write_text("Test content")

        result = update_checksum_for_file(test_file)

        assert "path" in result
        assert "hash" in result
        assert result["path"].endswith("update_test.txt")
        
        # Verify it's in the registry
        registry = load_checksums()
        assert result["path"] in registry["files"]
        assert registry["files"][result["path"]]["hash"] == result["hash"]

    def test_verify_file_integrity_success(self):
        """Test successful integrity verification."""
        test_file = Path(self.temp_dir) / "verify_test.txt"
        test_file.write_text("Verify me")

        # First, update the checksum
        update_checksum_for_file(test_file)

        # Then verify
        assert verify_file_integrity(test_file) is True

    def test_verify_file_integrity_failure(self):
        """Test integrity verification fails when file is modified."""
        test_file = Path(self.temp_dir) / "modify_test.txt"
        test_file.write_text("Original content")

        # Update checksum
        update_checksum_for_file(test_file)

        # Modify file
        test_file.write_text("Modified content")

        # Verification should fail
        with pytest.raises(ChecksumError, match="Integrity check failed"):
            verify_file_integrity(test_file)

    def test_verify_file_integrity_not_registered(self):
        """Test verification fails for unregistered file."""
        test_file = Path(self.temp_dir) / "unregistered.txt"
        test_file.write_text("I am not registered")

        with pytest.raises(ChecksumError, match="No stored checksum found"):
            verify_file_integrity(test_file)

    def test_save_checksums_creates_directory(self):
        """Test that saving checksums creates the data directory if needed."""
        # Remove the data directory
        if self.temp_data_path.exists():
            import shutil
            shutil.rmtree(self.temp_data_path)

        # Save should create it
        save_checksums({"files": {}})
        
        assert self.temp_data_path.exists()
        assert CHECKSUM_REGISTRY_PATH.exists()