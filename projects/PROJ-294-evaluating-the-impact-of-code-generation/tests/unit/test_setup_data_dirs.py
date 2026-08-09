import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))

from setup_data_dirs import create_directories

class TestDataDirectoryCreation:
    """Unit tests for T008: Data directory structure creation."""

    def setup_method(self):
        """Create a temporary directory to simulate project root."""
        self.temp_dir = tempfile.mkdtemp()
        self.code_dir = os.path.join(self.temp_dir, "code")
        self.data_dir = os.path.join(self.temp_dir, "data")
        os.makedirs(self.code_dir)

        # Mock the script location so setup_data_dirs thinks it's in the code folder
        self.original_script_path = "code/setup_data_dirs.py"
        # We will patch the logic by setting an environment variable or mocking os.path
        # For simplicity, we will test the directory creation logic directly by calling
        # a modified version or by mocking the base path.
        # However, the current function calculates path relative to __file__.
        # To test properly without moving files, we will test the logic by verifying
        # that the function creates the expected subfolders in 'data' relative to 'code'.
        
        # Since we can't easily move the file in the test environment without complex mocking,
        # we will verify the logic by checking if the function runs without error 
        # and creates the 'data' folder next to the 'code' folder where the script resides.
        # In this test, we assume the script is running from the temp_dir/code directory.
        
        # Actually, let's just verify the function runs and creates the dirs.
        # We need to ensure the 'code' directory exists in the temp structure.
        pass

    def teardown_method(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_creates_data_raw_directory(self):
        """Verify that data/raw is created."""
        # We need to execute the function. Since it calculates paths relative to __file__,
        # and our file is in tests/unit/, we need to be careful.
        # However, the requirement is that the script creates dirs relative to the project root.
        # Let's mock the __file__ path or just check if the dirs exist after running main.
        
        # Simpler approach: Run the function in a context where we know the layout.
        # We'll create a fake script in the temp_dir/code folder and import it? No, too complex.
        
        # Let's just assert that the function doesn't crash and creates the expected structure
        # if we run it from the temp_dir/code folder.
        
        # We will manually construct the expected paths and verify they are created.
        # Since the function uses os.path.dirname(__file__), and the file is in the project,
        # we trust the logic but verify the outcome.
        
        # To make this test work without moving the file:
        # 1. Create the temp structure: temp_dir/code, temp_dir/data
        # 2. The function should create temp_dir/data/raw, etc.
        # 3. We can't easily change __file__.
        
        # Alternative: Test the logic by extracting the path calculation.
        # But the function is simple enough. Let's just run it and see if it creates the dirs
        # in the expected location relative to where the test is run (which is wrong).
        
        # Correct approach for this specific constraint:
        # The function calculates: project_root = dirname(dirname(__file__))
        # If __file__ is .../tests/unit/test_setup_data_dirs.py, then:
        # dirname -> tests/unit
        # dirname -> tests
        # project_root -> tests (wrong)
        
        # We must mock the __file__ or the path calculation.
        # Since we can't edit the source to add a parameter for this test easily without
        # changing the signature (which might break other callers), we will rely on the
        # fact that the script is supposed to be run as a standalone.
        
        # Let's just verify that the function runs and creates the 'data' folder
        # in the directory two levels up from the script.
        # In a real run, the script is in code/, so two levels up is project root.
        # In this test, the script is in code/ (if we copy it) or we are importing it.
        
        # Let's assume the test is run from the project root and the script is in code/.
        # We will create the necessary directories manually to ensure the function has a place to run.
        
        # Create the 'code' directory in the temp root to simulate the project structure
        # Actually, the function uses __file__.
        # If we import setup_data_dirs from tests, __file__ is tests/setup_data_dirs.py? No.
        
        # Let's just check if the function creates the directories in the expected location
        # relative to the actual script location.
        # We will create a temporary 'code' folder in the temp_dir, copy the script there,
        # and run it.
        
        import importlib.util
        import shutil

        script_path = os.path.join(os.path.dirname(__file__), "..", "..", "code", "setup_data_dirs.py")
        # Normalize path
        script_path = os.path.normpath(script_path)
        
        if not os.path.exists(script_path):
            # If the script isn't where we think it is, skip or fail
            pytest.skip("Script not found at expected location")

        # Create a temp project structure
        test_project_root = tempfile.mkdtemp()
        test_code_dir = os.path.join(test_project_root, "code")
        os.makedirs(test_code_dir)
        
        # Copy the script to the test code dir
        test_script_path = os.path.join(test_code_dir, "setup_data_dirs.py")
        shutil.copy(script_path, test_script_path)
        
        # Also copy utils.py if needed
        utils_src = os.path.join(os.path.dirname(__file__), "..", "..", "code", "utils.py")
        if os.path.exists(utils_src):
            shutil.copy(utils_src, os.path.join(test_code_dir, "utils.py"))
        
        # Add the test_code_dir to sys.path temporarily
        sys.path.insert(0, test_code_dir)
        
        try:
            spec = importlib.util.spec_from_file_location("test_setup_data_dirs_script", test_script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Run the main function
            result = module.main()
            
            assert result == 0, "Function returned non-zero exit code"
            
            # Check if directories were created
            data_raw = os.path.join(test_project_root, "data", "raw")
            data_generated = os.path.join(test_project_root, "data", "generated")
            data_analysis = os.path.join(test_project_root, "data", "analysis")
            
            assert os.path.exists(data_raw), f"Directory {data_raw} was not created"
            assert os.path.exists(data_generated), f"Directory {data_generated} was not created"
            assert os.path.exists(data_analysis), f"Directory {data_analysis} was not created"
            
        finally:
            sys.path.remove(test_code_dir)
            shutil.rmtree(test_project_root)

    def test_directories_are_empty_or_valid(self):
        """Verify that created directories are valid directories."""
        # Reuse the logic from the previous test but simplified
        import importlib.util
        import shutil

        script_path = os.path.join(os.path.dirname(__file__), "..", "..", "code", "setup_data_dirs.py")
        script_path = os.path.normpath(script_path)
        
        if not os.path.exists(script_path):
            pytest.skip("Script not found")

        test_project_root = tempfile.mkdtemp()
        test_code_dir = os.path.join(test_project_root, "code")
        os.makedirs(test_code_dir)
        
        test_script_path = os.path.join(test_code_dir, "setup_data_dirs.py")
        shutil.copy(script_path, test_script_path)
        
        utils_src = os.path.join(os.path.dirname(__file__), "..", "..", "code", "utils.py")
        if os.path.exists(utils_src):
            shutil.copy(utils_src, os.path.join(test_code_dir, "utils.py"))
        
        sys.path.insert(0, test_code_dir)
        
        try:
            spec = importlib.util.spec_from_file_location("test_setup_data_dirs_script", test_script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.main()
            
            data_root = os.path.join(test_project_root, "data")
            assert os.path.isdir(data_root)
            
            for subdir in ["raw", "generated", "analysis"]:
                path = os.path.join(data_root, subdir)
                assert os.path.isdir(path)
                # They should be empty initially
                assert len(os.listdir(path)) == 0
        finally:
            sys.path.remove(test_code_dir)
            shutil.rmtree(test_project_root)
