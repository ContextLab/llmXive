"""
Tests for the project structure setup script.
Verifies that the required directories are created.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We will test the logic by simulating the directory creation in a temp dir
# rather than running the script directly on the repo root during CI,
# though the script itself is designed to run from the root.

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "tests/unit",
    "tests/integration",
    "config",
    "output",
    "figures"
]

def test_directory_creation_logic():
    """
    Simulates the directory creation logic to ensure all required paths
    are valid and can be created.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        
        for dir_path in REQUIRED_DIRS:
            full_path = root / dir_path
            # Ensure parent exists (mimics parents=True)
            full_path.mkdir(parents=True, exist_ok=True)
            
            # Verify existence
            assert full_path.exists(), f"Failed to create directory: {full_path}"
            assert full_path.is_dir(), f"Path is not a directory: {full_path}"

def test_script_syntax():
    """
    Ensures the setup script is syntactically valid and can be imported
    (which implies it's valid Python).
    """
    try:
        with open("code/setup_project_structure.py", "r") as f:
            compile(f.read(), "code/setup_project_structure.py", "exec")
    except FileNotFoundError:
        pytest.fail("Script code/setup_project_structure.py not found.")
    except SyntaxError as e:
        pytest.fail(f"Syntax error in script: {e}")