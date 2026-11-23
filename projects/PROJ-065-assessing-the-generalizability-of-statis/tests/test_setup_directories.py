"""
Tests for the setup_directories module.
Verifies that directory creation and file initialization work correctly.
"""
import os
import pytest
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from setup_directories import (
    ensure_directory_structure,
    create_initial_files,
    calculate_directory_hash,
    PROJECT_PATH,
    DIRECTORIES_TO_CREATE
)

class TestDirectoryCreation:
    def test_directories_exist_after_ensure(self, tmp_path, monkeypatch):
        """Test that ensure_directory_structure creates all required directories."""
        # Use a temporary path for testing to avoid polluting the real project
        monkeypatch.setattr('setup_directories.PROJECT_PATH', tmp_path / "PROJ-065-assessing-the-generalizability-of-statis")
        
        ensure_directory_structure()
        
        for dir_name in DIRECTORIES_TO_CREATE:
            dir_path = tmp_path / "PROJ-065-assessing-the-generalizability-of-statis" / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"
            # Check for .gitkeep
            gitkeep = dir_path / ".gitkeep"
            assert gitkeep.exists(), f".gitkeep not created in {dir_name}"

    def test_idempotency(self, tmp_path, monkeypatch):
        """Test that running ensure_directory_structure multiple times doesn't fail."""
        monkeypatch.setattr('setup_directories.PROJECT_PATH', tmp_path / "PROJ-065-assessing-the-generalizability-of-statis")
        
        # Run twice
        ensure_directory_structure()
        ensure_directory_structure()
        
        # Verify directories still exist
        for dir_name in DIRECTORIES_TO_CREATE:
            dir_path = tmp_path / "PROJ-065-assessing-the-generalizability-of-statis" / dir_name
            assert dir_path.exists()

class TestFileCreation:
    def test_requirements_txt_created(self, tmp_path, monkeypatch):
        """Test that requirements.txt is created with content."""
        monkeypatch.setattr('setup_directories.PROJECT_PATH', tmp_path / "PROJ-065-assessing-the-generalizability-of-statis")
        
        ensure_directory_structure()
        create_initial_files()
        
        req_path = tmp_path / "PROJ-065-assessing-the-generalizability-of-statis" / "requirements.txt"
        assert req_path.exists()
        content = req_path.read_text()
        assert "requests" in content
        assert "pandas" in content

    def test_readme_md_created(self, tmp_path, monkeypatch):
        """Test that README.md is created with content."""
        monkeypatch.setattr('setup_directories.PROJECT_PATH', tmp_path / "PROJ-065-assessing-the-generalizability-of-statis")
        
        ensure_directory_structure()
        create_initial_files()
        
        readme_path = tmp_path / "PROJ-065-assessing-the-generalizability-of-statis" / "README.md"
        assert readme_path.exists()
        content = readme_path.read_text()
        assert "PROJ-065-assessing-the-generalizability-of-statis" in content

class TestHashCalculation:
    def test_hash_of_empty_directory(self, tmp_path, monkeypatch):
        """Test hash calculation on an empty directory."""
        test_dir = tmp_path / "test_empty"
        test_dir.mkdir()
        
        hash_val = calculate_directory_hash(str(test_dir))
        assert hash_val is not None
        # Hash should be consistent
        assert hash_val == calculate_directory_hash(str(test_dir))

    def test_hash_of_directory_with_file(self, tmp_path, monkeypatch):
        """Test hash calculation changes when file is added."""
        test_dir = tmp_path / "test_with_file"
        test_dir.mkdir()
        
        # Get initial hash
        hash1 = calculate_directory_hash(str(test_dir))
        
        # Add a file
        (test_dir / "test.txt").write_text("hello")
        
        # Get new hash
        hash2 = calculate_directory_hash(str(test_dir))
        
        assert hash1 != hash2, "Hash should change when file is added"

    def test_nonexistent_directory_returns_none(self, tmp_path):
        """Test that hash calculation returns None for non-existent directory."""
        result = calculate_directory_hash(str(tmp_path / "nonexistent"))
        assert result is None
