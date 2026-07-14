"""
Contract test to ensure the project structure adheres to the specification.
This test checks the existence and permissions of the required directories.
"""
import os
import pytest
from pathlib import Path

def test_required_directories_exist():
    """
    Verify that the required project directories exist.
    This assumes the test is run from the project root or the script has been run.
    """
    # Determine the expected path relative to the current working directory
    # or the location where the project was initialized.
    # In a CI/CD context, this might need to be parameterized.
    # For now, we assume the project is in the expected location relative to cwd.
    
    project_name = "PROJ-550-exploring-the-convergence-of-iterated-fu"
    base_path = Path.cwd() / "projects" / project_name
    
    if not base_path.exists():
        pytest.skip(f"Project base path {base_path} does not exist. Run initialization first.")
    
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
        assert dir_path.exists(), f"Required directory {dir_path} does not exist"
        assert dir_path.is_dir(), f"{dir_path} is not a directory"
        
        # Check write permissions if applicable (optional but good practice)
        if dir_name.startswith("data") or dir_name.startswith("tests"):
            # Ensure we can write (create a temp file)
            test_file = dir_path / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
            except PermissionError:
                pytest.fail(f"Write permission denied for {dir_path}")