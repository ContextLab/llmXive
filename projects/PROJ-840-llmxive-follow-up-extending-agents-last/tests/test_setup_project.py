import os
import pytest
from pathlib import Path
from code.setup_project import create_directory_structure

def test_create_directory_structure():
    """
    Verify that create_directory_structure creates the required folders.
    """
    base_dir = Path.cwd()
    expected_dirs = ["code", "tests", "data", "docs"]
    
    # Run the function
    created = create_directory_structure()
    
    # Verify each expected directory exists
    for dir_name in expected_dirs:
        dir_path = base_dir / dir_name
        assert dir_path.exists(), f"Directory {dir_name} was not created"
        assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"
    
    # Verify the return list contains the created paths
    assert len(created) == 4
    for path_str in created:
        path = Path(path_str)
        assert path.exists()

def test_idempotency():
    """
    Verify that running the function multiple times does not raise errors.
    """
    # Run twice
    create_directory_structure()
    create_directory_structure()
    
    base_dir = Path.cwd()
    assert (base_dir / "code").exists()
    assert (base_dir / "tests").exists()
    assert (base_dir / "data").exists()
    assert (base_dir / "docs").exists()
