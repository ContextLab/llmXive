import os
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

# Add parent directory to path to import code.setup_project
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.setup_project import main

class TestSetupProject(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Create a temporary directory to simulate project root."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.original_cwd = os.getcwd()
        os.chdir(cls.temp_dir)

    @classmethod
    def tearDownClass(cls):
        """Restore original working directory and remove temp dir."""
        os.chdir(cls.original_cwd)
        shutil.rmtree(cls.temp_dir)

    def test_directories_created(self):
        """Verify that all required directories are created."""
        required_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "tests",
            "artifacts/logs",
            "artifacts/plots",
            "artifacts/reports",
            "contracts"
        ]
        
        # Run the setup function
        exit_code = main()
        
        # Check exit code
        self.assertEqual(exit_code, 0, "Setup function should return 0 on success")
        
        # Verify each directory exists
        for dir_path in required_dirs:
            full_path = Path(dir_path)
            self.assertTrue(
                full_path.exists() and full_path.is_dir(),
                f"Directory {dir_path} should exist after setup"
            )

    def test_nested_structure(self):
        """Verify nested directories like data/raw and artifacts/logs are created."""
        # Re-run setup in a fresh temp dir to ensure clean state
        fresh_temp = tempfile.mkdtemp()
        original_cwd = os.getcwd()
        os.chdir(fresh_temp)
        
        try:
            main()
            
            # Check specific nested paths
            self.assertTrue((Path("data") / "raw").exists())
            self.assertTrue((Path("data") / "processed").exists())
            self.assertTrue((Path("artifacts") / "logs").exists())
            self.assertTrue((Path("artifacts") / "plots").exists())
            self.assertTrue((Path("artifacts") / "reports").exists())
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(fresh_temp)

if __name__ == "__main__":
    unittest.main()