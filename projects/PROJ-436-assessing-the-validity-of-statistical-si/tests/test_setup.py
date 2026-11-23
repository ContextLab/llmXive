"""
Tests for the project setup script.
Verifies that the directory structure is created correctly.
"""
import os
import tempfile
import shutil
import pytest
import sys

# Add the code directory to the path to allow importing setup_project
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from code import setup_project

class TestSetupProject:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        original_cwd = os.getcwd()
        os.chdir(temp_path)
        yield temp_path
        os.chdir(original_cwd)
        shutil.rmtree(temp_path)

    def test_create_directories_creates_all_dirs(self, temp_dir):
        """Test that create_directories creates the expected folders."""
        expected_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/figures",
            "tests/unit",
            "tests/integration",
            "specs",
            "docs",
        ]

        created = setup_project.create_directories()

        # Check that all expected directories exist
        for dir_path in expected_dirs:
            assert os.path.isdir(dir_path), f"Directory {dir_path} was not created"

        # Check that the function returned the created list
        assert len(created) == len(expected_dirs)

    def test_create_init_files_creates_packages(self, temp_dir):
        """Test that create_init_files creates __init__.py files."""
        setup_project.create_directories()
        setup_project.create_init_files()

        init_files = [
            "code/__init__.py",
            "tests/__init__.py",
            "tests/unit/__init__.py",
            "tests/integration/__init__.py",
        ]

        for file_path in init_files:
            assert os.path.isfile(file_path), f"File {file_path} was not created"
            with open(file_path, "r") as f:
                content = f.read()
                # The file should not be empty (we wrote a comment)
                assert len(content) > 0, f"File {file_path} is empty"

    def test_main_executes_successfully(self, temp_dir):
        """Test that the main function runs without error."""
        # This should not raise any exceptions
        setup_project.main()

        # Verify structure exists after main
        assert os.path.isdir("code")
        assert os.path.isdir("data/raw")
        assert os.path.isfile("code/__init__.py")