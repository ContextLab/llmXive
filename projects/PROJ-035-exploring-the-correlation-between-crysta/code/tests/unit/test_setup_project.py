import os
import tempfile
import pytest
from pathlib import Path
from setup_project import setup_project_structure

class TestSetupProject:
    def test_directory_creation(self):
        """Test that the setup function creates the required directories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_dir)
                result = setup_project_structure()
                assert result is True

                # Verify critical directories exist
                required_dirs = [
                    "src",
                    "tests",
                    "data/raw",
                    "data/cleaned",
                    "data/results",
                    "figures",
                    "contracts"
                ]

                for dir_name in required_dirs:
                    dir_path = Path(tmp_dir) / dir_name
                    assert dir_path.exists(), f"Directory {dir_name} was not created"
                    assert dir_path.is_dir(), f"{dir_name} is not a directory"

            finally:
                os.chdir(original_cwd)

    def test_package_initialization(self):
        """Test that __init__.py files are created for packages."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_dir)
                setup_project_structure()

                # Verify __init__.py files exist in key packages
                init_files = [
                    "src/__init__.py",
                    "tests/__init__.py",
                    "src/ingest/__init__.py",
                    "src/cleaning/__init__.py",
                    "src/analysis/__init__.py"
                ]

                for init_file in init_files:
                    file_path = Path(tmp_dir) / init_file
                    assert file_path.exists(), f"Init file {init_file} was not created"
                    assert file_path.is_file(), f"{init_file} is not a file"

            finally:
                os.chdir(original_cwd)