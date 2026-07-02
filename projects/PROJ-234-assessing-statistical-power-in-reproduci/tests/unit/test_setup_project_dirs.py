"""
Unit tests for the project directory setup script.
Verifies that the expected directory structure is created.
"""
import os
import tempfile
import shutil
import pytest
import subprocess
import sys

# We need to run the script logic to test the side effects (directory creation)
# Since the script uses a hardcoded root, we will test the logic by importing
# the function logic or running the script in a temp environment if needed.
# However, for T001, the script is self-contained. We will test the outcome
# by running the script and checking the file system.

PROJECT_ROOT = "projects/PROJ-234-assessing-statistical-power-in-reproduci"

EXPECTED_DIRS = [
    os.path.join(PROJECT_ROOT, "code", "utils"),
    os.path.join(PROJECT_ROOT, "data", "raw"),
    os.path.join(PROJECT_ROOT, "data", "processed"),
    os.path.join(PROJECT_ROOT, "tests", "unit"),
    os.path.join(PROJECT_ROOT, "tests", "contract"),
    os.path.join(PROJECT_ROOT, "docs"),
    os.path.join(PROJECT_ROOT, "contracts"),
]

def test_project_directories_exist():
    """
    Run the setup script and verify all directories exist.
    """
    # Ensure we are running in a clean state relative to the project root
    # If the directories already exist, the script should still pass (exist_ok=True)
    
    # Run the script
    script_path = os.path.join("code", "setup_project_dirs.py")
    
    # Use subprocess to run the script as if it were a CLI tool
    # This ensures we test the actual execution flow
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check exit code
        assert result.returncode == 0, f"Script failed with output: {result.stdout} {result.stderr}"
        
        # Verify each directory
        for dir_path in EXPECTED_DIRS:
            assert os.path.isdir(dir_path), f"Directory {dir_path} does not exist after script execution"
            
    except FileNotFoundError:
        pytest.fail(f"Script not found at {script_path}. Ensure code/setup_project_dirs.py exists.")
    except Exception as e:
        pytest.fail(f"Unexpected error during test: {e}")

def test_directory_structure_correctness():
    """
    Additional check to ensure the hierarchy is correct (e.g., 'code' contains 'utils').
    """
    # Re-run or assume previous test ran. We check existence again.
    for dir_path in EXPECTED_DIRS:
        assert os.path.isdir(dir_path), f"Directory {dir_path} missing"
    
    # Specific check for hierarchy
    assert os.path.isdir("code"), "Root 'code' directory missing"
    assert os.path.isdir("data"), "Root 'data' directory missing"
    assert os.path.isdir("tests"), "Root 'tests' directory missing"
    assert os.path.isdir("docs"), "Root 'docs' directory missing"
    assert os.path.isdir("contracts"), "Root 'contracts' directory missing"
    
    # Check nested
    assert os.path.isdir(os.path.join("code", "utils")), "code/utils missing"
    assert os.path.isdir(os.path.join("data", "raw")), "data/raw missing"
    assert os.path.isdir(os.path.join("data", "processed")), "data/processed missing"
    assert os.path.isdir(os.path.join("tests", "unit")), "tests/unit missing"
    assert os.path.isdir(os.path.join("tests", "contract")), "tests/contract missing"