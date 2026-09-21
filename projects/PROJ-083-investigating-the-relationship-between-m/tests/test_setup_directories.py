import os
import sys
from pathlib import Path
import pytest

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.setup_directories import setup_directories

def test_setup_directories_creates_structure(tmp_path):
    """
    Verify that setup_directories creates the required directory structure.
    We override the default behavior by temporarily changing the working directory
    or mocking the path logic if necessary, but for this test we assume the function
    runs relative to the project root.
    
    Since setup_directories uses __file__ to determine root, we test the logic
    by checking if the directories exist after running in the actual project context.
    """
    # This test assumes the script is run from the project root context
    # or that the function correctly identifies the root.
    # For a robust unit test, we might refactor to accept a root_path argument,
    # but for now we verify the side effect on the actual file system.
    
    # We run the setup (it's idempotent)
    result = setup_directories()
    
    assert result is True
    
    # Define expected directories relative to project root
    expected_dirs = [
        "data/raw",
        "data/processed",
        "data/models",
        "tests",
        "specs",
        "docs",
        "docs/reports",
        "contracts"
    ]
    
    for dir_name in expected_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_path} was not created."
        assert dir_path.is_dir(), f"{dir_path} exists but is not a directory."

def test_directories_are_writable():
    """
    Ensure that the created directories have write permissions (basic check).
    """
    result = setup_directories()
    assert result is True
    
    test_file_path = project_root / "data" / "raw" / ".gitkeep"
    # Just verify we can write a marker file if needed, though .gitkeep might already exist
    # This is a sanity check for permissions
    try:
        test_file_path.touch(exist_ok=True)
        assert test_file_path.exists()
    except PermissionError:
        pytest.fail(f"Cannot write to {project_root / 'data' / 'raw'}")
