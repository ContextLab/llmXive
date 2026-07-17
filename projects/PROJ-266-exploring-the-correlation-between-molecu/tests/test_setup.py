import os
import sys
from pathlib import Path
import pytest

# Add the project root to the path if running tests directly
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from code.setup_project_structure import create_directory_structure
from code.data.setup_directories import compute_file_checksum, generate_checksum_manifest


class TestProjectStructure:
    """Tests for the project directory structure creation."""

    def test_directory_structure_creation(self, tmp_path):
        """Test that all required directories are created."""
        # Change to temp directory to simulate project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Create the structure
            created_dirs = create_directory_structure()
            
            # Verify expected directories exist
            expected_dirs = [
                "code",
                "code/utils",
                "code/data",
                "tests",
                "tests/contract",
                "data",
                "data/raw",
                "data/processed",
                "data/interim",
                "figures",
                "state",
                "state/projects",
                "specs",
            ]
            
            for dir_name in expected_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"
                
        finally:
            os.chdir(original_cwd)

    def test_idempotency(self, tmp_path):
        """Test that running the creation twice doesn't fail."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run twice
            create_directory_structure()
            create_directory_structure()
            
            # Should still exist
            assert (tmp_path / "code").exists()
            assert (tmp_path / "data").exists()
            
        finally:
            os.chdir(original_cwd)


class TestChecksumUtilities:
    """Tests for checksum utilities."""

    def test_compute_file_checksum(self, tmp_path):
        """Test checksum computation for a file."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        checksum = compute_file_checksum(test_file)
        
        # Verify it's a valid hex string of correct length for sha256
        assert len(checksum) == 64
        assert all(c in "0123456789abcdef" for c in checksum)
        
        # Verify consistency
        checksum2 = compute_file_checksum(test_file)
        assert checksum == checksum2

    def test_compute_file_checksum_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing files."""
        missing_file = tmp_path / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(missing_file)

    def test_generate_checksum_manifest(self, tmp_path):
        """Test manifest generation."""
        # Create some test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.txt").write_text("content3")
        
        output_path = tmp_path / "manifest.json"
        manifest = generate_checksum_manifest(tmp_path, output_path)
        
        # Verify manifest content
        assert len(manifest) == 3
        assert "file1.txt" in manifest
        assert "file2.txt" in manifest
        assert "subdir/file3.txt" in manifest
        
        # Verify file was written
        assert output_path.exists()
        
        # Verify JSON content
        import json
        with open(output_path, "r") as f:
            loaded_manifest = json.load(f)
        assert loaded_manifest == manifest

    def test_generate_checksum_manifest_with_filter(self, tmp_path):
        """Test manifest generation with extension filter."""
        # Create files with different extensions
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.csv").write_text("content2")
        (tmp_path / "file3.csv").write_text("content3")
        
        output_path = tmp_path / "manifest.json"
        manifest = generate_checksum_manifest(
            tmp_path, 
            output_path, 
            extensions=[".csv"]
        )
        
        # Should only include .csv files
        assert len(manifest) == 2
        assert "file1.txt" not in manifest
        assert "file2.csv" in manifest
        assert "file3.csv" in manifest
