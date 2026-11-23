"""
Tests for project structure setup utilities.
"""
import os
import tempfile
import pytest
from code.setup_project_structure import create_directory_structure, create_gitkeep_files


class TestCreateDirectoryStructure:
    def test_creates_required_directories(self):
        """Test that all required directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            created = create_directory_structure(tmpdir)
            
            # Check that all expected directories were created
            expected_dirs = [
                "code",
                "data",
                "data/raw",
                "data/generated",
                "data/results",
                "tests",
                "tests/unit",
                "tests/integration",
                "scripts",
                "figures",
            ]
            
            for dir_name in expected_dirs:
                full_path = os.path.join(tmpdir, dir_name)
                assert os.path.isdir(full_path), f"Directory {dir_name} was not created"
            
            # Verify returned list contains the created paths
            assert len(created) == len(expected_dirs)
            for expected in expected_dirs:
                assert os.path.join(tmpdir, expected) in created

    def test_skips_existing_directories(self):
        """Test that existing directories are not recreated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Pre-create some directories
            os.makedirs(os.path.join(tmpdir, "code"))
            os.makedirs(os.path.join(tmpdir, "data"))
            
            created = create_directory_structure(tmpdir)
            
            # Should only create the missing directories
            assert len(created) == len([d for d in [
                "data/raw", "data/generated", "data/results",
                "tests", "tests/unit", "tests/integration",
                "scripts", "figures"
            ]])
            assert "code" not in created
            assert "data" not in created

    def test_uses_current_directory_when_no_base_path(self):
        """Test that current directory is used when base_path is None."""
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                os.chdir(tmpdir)
                created = create_directory_structure()
                
                assert os.path.isdir(os.path.join(tmpdir, "code"))
                assert os.path.isdir(os.path.join(tmpdir, "data"))
            finally:
                os.chdir(original_cwd)


class TestCreateGitkeepFiles:
    def test_creates_gitkeep_in_data_subdirectories(self):
        """Test that .gitkeep files are created in all data subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # First create the directory structure
            create_directory_structure(tmpdir)
            
            created = create_gitkeep_files(tmpdir)
            
            expected_files = [
                os.path.join(tmpdir, "data/raw", ".gitkeep"),
                os.path.join(tmpdir, "data/generated", ".gitkeep"),
                os.path.join(tmpdir, "data/results", ".gitkeep"),
            ]
            
            assert len(created) == 3
            for expected in expected_files:
                assert os.path.isfile(expected), f"File {expected} was not created"
            
            # Verify content
            for gitkeep in expected_files:
                with open(gitkeep, 'r') as f:
                    content = f.read()
                    assert "# Keep this directory in git" in content

    def test_skips_existing_gitkeep_files(self):
        """Test that existing .gitkeep files are not recreated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directory structure
            create_directory_structure(tmpdir)
            
            # Pre-create one .gitkeep file
            existing_gitkeep = os.path.join(tmpdir, "data/raw", ".gitkeep")
            with open(existing_gitkeep, 'w') as f:
                f.write("existing content")
            
            created = create_gitkeep_files(tmpdir)
            
            # Should only create the missing .gitkeep files
            assert len(created) == 2
            assert existing_gitkeep not in created

    def test_creates_directories_if_missing(self):
        """Test that directories are created if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Don't create directory structure first
            created = create_gitkeep_files(tmpdir)
            
            # Should create directories and .gitkeep files
            assert len(created) == 3
            assert os.path.isdir(os.path.join(tmpdir, "data/raw"))
            assert os.path.isdir(os.path.join(tmpdir, "data/generated"))
            assert os.path.isdir(os.path.join(tmpdir, "data/results"))