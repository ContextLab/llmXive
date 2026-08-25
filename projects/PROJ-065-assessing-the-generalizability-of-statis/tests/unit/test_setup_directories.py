import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add code to path if not already present
code_path = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from setup_directories import (
    ensure_directory_structure,
    calculate_file_hash,
    calculate_directory_hash,
    DATA_RAW,
    DATA_PROCESSED,
    OUTPUTS_FIGURES,
    OUTPUTS_REPORTS
)

class TestDirectoryCreation:
    def test_ensure_directory_structure_creates_all_dirs(self, tmp_path, monkeypatch):
        """Test that all required directories are created."""
        # Monkeypatch the global constants to use tmp_path
        # We need to re-import or patch the module's global variables
        import setup_directories
        
        # Override the project root for this test
        original_root = setup_directories.PROJECT_ROOT
        setup_directories.PROJECT_ROOT = tmp_path
        
        # Re-evaluate paths based on new root
        setup_directories.DATA_RAW = tmp_path / "data" / "raw"
        setup_directories.DATA_PROCESSED = tmp_path / "data" / "processed"
        setup_directories.OUTPUTS = tmp_path / "outputs"
        setup_directories.OUTPUTS_FIGURES = setup_directories.OUTPUTS / "figures"
        setup_directories.OUTPUTS_REPORTS = setup_directories.OUTPUTS / "reports"
        setup_directories.STATE_DIR = tmp_path / "state"
        
        try:
            ensure_directory_structure()
            
            assert setup_directories.DATA_RAW.exists()
            assert setup_directories.DATA_PROCESSED.exists()
            assert setup_directories.OUTPUTS_FIGURES.exists()
            assert setup_directories.OUTPUTS_REPORTS.exists()
            assert (setup_directories.DATA_RAW / ".gitkeep").exists()
            assert (setup_directories.DATA_PROCESSED / ".gitkeep").exists()
        finally:
            setup_directories.PROJECT_ROOT = original_root

class TestFileHashing:
    def test_calculate_file_hash_sha256(self, tmp_path):
        """Test SHA256 hash calculation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        # Expected SHA256 for "Hello, World!"
        # dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        
        result = calculate_file_hash(test_file)
        assert result == expected_hash

    def test_calculate_file_hash_nonexistent(self, tmp_path):
        """Test hash calculation for non-existent file."""
        result = calculate_file_hash(tmp_path / "nonexistent.txt")
        assert result is None

class TestDirectoryHashing:
    def test_calculate_directory_hash_empty(self, tmp_path):
        """Test hash of an empty directory (with .gitkeep)."""
        # create .gitkeep
        (tmp_path / ".gitkeep").touch()
        
        # The function ignores .gitkeep, so it should hash as empty
        # But since we don't have any files, the hash should be deterministic for empty content
        hash1 = calculate_directory_hash(tmp_path)
        hash2 = calculate_directory_hash(tmp_path)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_calculate_directory_hash_content_change(self, tmp_path):
        """Test that directory hash changes when file content changes."""
        test_file = tmp_path / "data.txt"
        test_file.write_text("Content A")
        
        hash_a = calculate_directory_hash(tmp_path)
        
        test_file.write_text("Content B")
        hash_b = calculate_directory_hash(tmp_path)
        
        assert hash_a != hash_b

    def test_calculate_directory_hash_structure_change(self, tmp_path):
        """Test that directory hash changes when file is added."""
        test_file = tmp_path / "data.txt"
        test_file.write_text("Content")
        
        hash_a = calculate_directory_hash(tmp_path)
        
        new_file = tmp_path / "new_data.txt"
        new_file.write_text("New Content")
        
        hash_b = calculate_directory_hash(tmp_path)
        
        assert hash_a != hash_b
