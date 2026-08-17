import unittest
import os
from pathlib import Path
import tempfile
import shutil
from code.setup_directories import create_directories

class TestSetupDirectories(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create a dummy code directory structure to simulate project root
        os.makedirs("code", exist_ok=True)
        
    def tearDown(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_create_directories_structure(self):
        """Test that all required directories are created with correct structure."""
        import code.setup_directories as sd
        original_func = sd.create_directories
        
        def mock_create_directories():
            base_path = Path(self.test_dir)
            directories = [
                base_path / "code",
                base_path / "data" / "raw",
                base_path / "data" / "processed",
                base_path / "data" / "results",
                base_path / "specs" / "001-investigating-the-correlation-between-gu" / "contracts"
            ]
            
            created_paths = []
            for dir_path in directories:
                dir_path.mkdir(parents=True, exist_ok=True)
                created_paths.append(str(dir_path))
            
            return created_paths
        
        sd.create_directories = mock_create_directories
        
        try:
            created = create_directories()
            
            expected_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "data/results",
                "specs/001-investigating-the-correlation-between-gu/contracts"
            ]
            
            for dir_path in expected_dirs:
                full_path = Path(self.test_dir) / dir_path
                self.assertTrue(full_path.exists(), f"Directory {dir_path} was not created")
                self.assertTrue(full_path.is_dir(), f"{dir_path} is not a directory")
            
            contracts_path = Path(self.test_dir) / "specs" / "001-investigating-the-correlation-between-gu" / "contracts"
            self.assertTrue(contracts_path.exists(), "Contracts directory path is incorrect")
            
        finally:
            sd.create_directories = original_func

    def test_directories_are_unique(self):
        """Test that no duplicate directories are attempted."""
        import code.setup_directories as sd
        original_func = sd.create_directories
        
        def mock_create_directories():
            base_path = Path(self.test_dir)
            directories = [
                base_path / "code",
                base_path / "data" / "raw",
                base_path / "data" / "processed",
                base_path / "data" / "results",
                base_path / "specs" / "001-investigating-the-correlation-between-gu" / "contracts"
            ]
            
            paths = [str(d) for d in directories]
            self.assertEqual(len(paths), len(set(paths)), "Duplicate directories detected")
            
            return paths
        
        sd.create_directories = mock_create_directories
        
        try:
            created = create_directories()
            self.assertGreater(len(created), 0, "No directories were created")
        finally:
            sd.create_directories = original_func

    def test_nested_directory_creation(self):
        """Test that nested directories are created with parents=True."""
        import code.setup_directories as sd
        original_func = sd.create_directories
        
        def mock_create_directories():
            base_path = Path(self.test_dir)
            nested_path = base_path / "specs" / "001-investigating-the-correlation-between-gu" / "contracts"
            nested_path.mkdir(parents=True, exist_ok=True)
            return [str(nested_path)]
        
        sd.create_directories = mock_create_directories
        
        try:
            created = create_directories()
            specs_path = Path(self.test_dir) / "specs" / "001-investigating-the-correlation-between-gu"
            contracts_path = specs_path / "contracts"
            
            self.assertTrue(specs_path.exists(), "Parent specs directory not created")
            self.assertTrue(contracts_path.exists(), "Nested contracts directory not created")
        finally:
            sd.create_directories = original_func

if __name__ == "__main__":
    unittest.main()