"""
Tests for T001d: Verify that the checksumming script executes correctly
and produces the expected output file in state/.
"""
import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path
import sys

# Add code directory to path for imports if running as standalone
# This assumes the test is run with the project root as the working directory
# or PYTHONPATH is set correctly.
code_root = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from data_checksum_manager import record_checksums, save_checksums, load_checksums, verify_integrity

class TestChecksumExecution:
    """Tests for the checksum generation and storage logic."""

    @pytest.fixture
    def temp_project_structure(self, tmp_path: Path):
        """Create a temporary directory structure mimicking the project layout."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Create some dummy files
        (data_dir / "file1.txt").write_text("content1")
        (data_dir / "file2.json").write_text('{"key": "value"}')
        
        subdir = data_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested content")
        
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        
        return {
            "root": tmp_path,
            "data": data_dir,
            "state": state_dir
        }

    def test_record_checksums_finds_files(self, temp_project_structure):
        """Verify that record_checksums finds all files recursively."""
        checksums = record_checksums(temp_project_structure["data"])
        
        assert len(checksums) == 3
        assert "file1.txt" in checksums
        assert "file2.json" in checksums
        assert "subdir/nested.txt" in checksums

    def test_save_and_load_checksums(self, temp_project_structure):
        """Verify that checksums can be saved to JSON and loaded back."""
        checksums = record_checksums(temp_project_structure["data"])
        output_path = temp_project_structure["state"] / "test_checksums.json"
        
        save_checksums(checksums, output_path)
        
        assert output_path.exists()
        
        loaded = load_checksums(output_path)
        assert loaded == checksums

    def test_verify_integrity_pass(self, temp_project_structure):
        """Verify that integrity check passes when files match checksums."""
        checksums = record_checksums(temp_project_structure["data"])
        is_valid = verify_integrity(checksums, temp_project_structure["data"])
        assert is_valid is True

    def test_verify_integrity_fail_modified(self, temp_project_structure):
        """Verify that integrity check fails if a file is modified."""
        checksums = record_checksums(temp_project_structure["data"])
        
        # Modify a file
        (temp_project_structure["data"] / "file1.txt").write_text("modified content")
        
        is_valid = verify_integrity(checksums, temp_project_structure["data"])
        assert is_valid is False

    def test_verify_integrity_fail_deleted(self, temp_project_structure):
        """Verify that integrity check fails if a file is deleted."""
        checksums = record_checksums(temp_project_structure["data"])
        
        # Delete a file
        (temp_project_structure["data"] / "file1.txt").unlink()
        
        is_valid = verify_integrity(checksums, temp_project_structure["data"])
        assert is_valid is False

    def test_empty_directory_checksum(self, tmp_path: Path):
        """Verify behavior with an empty data directory."""
        data_dir = tmp_path / "empty_data"
        data_dir.mkdir()
        
        checksums = record_checksums(data_dir)
        assert checksums == {}
        
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        output_path = state_dir / "empty.json"
        
        save_checksums(checksums, output_path)
        assert output_path.exists()
        
        loaded = load_checksums(output_path)
        assert loaded == {}