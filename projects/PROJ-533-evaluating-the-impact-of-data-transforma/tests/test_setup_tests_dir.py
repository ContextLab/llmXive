import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the parent directory to the path to import the module
sys_path_backup = __import__('sys').path.copy()
try:
    __import__('sys').path.insert(0, str(Path(__file__).parent.parent / "code"))
    from setup_tests_dir import main
finally:
    __import__('sys').path = sys_path_backup


def test_create_tests_directory(tmp_path):
    """
    Test that the setup script creates the tests directory.
    We run the script in a temporary directory to avoid modifying the actual project structure.
    """
    # Create a temporary directory structure to simulate project root
    # The script looks for 'tests' relative to the script's parent's parent.
    # We will run the script from a temp location.
    
    original_cwd = os.getcwd()
    try:
        # Create a temp project structure
        temp_project = tmp_path / "fake_project"
        temp_code = temp_project / "code"
        temp_code.mkdir(parents=True)
        
        # Copy the script to the temp code directory
        script_path = Path(__file__).parent.parent / "code" / "setup_tests_dir.py"
        if script_path.exists():
            shutil.copy(script_path, temp_code / "setup_tests_dir.py")
        
        # Change to the temp code directory to run the script
        os.chdir(temp_code)
        
        # Run the main function
        exit_code = main()
        
        # Verify exit code
        assert exit_code == 0, "Script should exit with 0 on success"
        
        # Verify directory exists
        assert (temp_project / "tests").is_dir(), "tests directory should exist"
        
    finally:
        os.chdir(original_cwd)

def test_directory_already_exists(tmp_path):
    """
    Test that the script handles the case where the directory already exists.
    """
    original_cwd = os.getcwd()
    try:
        temp_project = tmp_path / "fake_project_2"
        temp_code = temp_project / "code"
        temp_code.mkdir(parents=True)
        
        # Create the tests directory beforehand
        (temp_project / "tests").mkdir()
        
        # Copy script
        script_path = Path(__file__).parent.parent / "code" / "setup_tests_dir.py"
        if script_path.exists():
            shutil.copy(script_path, temp_code / "setup_tests_dir.py")
        
        os.chdir(temp_code)
        
        exit_code = main()
        
        assert exit_code == 0, "Script should exit with 0 even if directory exists"
        assert (temp_project / "tests").is_dir(), "tests directory should still exist"
        
    finally:
        os.chdir(original_cwd)