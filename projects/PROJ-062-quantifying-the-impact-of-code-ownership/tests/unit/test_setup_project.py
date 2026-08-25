import os
import pytest
from pathlib import Path
import sys
import shutil

# Add the project root to the path so we can import the script
# Assuming tests are run from the repository root
project_root = Path(__file__).resolve().parent.parent.parent
scripts_dir = project_root / "code" / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from setup_project import create_structure

class TestProjectStructure:
    """
    Tests for T001: Create project structure per implementation plan.
    Verifies that the required directory structure is created correctly.
    """

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmp_path):
        """
        Set up a temporary directory structure to simulate the project root,
        and clean up after the test.
        """
        self.original_cwd = os.getcwd()
        # Change to the temporary directory to simulate running from repo root
        os.chdir(tmp_path)
        yield
        # Restore original directory and clean up
        os.chdir(self.original_cwd)

    def test_project_root_created(self):
        """Verify the main project root directory is created."""
        create_structure()
        project_root = Path("projects/PROJ-062-quantifying-the-impact-of-code-ownership")
        assert project_root.exists(), "Project root directory was not created"
        assert project_root.is_dir(), "Project root is not a directory"

    def test_code_directories_created(self):
        """Verify code source directories are created."""
        create_structure()
        project_root = Path("projects/PROJ-062-quantifying-the-impact-of-code-ownership")
        
        expected_dirs = [
            "code",
            "code/utils",
            "code/scripts"
        ]
        
        for dir_path in expected_dirs:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} is not a directory"

    def test_tests_directories_created(self):
        """Verify test directories are created."""
        create_structure()
        project_root = Path("projects/PROJ-062-quantifying-the-impact-of-code-ownership")
        
        expected_dirs = [
            "tests",
            "tests/unit",
            "tests/integration",
            "tests/contract"
        ]
        
        for dir_path in expected_dirs:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} is not a directory"

    def test_data_directories_created(self):
        """Verify data directories are created."""
        create_structure()
        project_root = Path("projects/PROJ-062-quantifying-the-impact-of-code-ownership")
        
        expected_dirs = [
            "data",
            "data/raw",
            "data/intermediate",
            "data/results",
            "data/ownership_metrics"
        ]
        
        for dir_path in expected_dirs:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} is not a directory"

    def test_init_files_created(self):
        """Verify __init__.py files are created in Python package directories."""
        create_structure()
        project_root = Path("projects/PROJ-062-quantifying-the-impact-of-code-ownership")
        
        expected_init_files = [
            "code/__init__.py",
            "code/utils/__init__.py",
            "code/scripts/__init__.py",
            "tests/__init__.py",
            "tests/unit/__init__.py",
            "tests/integration/__init__.py",
            "tests/contract/__init__.py"
        ]
        
        for file_path in expected_init_files:
            full_path = project_root / file_path
            assert full_path.exists(), f"Init file {file_path} was not created"
            assert full_path.is_file(), f"{file_path} is not a file"

    def test_other_directories_created(self):
        """Verify other required directories (state, specs, docs, figures) are created."""
        create_structure()
        project_root = Path("projects/PROJ-062-quantifying-the-impact-of-code-ownership")
        
        expected_dirs = [
            "state",
            "specs",
            "docs",
            "figures"
        ]
        
        for dir_path in expected_dirs:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} is not a directory"
