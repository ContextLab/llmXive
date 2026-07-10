import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest import TestCase, mock

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_project import create_project_structure, main

class TestSetupProject(TestCase):
    def setUp(self):
        """Create a temporary directory to simulate the project root."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Ensure 'code' directory doesn't exist yet to test creation
        code_dir = Path("code")
        if code_dir.exists():
            shutil.rmtree(code_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_create_project_structure_creates_directories(self):
        """Verify that create_project_structure creates all required directories."""
        created_dirs = create_project_structure()
        
        # Check that 'code' exists
        self.assertTrue(Path("code").exists())
        
        # Check specific subdirectories
        required_dirs = [
            "code/src",
            "code/tests",
            "code/data/raw",
            "code/data/preprocessed",
            "code/data/results",
            "code/data/logs",
            "code/data/motion"
        ]
        
        for dir_path in required_dirs:
            self.assertTrue(Path(dir_path).exists(), f"Directory {dir_path} was not created")
            self.assertTrue(Path(dir_path).is_dir(), f"{dir_path} is not a directory")

    def test_create_project_structure_creates_init_files(self):
        """Verify that __init__.py files are created in src and tests."""
        create_project_structure()
        
        src_init = Path("code/src/__init__.py")
        tests_init = Path("code/tests/__init__.py")
        
        self.assertTrue(src_init.exists(), "code/src/__init__.py not created")
        self.assertTrue(tests_init.exists(), "code/tests/__init__.py not created")

    def test_create_project_structure_creates_gitkeep(self):
        """Verify that .gitkeep files are created in data directories."""
        create_project_structure()
        
        data_subdirs = ["raw", "preprocessed", "results", "logs", "motion"]
        for subdir in data_subdirs:
            gitkeep = Path(f"code/data/{subdir}/.gitkeep")
            self.assertTrue(gitkeep.exists(), f".gitkeep not created in code/data/{subdir}")

    @mock.patch('sys.stdout')
    def test_main_returns_zero(self, mock_stdout):
        """Verify that main() returns 0 on success."""
        result = main()
        self.assertEqual(result, 0)
