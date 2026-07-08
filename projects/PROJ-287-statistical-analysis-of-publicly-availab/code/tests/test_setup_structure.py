import os
import unittest
from pathlib import Path
import tempfile
import shutil

# Import the setup function
# Note: The path in the artifact is code/code/setup_project_structure.py
# But the API surface says code/setup_project_structure.py
# We will adjust the import based on the actual file path provided in the artifact.
# The artifact path is code/code/setup_project_structure.py, so we import from there.
# However, to make it runnable in a test context, we might need to adjust sys.path.

# Let's assume the test runs from the project root where 'code' is a subdirectory.
# The artifact path provided is 'code/code/setup_project_structure.py'.
# This seems nested. Let's assume the user will run the script from the root.
# For the test, we will import the module dynamically.

class TestProjectStructure(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary directory to simulate the project root
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Ensure the 'code' directory exists if the script is expected to be there
        code_dir = Path(self.test_dir) / "code"
        code_dir.mkdir(exist_ok=True)
        
        # Copy the script logic or import it. Since we can't easily import a file
        # from a temp dir without sys.path manipulation, we will re-implement the logic
        # or import it by adding the path.
        # Better: We will just run the main() function from the imported module if possible.
        # But the file is in code/code/.
        
        # Let's add the test_dir/code to sys.path
        import sys
        self.sys_path_backup = sys.path.copy()
        sys.path.insert(0, str(Path(self.test_dir) / "code"))
        
        # Now try to import. The file is code/setup_project_structure.py inside code/
        # Wait, the artifact path is "code/code/setup_project_structure.py".
        # This implies the file is at <root>/code/code/setup_project_structure.py.
        # So we need to add <root>/code to path, and import setup_project_structure.
        # But the file is inside code/code/.
        # Let's just copy the logic to a temporary module or import it directly.
        
        # Actually, let's just test the directories exist after running the script.
        # We will execute the script using subprocess or by importing the function.
        # To import, we need the file to be in a package.
        # Let's assume the file is at <root>/code/setup_project_structure.py for simplicity in testing,
        # or we adjust the import.
        
        # Given the artifact path "code/code/setup_project_structure.py",
        # let's assume the user will run it from the root.
        # We will import it by adding the parent of 'code' to path? No.
        # Let's just use importlib to load the file.
        import importlib.util
        script_path = Path(self.test_dir) / "code" / "code" / "setup_project_structure.py"
        spec = importlib.util.spec_from_file_location("setup_script", script_path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def tearDown(self):
        os.chdir(self.original_cwd)
        import sys
        sys.path = self.sys_path_backup
        shutil.rmtree(self.test_dir)

    def test_directories_created(self):
        """Verify that all required directories are created."""
        required_dirs = [
            "src",
            "tests",
            "data/raw",
            "data/processed",
            "results/figures",
            "results/stats",
            "docs"
        ]
        
        # Run the main function
        self.module.main()
        
        for dir_name in required_dirs:
            full_path = Path(self.test_dir) / dir_name
            self.assertTrue(full_path.exists(), f"Directory {dir_name} was not created.")
            self.assertTrue(full_path.is_dir(), f"{dir_name} is not a directory.")

    def test_nested_directories(self):
        """Verify that nested directories like data/raw are created correctly."""
        self.module.main()
        
        nested_dirs = [
            "data/raw",
            "data/processed",
            "results/figures",
            "results/stats"
        ]
        
        for dir_name in nested_dirs:
            full_path = Path(self.test_dir) / dir_name
            self.assertTrue(full_path.exists(), f"Nested directory {dir_name} was not created.")