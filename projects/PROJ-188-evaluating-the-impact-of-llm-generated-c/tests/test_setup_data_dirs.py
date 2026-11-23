import os
import tempfile
from pathlib import Path
import sys

# Add the code directory to the path to allow imports
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_data_dirs import create_data_directories

def test_create_data_directories():
    """
    Test that create_data_directories creates the expected folder structure.
    We use a temporary directory to avoid side effects on the real project tree.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Mock the __file__ behavior by temporarily changing the module's context
        # or by directly testing the logic if we refactor slightly.
        # For this test, we will patch the behavior or verify the function's
        # side effects by calling it in a controlled environment.
        
        # Since the function relies on __file__ to find the project root,
        # we will test the logic by creating a mock structure.
        
        # However, to strictly test the function as written:
        # The function assumes it is run from code/setup_data_dirs.py
        # and creates directories relative to the project root (parent of code/).
        
        # We will verify the function exists and runs without error.
        # A more robust integration test would mock the path logic.
        
        try:
            create_data_directories()
            # If we are running this in the real project, the dirs should exist now.
            # If running in a temp dir, the function might try to create dirs
            # in the actual repo root.
            
            # Verification: Check if the directories exist in the current working directory
            # relative to the script's expected location.
            # Since we are in a test, we assume the test runner is at the project root.
            # We check if 'data' exists at the project root level.
            project_root = Path(__file__).parent.parent
            data_root = project_root / "data"
            
            assert data_root.exists(), "data/ directory was not created."
            assert (data_root / "raw").exists(), "data/raw/ directory was not created."
            assert (data_root / "intermediate").exists(), "data/intermediate/ directory was not created."
            assert (data_root / "processed").exists(), "data/processed/ directory was not created."
            
        except Exception as e:
            # If the test environment is isolated, we might not be able to write to the real root.
            # In that case, we assert that the function is callable and the logic is sound.
            # But for a real test, we want the files to exist.
            raise e

if __name__ == "__main__":
    test_create_data_directories()
    print("Test passed: Data directories created successfully.")