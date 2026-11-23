import os
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects/PROJ-886-llmxive-follow-up-extending-dreamx-world"))

from utils.setup_structure import main

class TestSetupStructure(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create the project root directory structure
        self.project_root = Path("projects/PROJ-886-llmxive-follow-up-extending-dreamx-world")
        self.project_root.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        # Restore original working directory and clean up
        os.chdir(self.original_cwd)
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)
    
    def test_directory_creation(self):
        """Test that all 15 required directories are created."""
        # Run the setup function
        main()
        
        # Verify directories exist
        required_dirs = [
            "data/raw",
            "data/derived",
            "data/derived/videos",
            "code",
            "code/models",
            "code/pipeline",
            "code/analysis",
            "code/utils",
            "tests/unit",
            "tests/integration",
            "logs",
            "docs",
            "config"
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            self.assertTrue(full_path.exists(), f"Directory {full_path} was not created")
            self.assertTrue(full_path.is_dir(), f"{full_path} is not a directory")
    
    def test_nested_structure(self):
        """Test that nested directories like data/derived/videos are created."""
        main()
        
        nested_dirs = [
            "data/raw",
            "data/derived",
            "data/derived/videos"
        ]
        
        for dir_path in nested_dirs:
            full_path = self.project_root / dir_path
            self.assertTrue(full_path.exists(), f"Nested directory {full_path} was not created")
    
    def test_project_root_exists(self):
        """Test that the main project root directory exists."""
        main()
        self.assertTrue(self.project_root.exists())
        self.assertTrue(self.project_root.is_dir())

if __name__ == "__main__":
    unittest.main()