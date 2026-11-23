import pytest
from pathlib import Path
import os

def test_required_directories_exist():
    """
    Contract test: Verifies that the project directory structure required by T001
    exists at the expected relative paths.
    """
    # Determine the project root (parent of 'code' and 'tests' directories)
    # We assume this test is run from the project root or we find the root by looking
    # for the 'code' directory.
    current = Path(__file__).resolve()
    project_root = current.parent.parent.parent  # tests/contract -> tests -> root -> project_root? 
    # Actually, if this file is at tests/contract/test_directory_structure.py
    # Then parent is tests/contract, parent is tests, parent is root.
    
    # Let's find the root by looking for the 'code' directory upwards
    root = current
    while root != root.parent:
        if (root / "code").exists() and (root / "tests").exists():
            project_root = root
            break
        root = root.parent
    else:
        # Fallback: assume current working directory or parent of tests
        project_root = Path.cwd()
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "code/models",
        "code/analysis",
        "code/utils",
        "code/config",
        "tests/contract",
        "tests/unit",
        "tests/integration"
    ]
    
    missing = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing.append(dir_path)
        elif not full_path.is_dir():
            missing.append(f"{dir_path} (exists but is not a directory)")
    
    assert len(missing) == 0, f"Missing required directories: {missing}"