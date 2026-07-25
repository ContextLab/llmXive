import os
import pytest
from pathlib import Path
import sys

# Add the parent directory to the path to allow importing from code/
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_project import main

def test_setup_project_creates_directories(tmp_path, capsys):
    """
    Test that setup_project creates the required directory structure.
    We mock the root path by changing the working directory and using tmp_path.
    """
    # We need to monkeypatch the root detection logic in setup_project
    # Since setup_project calculates root relative to its own file, 
    # we will test the logic by importing and calling main, 
    # but we must ensure the directories are created in a known location.
    
    # To properly test this without altering the global file system or 
    # relying on the actual script location during CI, we verify the 
    # existence of the directories after running the script in the 
    # actual project context if possible, or mock the Path logic.
    
    # However, the task requires the script to actually run and create dirs.
    # We will assert that the function returns 0 and check standard output.
    
    # Since the script determines root based on its own location (__file__),
    # and we are running this test in the repo root context (ideally),
    # we verify the directories exist in the current working directory 
    # relative to where the script expects to run (project root).
    
    # For this test to be robust in a CI environment where we might run 
    # from a specific root, we assume the test is run from the project root.
    
    original_cwd = os.getcwd()
    try:
        # Ensure we are in the project root for the test
        # The script looks for 'data', 'code', etc. relative to its parent.
        # If this test file is in tests/, and script in code/, 
        # the script's parent is code/, so root is project root.
        
        # We run the main function
        exit_code = main()
        
        assert exit_code == 0, "main() should return 0 on success"
        
        # Verify directories were created (or existed)
        root = Path(__file__).resolve().parent.parent
        required_dirs = [
            root / "data" / "raw",
            root / "data" / "processed",
            root / "data" / "results",
            root / "code",
            root / "tests",
            root / "state",
        ]
        
        for d in required_dirs:
            assert d.exists(), f"Directory {d} should exist after running setup_project"
            assert d.is_dir(), f"{d} should be a directory"
            
    finally:
        os.chdir(original_cwd)

def test_setup_project_idempotent(tmp_path, capsys):
    """
    Test that running the script multiple times does not fail.
    """
    # Run twice
    exit_code_1 = main()
    exit_code_2 = main()
    
    assert exit_code_1 == 0
    assert exit_code_2 == 0