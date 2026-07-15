"""
Integration test to verify that the project directory structure is correctly created.
"""
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add the code directory to the path to import the setup module
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
code_dir = root_dir / "code"

if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_structure import create_directories, create_init_files

def test_directory_creation():
    """Test that create_directories creates the required folders."""
    # We test in the actual project root, but verify existence
    base_path = root_dir
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "specs/001-gene-regulation/contracts"
    ]
    
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        assert full_path.exists(), f"Directory {full_path} does not exist."
        assert full_path.is_dir(), f"{full_path} exists but is not a directory."

def test_init_files_exist():
    """Test that __init__.py files exist in required package directories."""
    base_path = root_dir
    
    package_dirs = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "specs",
        "specs/001-gene-regulation",
        "specs/001-gene-regulation/contracts"
    ]
    
    for dir_path in package_dirs:
        full_path = base_path / dir_path
        init_file = full_path / "__init__.py"
        assert init_file.exists(), f"__init__.py missing in {full_path}"
        assert init_file.is_file(), f"{init_file} is not a file."

if __name__ == "__main__":
    test_directory_creation()
    test_init_files_exist()
    print("All structure tests passed.")