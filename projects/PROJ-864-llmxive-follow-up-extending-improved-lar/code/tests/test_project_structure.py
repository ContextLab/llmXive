import os
import sys
import unittest
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

class TestProjectStructure(unittest.TestCase):
    """
    Contract test to verify the project directory structure
    matches the requirements of T001.
    """
    
    def setUp(self):
        self.project_root = project_root
        self.code_dir = self.project_root / "code"
        
        # Expected directories relative to code/
        self.expected_dirs = [
            "data",
            "models",
            "training",
            "analysis",
            "utils",
            "tests"
        ]
        
        # Expected files
        self.expected_files = [
            "main.py"
        ]

    def test_code_directory_exists(self):
        """Verify the code/ directory exists."""
        self.assertTrue(self.code_dir.exists(), f"Directory {self.code_dir} does not exist")
        self.assertTrue(self.code_dir.is_dir(), f"{self.code_dir} is not a directory")

    def test_subdirectories_exist(self):
        """Verify all required subdirectories exist."""
        for subdir_name in self.expected_dirs:
            subdir_path = self.code_dir / subdir_name
            self.assertTrue(
                subdir_path.exists(), 
                f"Subdirectory {subdir_name} missing in {self.code_dir}"
            )
            self.assertTrue(
                subdir_path.is_dir(),
                f"{subdir_name} is not a directory"
            )

    def test_data_subdirectories_exist(self):
        """Verify data/raw, data/processed, data/artifacts exist."""
        data_dir = self.code_dir / "data"
        required_data_subdirs = ["raw", "processed", "artifacts"]
        
        for subdir_name in required_data_subdirs:
            subdir_path = data_dir / subdir_name
            self.assertTrue(
                subdir_path.exists(),
                f"Data subdirectory {subdir_name} missing in {data_dir}"
            )
            self.assertTrue(
                subdir_path.is_dir(),
                f"{subdir_name} is not a directory"
            )

    def test_main_py_exists(self):
        """Verify main.py exists at the root of code/."""
        main_py_path = self.code_dir / "main.py"
        self.assertTrue(
            main_py_path.exists(),
            f"main.py missing in {self.code_dir}"
        )
        self.assertTrue(
            main_py_path.is_file(),
            "main.py is not a file"
        )

    def test_main_py_importable(self):
        """Verify main.py is syntactically valid and importable."""
        main_py_path = self.code_dir / "main.py"
        try:
            # Attempt to import the main module
            import importlib.util
            spec = importlib.util.spec_from_file_location("main", main_py_path)
            if spec is None or spec.loader is None:
                self.fail(f"Could not load spec for {main_py_path}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Verify main function exists
            self.assertTrue(
                hasattr(module, 'main'),
                "main.py does not export a 'main' function"
            )
        except Exception as e:
            self.fail(f"Failed to import or execute main.py: {e}")

if __name__ == "__main__":
    unittest.main()