import os
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

# Add the code directory to the path so we can import create_project_structure
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from create_project_structure import create_structure

class TestProjectStructure(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to simulate the project root
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_structure_created(self):
        """Test that the required directory structure is created."""
        create_structure()
        
        base_dir = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
        
        # Verify base directory exists
        self.assertTrue(base_dir.exists(), f"Base directory {base_dir} does not exist")
        
        # Verify subdirectories
        required_subdirs = [
            "data/raw",
            "data/processed",
            "code",
            "tests",
            "artifacts",
            "artifacts/checkpoints",
            "artifacts/results"
        ]
        
        for subdir in required_subdirs:
            full_path = base_dir / subdir
            self.assertTrue(full_path.exists(), f"Subdirectory {full_path} was not created")
            self.assertTrue(full_path.is_dir(), f"{full_path} exists but is not a directory")

if __name__ == "__main__":
    unittest.main()