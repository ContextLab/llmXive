import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the code directory to the path so we can import setup_project and setup_verify
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_project import create_project_structure
from setup_verify import verify_project_structure

class TestProjectStructure(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory to simulate the project root."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create a mock code directory structure for imports
        self.mock_code_dir = Path(self.temp_dir) / "code"
        self.mock_code_dir.mkdir()
        (self.mock_code_dir / "__init__.py").touch()
        
        # Add temp dir to sys.path temporarily
        if self.temp_dir not in sys.path:
            sys.path.insert(0, self.temp_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        if self.temp_dir in sys.path:
            sys.path.remove(self.temp_dir)

    def test_create_project_structure_creates_directories(self):
        """Test that create_project_structure creates all required directories."""
        # We need to mock the base_path resolution since we're in a temp dir
        import setup_project
        original_resolve = Path.resolve
        
        def mock_resolve(self):
            if self.name == "setup_project.py":
                return Path(self.temp_dir) / "code" / "setup_project.py"
            return original_resolve(self)
        
        Path.resolve = mock_resolve
        
        try:
            dirs, init_files = create_project_structure()
            
            # Check that directories were created
            required_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "results",
                "specs",
                "tests",
                "tests/unit",
                "tests/integration",
                "code/pipeline",
                "code/utils",
                "code/schemas",
                "code/results",
                "code/tests/unit",
                "code/tests/integration",
                "code/scripts",
                "data/logs",
            ]
            
            for dir_name in required_dirs:
                full_path = Path(self.temp_dir) / dir_name
                self.assertTrue(full_path.exists(), f"Directory {full_path} was not created")
                self.assertTrue(full_path.is_dir(), f"{full_path} exists but is not a directory")
        finally:
            Path.resolve = original_resolve

    def test_create_project_structure_creates_init_files(self):
        """Test that create_project_structure creates __init__.py in all directories."""
        import setup_project
        original_resolve = Path.resolve
        
        def mock_resolve(self):
            if self.name == "setup_project.py":
                return Path(self.temp_dir) / "code" / "setup_project.py"
            return original_resolve(self)
        
        Path.resolve = mock_resolve
        
        try:
            dirs, init_files = create_project_structure()
            
            required_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "results",
                "specs",
                "tests",
                "tests/unit",
                "tests/integration",
                "code/pipeline",
                "code/utils",
                "code/schemas",
                "code/results",
                "code/tests/unit",
                "code/tests/integration",
                "code/scripts",
                "data/logs",
            ]
            
            for dir_name in required_dirs:
                full_path = Path(self.temp_dir) / dir_name
                init_file = full_path / "__init__.py"
                self.assertTrue(init_file.exists(), f"__init__.py not found in {full_path}")
        finally:
            Path.resolve = original_resolve

    def test_verify_project_structure_passes_after_creation(self):
        """Test that verify_project_structure returns success after structure is created."""
        import setup_project
        original_resolve = Path.resolve
        
        def mock_resolve(self):
            if self.name == "setup_project.py":
                return Path(self.temp_dir) / "code" / "setup_project.py"
            return original_resolve(self)
        
        Path.resolve = mock_resolve
        
        try:
            # Create structure
            create_project_structure()
            
            # Verify
            success, missing_dirs, missing_inits = verify_project_structure()
            
            self.assertTrue(success, f"Verification failed. Missing dirs: {missing_dirs}, Missing inits: {missing_inits}")
            self.assertEqual(len(missing_dirs), 0)
            self.assertEqual(len(missing_inits), 0)
        finally:
            Path.resolve = original_resolve

    def test_verify_project_structure_fails_without_structure(self):
        """Test that verify_project_structure fails if structure is not created."""
        # Don't create structure, just verify
        success, missing_dirs, missing_inits = verify_project_structure()
        
        self.assertFalse(success)
        self.assertGreater(len(missing_dirs) + len(missing_inits), 0)

if __name__ == "__main__":
    unittest.main()