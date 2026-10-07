import os
import sys
from pathlib import Path
import tempfile
import shutil

def test_create_project_structure():
    """
    Test that create_project_structure creates the required directories.
    
    This test creates a temporary directory structure and verifies that
    all required subdirectories are created.
    """
    # Create a temporary base directory
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    
    try:
        # Change to the temporary directory
        os.chdir(temp_dir)
        
        # Create the code directory to simulate the project root
        # We need to create the structure relative to the temp directory
        # which acts as our "project root"
        
        # Define the expected directories relative to temp_dir
        expected_dirs = [
            "code/simulation",
            "code/analysis",
            "code/statistics",
            "code/viz",
            "code/utils",
            "data/raw",
            "data/processed",
            "data/aggregated",
            "tests/unit",
            "tests/contract",
            "tests/integration"
        ]
        
        # Create the structure using the function
        from utils.setup_data_dirs import create_project_structure
        
        # We need to simulate the project root being temp_dir
        # The function looks for the parent of the module's parent
        # So we'll create a mock structure
        
        # Actually, let's just verify the directories exist after running
        # the function in the temp directory
        
        # Create a minimal structure to allow the import to work
        os.makedirs("code/utils", exist_ok=True)
        
        # Copy the function into a temporary module
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "setup_data_dirs", 
            "code/utils/setup_data_dirs.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Run the function
        result = module.create_project_structure()
        
        # Verify all directories were created
        for dir_path in expected_dirs:
            full_path = Path(temp_dir) / dir_path
            assert full_path.exists(), f"Directory not created: {full_path}"
            assert full_path.is_dir(), f"Not a directory: {full_path}"
        
        assert result is True, "Function should return True on success"
        
    finally:
        # Restore original directory and clean up
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

def test_idempotency():
    """
    Test that running create_project_structure multiple times doesn't fail.
    """
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        os.makedirs("code/utils", exist_ok=True)
        
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "setup_data_dirs", 
            "code/utils/setup_data_dirs.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Run twice
        result1 = module.create_project_structure()
        result2 = module.create_project_structure()
        
        assert result1 is True
        assert result2 is True
        
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_create_project_structure()
    test_idempotency()
    print("All tests passed!")
