import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the project root to the path so we can import from code/
# Assuming tests are run from the project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects" / "PROJ-312-evaluating-the-impact-of-code-generation" / "code"))

from create_directories import main

def test_directory_structure_creation(tmp_path):
    """Test that the main function creates the required directory structure."""
    # Change to a temporary directory to simulate a fresh project setup
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Define the expected project root path
        project_root = tmp_path / "projects" / "PROJ-312-evaluating-the-impact-of-code-generation"
        
        # Run the main function
        result = main()
        
        # Verify the return code
        assert result == 0, "main() should return 0 on success"
        
        # Verify the project root exists
        assert project_root.exists(), "Project root directory should exist"
        assert project_root.is_dir(), "Project root should be a directory"
        
        # Define expected directories (relative to project root)
        expected_dirs = [
            "code",
            "data",
            "tests",
            "contracts",
            "artifacts",
            "state",
            "data/raw",
            "data/processed",
            "data/spot_check",
            "tests/unit",
            "tests/contract",
        ]
        
        # Check each expected directory
        for dir_name in expected_dirs:
            dir_path = project_root / dir_name
            assert dir_path.exists(), f"Directory {dir_path} should exist"
            assert dir_path.is_dir(), f"{dir_path} should be a directory"
            
    finally:
        # Restore original working directory
        os.chdir(original_cwd)

def test_idempotency(tmp_path):
    """Test that running main() twice does not cause errors."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Run main() twice
        result1 = main()
        result2 = main()
        
        assert result1 == 0
        assert result2 == 0
        
        # Verify directories still exist
        project_root = tmp_path / "projects" / "PROJ-312-evaluating-the-impact-of-code-generation"
        assert project_root.exists()
        
    finally:
        os.chdir(original_cwd)