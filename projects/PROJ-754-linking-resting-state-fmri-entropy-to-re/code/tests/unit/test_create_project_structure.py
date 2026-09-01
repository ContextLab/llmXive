"""
Unit tests for the create_project_structure script.
Validates that the directory creation logic works correctly.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path so we can import the script logic
# We import the functions directly from the module if it were a module,
# but since it's a script, we might need to execute or mock.
# For this test, we will test the logic by importing the functions
# if we refactor slightly, or by testing the side effects.
# To keep it simple and testable, we will import the functions
# assuming the script is importable (it has a main guard).

# We need to add the parent of 'scripts' to sys.path to import
# But the script is in code/scripts. The root is code/.
# Let's adjust the import path dynamically for the test.
script_path = Path(__file__).parent.parent.parent / "scripts"
if str(script_path) not in sys.path:
    sys.path.insert(0, str(script_path))

from create_project_structure import get_project_root, ensure_directory

def test_ensure_directory_creates_new(tmp_path):
    """Test that ensure_directory creates a new directory."""
    new_dir = tmp_path / "new_dir" / "sub_dir"
    assert not new_dir.exists()
    result = ensure_directory(new_dir)
    assert result is True
    assert new_dir.exists()
    assert new_dir.is_dir()

def test_ensure_directory_existing(tmp_path):
    """Test that ensure_directory returns True for existing directory."""
    existing_dir = tmp_path / "existing"
    existing_dir.mkdir()
    result = ensure_directory(existing_dir)
    assert result is True
    assert existing_dir.exists()

def test_get_project_root_fallback():
    """
    Test get_project_root logic.
    Since we are running in a test environment, we can't guarantee
    the .git structure matches the real repo, but we can test the logic
    by checking if it returns a Path object.
    """
    root = get_project_root()
    assert isinstance(root, Path)
    assert root.exists()

def test_directory_creation_logic():
    """
    Test the logic of creating a specific set of directories.
    We simulate the logic from main() in a temporary directory.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        
        # Simulate the directories T001 asks for
        dirs_to_create = [
            "src", "tests", "data", "reports", "docs", "scripts", "state",
            "src/data", "src/analysis", "src/stats", "src/config", "src/utils", "src/entities",
            "tests/unit", "tests/integration"
        ]
        
        for d in dirs_to_create:
            target = root / d
            ensure_directory(target)
            assert target.exists(), f"Directory {target} was not created."
            assert target.is_dir(), f"{target} is not a directory."

        # Verify structure
        assert (root / "src").exists()
        assert (root / "src" / "data").exists()
        assert (root / "tests" / "unit").exists()
        assert (root / "state").exists()
        assert (root / "data").exists()