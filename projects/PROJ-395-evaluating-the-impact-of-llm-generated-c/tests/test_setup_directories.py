"""
Unit tests for the ``setup_directories`` script.

The tests verify that running the script creates the expected directory
structure. They are intentionally simple and avoid external dependencies.
"""

import shutil
from pathlib import Path
import subprocess
import sys

# Import the script module directly to test the ``create_directory`` helper
# without invoking the subprocess. This also ensures the function works
# correctly when imported.
from code.setup_directories import create_directory

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # repository root

def _clean_directories():
    """Remove any directories that may have been created by previous runs."""
    for sub in ["data", "state", "code"]:
        dir_path = PROJECT_ROOT / sub
        if dir_path.is_dir():
            shutil.rmtree(dir_path)

def test_create_directory_idempotent(tmp_path: Path):
    """Calling ``create_directory`` twice must not raise an error."""
    test_dir = tmp_path / "sample_dir"
    # First creation
    create_directory(test_dir)
    assert test_dir.is_dir()
    # Second creation (idempotent)
    create_directory(test_dir)
    assert test_dir.is_dir()

def test_main_creates_all_directories():
    """Running the script as a subprocess must create the required tree."""
    _clean_directories()
    # Execute the script via the interpreter to simulate CLI usage
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "code" / "setup_directories.py")],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    # Verify each expected directory exists
    for rel in ["data/raw", "data/processed", "state", "code"]:
        assert (PROJECT_ROOT / rel).is_dir(), f"Missing directory: {rel}"
    # Clean up after test
    _clean_directories()