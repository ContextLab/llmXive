import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path if running as script, though pytest usually handles this
# Assuming this test is run from project root or sys.path includes it
try:
    from code.setup_structure import create_directories, create_init_files
except ImportError:
    # Fallback for direct execution or different path setup
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from code.setup_structure import create_directories, create_init_files


def test_directory_creation(tmp_path):
    """
    Test that create_directories creates the expected folder structure.
    We run this in a temporary directory to avoid polluting the real project tree during testing.
    """
    # Save current directory
    original_cwd = os.getcwd()
    
    try:
        # Change to temp directory
        os.chdir(tmp_path)
        
        # Call the function
        create_directories()
        
        # Verify directories exist
        expected_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "tests/unit",
            "tests/integration",
            "tests/contract",
            "specs/001-gene-regulation/contracts"
        ]
        
        for dir_name in expected_dirs:
            full_path = tmp_path / dir_name
            assert full_path.exists(), f"Directory {dir_name} was not created"
            assert full_path.is_dir(), f"{dir_name} is not a directory"
            
    finally:
        # Restore original directory
        os.chdir(original_cwd)

def test_init_file_creation(tmp_path):
    """
    Test that create_init_files creates __init__.py in package directories.
    """
    original_cwd = os.getcwd()
    
    try:
        os.chdir(tmp_path)
        
        # First create the directories
        create_directories()
        
        # Then create init files
        create_init_files()
        
        # Expected directories for __init__.py
        init_dirs = [
            "tests/unit",
            "tests/integration",
            "tests/contract",
            "code"
        ]
        
        for dir_name in init_dirs:
            full_path = tmp_path / dir_name / "__init__.py"
            assert full_path.exists(), f"__init__.py was not created in {dir_name}"
            assert full_path.is_file(), f"{dir_name}/__init__.py is not a file"
            
    finally:
        os.chdir(original_cwd)
