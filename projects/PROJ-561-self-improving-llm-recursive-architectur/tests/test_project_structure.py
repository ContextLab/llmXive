import os
import sys
import unittest
from pathlib import Path

class TestProjectStructure(unittest.TestCase):
    """
    Verification test for T001: Create project structure.
    
    This test verifies that all required directories and __init__.py files
    exist after running setup_project.py.
    """
    
    @classmethod
    def setUpClass(cls):
        """Run setup script before tests."""
        script_path = Path(__file__).parent.parent.parent / "code" / "setup_project.py"
        if script_path.exists():
            import subprocess
            result = subprocess.run([sys.executable, str(script_path)], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Setup script failed: {result.stderr}")
    
    def test_directories_exist(self):
        """Verify all required directories exist."""
        base_dir = Path(__file__).parent.parent.parent
        
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "results",
            "specs",
            "tests",
            "tests/unit",
            "tests/integration"
        ]
        
        for dir_name in required_dirs:
            dir_path = base_dir / dir_name
            self.assertTrue(dir_path.exists(), f"Directory missing: {dir_path}")
            self.assertTrue(dir_path.is_dir(), f"Not a directory: {dir_path}")
    
    def test_init_files_exist(self):
        """Verify __init__.py files exist in required locations."""
        base_dir = Path(__file__).parent.parent.parent
        
        init_files = [
            "code/__init__.py",
            "tests/__init__.py",
            "tests/unit/__init__.py",
            "tests/integration/__init__.py",
            "results/__init__.py",
            "specs/__init__.py"
        ]
        
        for file_name in init_files:
            file_path = base_dir / file_name
            self.assertTrue(file_path.exists(), f"__init__.py missing: {file_path}")
            self.assertTrue(file_path.is_file(), f"Not a file: {file_path}")

if __name__ == "__main__":
    unittest.main()