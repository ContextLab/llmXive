import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the code directory to the path so we can import from it
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from create_project_structure import create_project_structure

class TestCreateProjectStructure:
    """
    Unit tests for the project structure creation task T001.
    Verifies that all required directories and __init__.py files are created.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Create a temporary directory for testing and clean up afterwards."""
        self.temp_dir = tempfile.mkdtemp()
        # Change to temp directory to avoid creating files in actual project
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        yield
        
        # Cleanup
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_project_structure_creates_base_dir(self):
        """Test that the base project directory is created."""
        result = create_project_structure()
        base_path = Path("projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code")
        assert base_path.exists(), "Base project directory was not created"
        assert base_path.is_dir(), "Base project path is not a directory"

    def test_create_project_structure_creates_all_directories(self):
        """Test that all required subdirectories are created."""
        result = create_project_structure()
        required_dirs = [
            "src",
            "tests",
            "data",
            "src/generation",
            "src/filtering",
            "src/training",
            "src/evaluation",
            "src/utils",
            "tests/unit",
            "tests/integration",
            "data/raw",
            "data/curated",
            "data/eval",
            "data/validation",
        ]
        
        base_path = Path("projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code")
        for dir_name in required_dirs:
            dir_path = base_path / dir_name
            assert dir_path.exists(), f"Required directory {dir_path} was not created"
            assert dir_path.is_dir(), f"Required path {dir_path} is not a directory"

    def test_create_project_structure_creates_init_files(self):
        """Test that __init__.py files are created for Python packages."""
        result = create_project_structure()
        init_files = [
            "src/__init__.py",
            "tests/__init__.py",
            "src/generation/__init__.py",
            "src/filtering/__init__.py",
            "src/training/__init__.py",
            "src/evaluation/__init__.py",
            "src/utils/__init__.py",
            "tests/unit/__init__.py",
            "tests/integration/__init__.py",
        ]
        
        base_path = Path("projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code")
        for init_file in init_files:
            file_path = base_path / init_file
            assert file_path.exists(), f"Required __init__.py {file_path} was not created"

    def test_create_project_structure_returns_valid_result(self):
        """Test that the function returns a dictionary with expected keys."""
        result = create_project_structure()
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "base_path" in result, "Result missing 'base_path' key"
        assert "directories" in result, "Result missing 'directories' key"
        assert "init_files" in result, "Result missing 'init_files' key"
        assert isinstance(result["directories"], list), "'directories' should be a list"
        assert isinstance(result["init_files"], list), "'init_files' should be a list"
        assert len(result["directories"]) > 0, "No directories were created"
        assert len(result["init_files"]) > 0, "No __init__.py files were created"

    def test_create_project_structure_idempotent(self):
        """Test that running the function twice doesn't cause errors."""
        result1 = create_project_structure()
        result2 = create_project_structure()
        assert len(result1["directories"]) == len(result2["directories"]), \
            "Running twice created different number of directories"
        assert len(result1["init_files"]) == len(result2["init_files"]), \
            "Running twice created different number of __init__.py files"
