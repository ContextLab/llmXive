import os
import pytest
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.setup_data_dir import main

def test_data_dir_creation_and_verification(tmp_path):
    """
    Test that setup_data_dir creates the data directory and verifies it.
    We patch the working directory to use a temporary path to avoid
    modifying the actual project structure during tests.
    """
    # Create a temporary directory to act as the project root
    original_cwd = os.getcwd()
    test_project_root = tmp_path / "test_project"
    test_project_root.mkdir()
    
    # Change to the test project root
    os.chdir(test_project_root)
    
    try:
        # The script looks for 'data' relative to the script's parent's parent.
        # However, in a test environment, we want to ensure it creates the dir.
        # We will invoke the function which uses pathlib relative to the script file.
        # To make this test robust, we verify the side effect: the directory exists.
        
        # Since the script uses __file__ to determine paths, it will look for 
        # code/setup_data_dir.py -> parent (code) -> parent (root) -> data
        # We need to ensure the structure exists or mock the path logic.
        # Given the constraint of not rewriting the script, we rely on the script's 
        # logic: project_root = Path(__file__).resolve().parent.parent
        
        # Let's create the expected directory structure in the temp path to match
        # where the script expects to be if it were run from the repo root.
        # Actually, the script determines root based on its own location.
        # If we run this test, __file__ is tests/unit/test_setup_data_dir.py.
        # parent.parent is tests/unit -> tests -> root.
        # So it will look for <test_root>/data.
        
        result = main()
        
        # Check return code
        assert result == 0, "Main function should return 0 on success"
        
        # Verify directory exists
        data_dir = test_project_root / "data" # This logic in main() relies on __file__
        # Wait, the script uses __file__. In the test runner, __file__ is inside tests/unit.
        # So parent.parent is the repo root (tmp_path).
        # So data_dir should be tmp_path / "data".
        
        expected_data_dir = test_project_root / "data"
        assert expected_data_dir.exists(), f"Directory {expected_data_dir} was not created."
        assert expected_data_dir.is_dir(), f"{expected_data_dir} is not a directory."
        
    finally:
        os.chdir(original_cwd)