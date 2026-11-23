"""
Unit tests for setup_data_dirs module.
Tests directory creation, .gitkeep generation, and checksum functionality.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from setup_data_dirs import create_gitkeep, setup_data_directories, generate_checksums, verify_checksums
from config import compute_file_checksum

class TestCreateGitkeep:
    """Tests for create_gitkeep function."""
    
    def test_creates_gitkeep_if_not_exists(self, tmp_path):
        """Test that .gitkeep is created when it doesn't exist."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        gitkeep_path = test_dir / ".gitkeep"
        assert not gitkeep_path.exists()
        
        create_gitkeep(test_dir)
        
        assert gitkeep_path.exists()
        content = gitkeep_path.read_text()
        assert "# Keep this directory under version control" in content
        
        # Verify it didn't overwrite if it already existed
        original_content = content
        create_gitkeep(test_dir)
        assert gitkeep_path.read_text() == original_content

    def test_does_not_create_if_exists(self, tmp_path):
        """Test that .gitkeep is not modified if it already exists."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        gitkeep_path = test_dir / ".gitkeep"
        gitkeep_path.write_text("existing content")
        
        create_gitkeep(test_dir)
        
        assert gitkeep_path.read_text() == "existing content"

class TestSetupDataDirectories:
    """Tests for setup_data_directories function."""
    
    def test_creates_all_required_directories(self, tmp_path):
        """Test that all required data directories are created."""
        result = setup_data_directories(tmp_path)
        
        assert "raw" in result
        assert "processed" in result
        assert "logs" in result
        
        raw_path = result["raw"]
        processed_path = result["processed"]
        logs_path = result["logs"]
        
        assert raw_path.exists()
        assert processed_path.exists()
        assert logs_path.exists()
        
        # Verify .gitkeep files exist
        assert (raw_path / ".gitkeep").exists()
        assert (processed_path / ".gitkeep").exists()
        assert (logs_path / ".gitkeep").exists()

    def test_returns_correct_paths(self, tmp_path):
        """Test that returned paths are correct."""
        result = setup_data_directories(tmp_path)
        
        assert result["raw"] == tmp_path / "data" / "raw"
        assert result["processed"] == tmp_path / "data" / "processed"
        assert result["logs"] == tmp_path / "data" / "logs"

class TestGenerateChecksums:
    """Tests for generate_checksums function."""
    
    def test_generates_checksums_for_existing_files(self, tmp_path):
        """Test that checksums are generated for existing files."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Create test files
        (data_dir / "file1.txt").write_text("content1")
        (data_dir / "file2.txt").write_text("content2")
        
        # Create subdirectory with file
        subdir = data_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")
        
        checksums = generate_checksums(data_dir)
        
        assert len(checksums) == 3
        assert "file1.txt" in checksums
        assert "file2.txt" in checksums
        assert "subdir/file3.txt" in checksums
        
        # Verify checksums are valid SHA-256 hashes
        for checksum in checksums.values():
            assert len(checksum) == 64  # SHA-256 hex length
            assert all(c in '0123456789abcdef' for c in checksum)
    
    def test_excludes_gitkeep_files(self, tmp_path):
        """Test that .gitkeep files are excluded from checksums."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        (data_dir / ".gitkeep").write_text("# keep")
        (data_dir / "file1.txt").write_text("content")
        
        checksums = generate_checksums(data_dir)
        
        assert len(checksums) == 1
        assert ".gitkeep" not in checksums
        assert "file1.txt" in checksums

class TestVerifyChecksums:
    """Tests for verify_checksums function."""
    
    def test_verifies_valid_checksums(self, tmp_path):
        """Test verification of valid checksums."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Create a file
        test_file = data_dir / "test.txt"
        test_file.write_text("test content")
        
        # Generate checksum
        checksum = compute_file_checksum(test_file)
        checksums_file = data_dir / "checksums.json"
        
        import json
        with open(checksums_file, 'w') as f:
            json.dump({"test.txt": checksum}, f)
        
        # Verify
        result = verify_checksums(data_dir, checksums_file)
        assert result is True

    def test_fails_on_modified_files(self, tmp_path):
        """Test that verification fails when files are modified."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Create a file
        test_file = data_dir / "test.txt"
        test_file.write_text("test content")
        
        # Generate checksum
        checksum = compute_file_checksum(test_file)
        checksums_file = data_dir / "checksums.json"
        
        import json
        with open(checksums_file, 'w') as f:
            json.dump({"test.txt": checksum}, f)
        
        # Modify file
        test_file.write_text("modified content")
        
        # Verify should fail
        result = verify_checksums(data_dir, checksums_file)
        assert result is False

    def test_handles_missing_checksum_file(self, tmp_path):
        """Test handling of missing checksum file."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        checksums_file = data_dir / "missing.json"
        
        result = verify_checksums(data_dir, checksums_file)
        assert result is False

# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
