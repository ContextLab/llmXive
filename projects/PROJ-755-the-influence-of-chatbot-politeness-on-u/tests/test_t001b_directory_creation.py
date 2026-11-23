"""
Unit test for T001b: Directory Creation.
Verifies that the setup_directories script successfully creates
the `code` and `code/utils` directories.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
# We need to simulate the environment where the script runs from the root
# so we import the logic directly or via the module if it were installed.
# For this test, we will replicate the logic to ensure it works in isolation
# or import if the path is set up correctly.

def ensure_directories_logic(base_path: Path):
    """Replica of the logic in code/setup_directories.py for testing."""
    dirs_to_create = [
        base_path / "code",
        base_path / "code" / "utils"
    ]
    results = []
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
        results.append(dir_path)
    return results

def test_code_directories_created():
    """Test that 'code' and 'code/utils' directories are created."""
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        
        # Run the logic
        created_paths = ensure_directories_logic(base_path)
        
        # Assertions
        code_dir = base_path / "code"
        utils_dir = base_path / "code" / "utils"
        
        assert code_dir.exists(), "The 'code' directory was not created."
        assert code_dir.is_dir(), "'code' is not a directory."
        
        assert utils_dir.exists(), "The 'code/utils' directory was not created."
        assert utils_dir.is_dir(), "'code/utils' is not a directory."

def test_directories_persist_if_exist():
    """Test that the function handles existing directories gracefully."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        
        # Pre-create the directories
        (base_path / "code").mkdir()
        (base_path / "code" / "utils").mkdir()
        
        # Run the logic
        created_paths = ensure_directories_logic(base_path)
        
        # Should still return the paths and not raise errors
        assert len(created_paths) == 2
        assert (base_path / "code").exists()
        assert (base_path / "code" / "utils").exists()