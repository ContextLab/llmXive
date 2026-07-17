"""
Unit tests for setup_plots_directory.py (Task T003).
"""
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add the code directory to the path to import the module
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_plots_directory import main

def test_plots_directory_creation():
    """
    Verify that the output/plots directory is created if it doesn't exist.
    Since we cannot easily manipulate the actual project directory structure
    in a test environment without side effects, we test the logic by
    mocking the path or verifying the function's behavior on a temp dir.
    
    However, the requirement is to create the directory in the specific project path.
    We will run the main function and check if the directory exists in the
    expected location relative to the script.
    """
    # We rely on the script determining its own location.
    # We can't easily mock the file system path of the script itself in this context
    # without complex mocking. Instead, we verify the directory exists after running.
    
    # Run the main function
    main()
    
    # Determine the expected path relative to the script location
    script_path = Path(__file__).parent.parent.parent / "code" / "setup_plots_directory.py"
    project_root = script_path.parent.parent
    expected_dir = project_root / "output" / "plots"
    
    assert expected_dir.exists(), f"Directory {expected_dir} was not created."
    assert expected_dir.is_dir(), f"{expected_dir} exists but is not a directory."