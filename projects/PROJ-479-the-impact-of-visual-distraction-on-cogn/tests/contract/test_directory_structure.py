"""
Contract Test for Directory Structure (T004)
Verifies that the required data and results directories exist.
"""
import os
import pytest
import sys

# Add the parent directory to the path to allow imports if needed
# though this test primarily checks filesystem state
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "results/statistics",
    "results/plots",
    "results/sensitivity",
    "results/methodology"
]

def get_project_root():
    """
    Determine the project root directory.
    Assumes the test is run from the repository root or the script is in tests/contract.
    """
    # Try to find the directory containing 'code' and 'data'
    current = os.path.dirname(os.path.abspath(__file__))
    while current != os.path.dirname(current):
        if os.path.isdir(os.path.join(current, "code")) and os.path.isdir(os.path.join(current, "data")):
            return current
        current = os.path.dirname(current)
    # Fallback: assume current working directory is root if not found
    return os.getcwd()

@pytest.mark.parametrize("dir_path", REQUIRED_DIRS)
def test_directory_exists(dir_path):
    """
    Contract test: Verify that each required directory exists.
    """
    root = get_project_root()
    full_path = os.path.join(root, dir_path)
    
    assert os.path.exists(full_path), f"Required directory does not exist: {full_path}"
    assert os.path.isdir(full_path), f"Path exists but is not a directory: {full_path}"

def test_directory_structure_completeness():
    """
    Contract test: Verify the full set of required directories is present.
    """
    root = get_project_root()
    missing = []
    for dir_path in REQUIRED_DIRS:
        if not os.path.isdir(os.path.join(root, dir_path)):
            missing.append(dir_path)
    
    assert len(missing) == 0, f"Missing required directories: {missing}"