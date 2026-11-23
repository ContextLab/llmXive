"""
Test to verify project structure is correctly initialized.
"""
import os
from pathlib import Path

def test_project_structure_exists():
    """Verify that the required project directories exist."""
    project_root = Path(__file__).parent.parent
    
    required_dirs = [
        project_root / "code",
        project_root / "data",
        project_root / "tests"
    ]
    
    for dir_path in required_dirs:
        assert dir_path.exists(), f"Directory {dir_path} does not exist"
        assert dir_path.is_dir(), f"{dir_path} is not a directory"

def test_init_files_exist():
    """Verify that __init__.py files exist in required modules."""
    project_root = Path(__file__).parent.parent
    
    init_files = [
        project_root / "code" / "__init__.py",
        project_root / "data" / "__init__.py",
        project_root / "tests" / "__init__.py"
    ]
    
    for file_path in init_files:
        assert file_path.exists(), f"File {file_path} does not exist"
        assert file_path.is_file(), f"{file_path} is not a file"
