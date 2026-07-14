import os
import pytest
from pathlib import Path
import shutil
import tempfile

# We need to import the function to test, but since it relies on cwd,
# we will test the logic by mocking or checking side effects in a temp dir.
# For simplicity in this unit test, we verify the directory creation logic.

def test_project_structure_creation(tmp_path):
    """
    Verify that the project structure is created correctly.
    We change to a temp directory to simulate the project root.
    """
    from initialize_project import main
    
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Run the initialization
        exit_code = main()
        
        assert exit_code == 0, "Initialization script should return 0"
        
        project_name = "PROJ-550-exploring-the-convergence-of-iterated-fu"
        base_path = tmp_path / "projects" / project_name
        
        assert base_path.exists(), "Base project directory should exist"
        
        required_dirs = [
            "code",
            "data/raw",
            "data/derived",
            "tests/unit",
            "tests/contract",
            "docs"
        ]
        
        for dir_name in required_dirs:
            dir_path = base_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} should exist"
            assert dir_path.is_dir(), f"{dir_name} should be a directory"
    
    finally:
        os.chdir(original_cwd)
