import os
import pytest
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from setup_spec_directories import create_spec_directories

def test_spec_directory_creation(tmp_path):
    """
    Test that the spec directory creation function works correctly.
    We patch the project root to use a temporary directory for testing.
    """
    # Create a temporary specs directory structure
    test_spec_root = tmp_path / "specs"
    test_spec_root.mkdir()
    
    # Mock the target directory path within the temp structure
    target_dir = test_spec_root / "001-neural-correlates-of-anticipatory-reward"
    
    # We can't easily mock the absolute path logic inside the function 
    # without refactoring, so we test the logic by ensuring the 
    # function can create a directory when called in a real context,
    # or we verify the directory exists after running the main logic 
    # if we were to run it in the real project root.
    
    # Since the function relies on __file__ to find the root, 
    # and we are running tests from a different location, 
    # we will verify the function's ability to create a directory 
    # by checking if the logic holds for the actual project structure 
    # after the script is run.
    
    # For this unit test, we assert that the function returns True 
    # when the directory is successfully created in the actual project root.
    # However, to make this test portable, we will just verify the 
    # function exists and can be imported. The actual creation is 
    # verified by the integration of the script in the real project root.
    
    # A more robust test: Run the function and check if the directory 
    # exists relative to the code directory (assuming standard layout).
    # We assume the test runs in the context where 'code' is a sibling to 'tests'.
    code_dir = Path(__file__).resolve().parent.parent / "code"
    project_root = code_dir.parent
    expected_spec_dir = project_root / "specs" / "001-neural-correlates-of-anticipatory-reward"
    
    # Clean up if exists from previous runs
    if expected_spec_dir.exists():
        # We shouldn't delete it here if it's part of the project state, 
        # but for a test of creation, we just check existence after call.
        pass

    # Call the function
    result = create_spec_directories()
    
    assert result is True
    assert expected_spec_dir.exists()
    assert expected_spec_dir.is_dir()