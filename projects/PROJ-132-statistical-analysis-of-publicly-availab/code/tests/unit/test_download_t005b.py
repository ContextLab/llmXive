"""
Unit tests for T005b: Download and Verify eBird Sample Data.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.data.download_t005b import compute_sha256, verify_checksums, archive_data


class TestDownloadT005b:
    """Test suite for T005b download and verification functions."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        temp_root = tempfile.mkdtemp()
        temp_data = Path(temp_root) / "data"
        temp_archive = Path(temp_root) / "archive"
        temp_data.mkdir()
        temp_archive.mkdir()
        
        # Create a dummy file
        dummy_file = temp_data / "test_file.txt"
        dummy_file.write_text("Hello, World!")
        
        yield {
            "root": Path(temp_root),
            "data": temp_data,
            "archive": temp_archive,
            "dummy_file": dummy_file
        }
        
        # Cleanup
        shutil.rmtree(temp_root)

    def test_compute_sha256_basic(self, temp_dirs):
        """Test basic SHA-256 computation."""
        checksum = compute_sha256(temp_dirs["dummy_file"])
        assert len(checksum) == 64  # SHA-256 hex string length
        assert all(c in '0123456789abcdef' for c in checksum)

    def test_compute_sha256_file_not_found(self, temp_dirs):
        """Test SHA-256 computation on non-existent file."""
        non_existent = temp_dirs["data"] / "non_existent.txt"
        with pytest.raises(FileNotFoundError):
            compute_sha256(non_existent)

    def test_verify_checksums(self, temp_dirs):
        """Test checksum verification."""
        file_paths = [temp_dirs["dummy_file"]]
        checksums = verify_checksums(file_paths)
        
        assert len(checksums) == 1
        assert "test_file.txt" in checksums
        assert len(checksums["test_file.txt"]) == 64

    def test_archive_data_basic(self, temp_dirs):
        """Test basic archiving functionality."""
        archived_files = archive_data([temp_dirs["dummy_file"]], temp_dirs["archive"])
        
        assert len(archived_files) == 1
        assert archived_files[0].exists()
        assert archived_files[0].name == "test_file.txt"
        
        # Verify content matches
        original_content = temp_dirs["dummy_file"].read_text()
        archived_content = archived_files[0].read_text()
        assert original_content == archived_content

    def test_archive_data_overwrite_false(self, temp_dirs):
        """Test archiving when overwrite is not explicitly handled (shutil.copy2 by default)."""
        # First archive
        archive_data([temp_dirs["dummy_file"]], temp_dirs["archive"])
        
        # Modify original
        temp_dirs["dummy_file"].write_text("Modified content")
        
        # Archive again
        archived_files = archive_data([temp_dirs["dummy_file"]], temp_dirs["archive"])
        
        # Should reflect the modification
        archived_content = archived_files[0].read_text()
        assert archived_content == "Modified content"

    def test_archive_data_empty_source(self, temp_dirs):
        """Test archiving with empty source list."""
        archived_files = archive_data([], temp_dirs["archive"])
        assert len(archived_files) == 0

    def test_archive_data_source_not_found(self, temp_dirs):
        """Test archiving with non-existent source file."""
        non_existent = temp_dirs["data"] / "non_existent.txt"
        with pytest.raises(FileNotFoundError):
            archive_data([non_existent], temp_dirs["archive"])