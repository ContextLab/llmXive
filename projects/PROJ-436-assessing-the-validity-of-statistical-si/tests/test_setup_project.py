import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add code directory to path for imports
code_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_project import create_directories, create_init_files

class TestProjectStructure:
    """Test that project structure creation functions work correctly."""

    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory to act as project root."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_create_directories_creates_all_required(self, temp_project_root):
        """Verify that all required directories are created."""
        # Change to temp root for the test
        original_cwd = os.getcwd()
        os.chdir(temp_project_root)
        
        try:
            # Mock the Path(__file__).resolve().parent.parent to be temp_project_root
            # by temporarily changing the working directory
            created = create_directories()
            
            required_dirs = [
                "data/raw",
                "data/processed",
                "code",
                "tests/unit",
                "tests/integration",
                "contracts",
                "figures",
                "specs"
            ]
            
            for dir_name in required_dirs:
                dir_path = temp_project_root / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"
        finally:
            os.chdir(original_cwd)

    def test_create_init_files_creates_init_py(self, temp_project_root):
        """Verify that __init__.py files are created in required directories."""
        original_cwd = os.getcwd()
        os.chdir(temp_project_root)
        
        try:
            # First create directories
            create_directories()
            
            # Then create init files
            created = create_init_files()
            
            required_init_dirs = [
                "code",
                "tests",
                "tests/unit",
                "tests/integration",
                "contracts"
            ]
            
            for dir_name in required_init_dirs:
                init_path = temp_project_root / dir_name / "__init__.py"
                assert init_path.exists(), f"__init__.py not created in {dir_name}"
                assert init_path.is_file(), f"{dir_name}/__init__.py exists but is not a file"
        finally:
            os.chdir(original_cwd)

    def test_create_directories_idempotent(self, temp_project_root):
        """Verify that running create_directories multiple times doesn't fail."""
        original_cwd = os.getcwd()
        os.chdir(temp_project_root)
        
        try:
            create_directories()
            # Run again - should not raise
            create_directories()
            
            # Verify directories still exist
            assert (temp_project_root / "code").exists()
            assert (temp_project_root / "data/raw").exists()
        finally:
            os.chdir(original_cwd)

    def test_create_init_files_idempotent(self, temp_project_root):
        """Verify that running create_init_files multiple times doesn't fail."""
        original_cwd = os.getcwd()
        os.chdir(temp_project_root)
        
        try:
            create_directories()
            create_init_files()
            # Run again - should not raise
            create_init_files()
            
            # Verify init files still exist
            assert (temp_project_root / "code" / "__init__.py").exists()
            assert (temp_project_root / "tests" / "__init__.py").exists()
        finally:
            os.chdir(original_cwd)
