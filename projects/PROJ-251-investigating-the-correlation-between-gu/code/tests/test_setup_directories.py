import unittest
import os
from pathlib import Path
import tempfile
import shutil
from code.setup_directories import create_directories

class TestSetupDirectories(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_directories_structure(self):
        """Test that all required directories are created."""
        success = create_directories()
        self.assertTrue(success, "Directory creation should succeed")

        base_path = Path(self.temp_dir)
        
        expected_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "specs/001-investigating-the-correlation-between-gu/contracts",
        ]
        
        for dir_path in expected_dirs:
            full_path = base_path / dir_path
            self.assertTrue(
                full_path.exists(), 
                f"Directory {dir_path} should exist after creation"
            )
            self.assertTrue(
                full_path.is_dir(), 
                f"{dir_path} should be a directory"
            )

    def test_create_directories_idempotent(self):
        """Test that running create_directories multiple times doesn't fail."""
        success1 = create_directories()
        success2 = create_directories()
        self.assertTrue(success1, "First run should succeed")
        self.assertTrue(success2, "Second run should succeed (exist_ok=True)")

    def test_create_directories_creates_parents(self):
        """Test that parent directories are created when needed."""
        # The contracts directory requires multiple parent levels
        success = create_directories()
        self.assertTrue(success)
        
        contracts_path = Path(self.temp_dir) / "specs" / "001-investigating-the-correlation-between-gu" / "contracts"
        self.assertTrue(contracts_path.exists())
        
        # Verify intermediate directories also exist
        specs_path = Path(self.temp_dir) / "specs"
        self.assertTrue(specs_path.exists())
        
        project_spec_path = Path(self.temp_dir) / "specs" / "001-investigating-the-correlation-between-gu"
        self.assertTrue(project_spec_path.exists())

if __name__ == "__main__":
    unittest.main()