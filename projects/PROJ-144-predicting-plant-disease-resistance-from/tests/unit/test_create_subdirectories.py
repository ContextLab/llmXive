import os
import pytest
from pathlib import Path
import tempfile
import shutil

# We need to mock the PROJECT_ROOT and other constants for testing
# or test the logic directly without relying on the global constants
# if they are not easily mockable.
# For this test, we will test the function logic by passing specific paths
# or by temporarily changing the constants if possible.
# However, since the function uses global constants from utils.constants,
# we will test the creation logic by ensuring the directories exist after calling main.

# A better approach for unit testing is to refactor the function to accept paths,
# but since we are extending existing code, we will test the side effects.

# We will create a temporary directory structure to simulate the project root
# and patch the constants if necessary, or just run the script and check.
# Given the constraint of not modifying too much, we will run the script
# in a controlled environment.

# Actually, let's just test that the directories are created relative to the project root.
# We can't easily change PROJECT_ROOT in utils.constants without modifying that file.
# So we will assume the test is run from the project root.

# Alternative: Test the function create_subdirectories directly if we can mock the constants.
# Since we can't easily mock module-level constants in the imported module without
# reloading or complex mocking, we will test the behavior by checking the file system
# after running the main function, assuming the test is run from the project root.

# For a more robust unit test, we would refactor create_subdirectories to accept a base_path.
# But for now, we will test the side effects.

# Let's assume the project root is the current working directory for the test.

import sys
from code.setup.create_subdirectories import create_subdirectories, main
from utils.constants import PROJECT_ROOT, DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_INTERMEDIATE_DIR, RESULTS_PLOTS_DIR

def test_create_subdirectories_creates_directories():
    """Test that create_subdirectories creates the required directories."""
    # Clear any existing directories to ensure a clean test
    # This is a bit risky if run in a real project, but for CI it's fine
    # We will just check if they exist after creation, and if they exist, the test passes.
    # The function uses exist_ok=True, so it won't fail if they already exist.
    
    result = create_subdirectories()
    
    # Check that the returned list has the expected number of directories
    assert len(result) == 4
    
    # Check that each directory exists
    for dir_path in result:
        assert os.path.exists(dir_path), f"Directory {dir_path} was not created."
        assert os.path.isdir(dir_path), f"{dir_path} is not a directory."
        
    # Specifically check the expected paths
    assert os.path.exists(DATA_RAW_DIR), f"Directory {DATA_RAW_DIR} was not created."
    assert os.path.exists(DATA_PROCESSED_DIR), f"Directory {DATA_PROCESSED_DIR} was not created."
    assert os.path.exists(DATA_INTERMEDIATE_DIR), f"Directory {DATA_INTERMEDIATE_DIR} was not created."
    assert os.path.exists(RESULTS_PLOTS_DIR), f"Directory {RESULTS_PLOTS_DIR} was not created."

def test_main_returns_zero():
    """Test that main returns 0 on success."""
    # We can call main and check the return value
    # But main calls create_subdirectories which prints to stdout
    # We can capture stdout if needed, but for now just check the return value
    result = main()
    assert result == 0