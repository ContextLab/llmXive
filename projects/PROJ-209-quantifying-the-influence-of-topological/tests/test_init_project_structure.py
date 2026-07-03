"""Test that the project initialization script creates the expected directories."""

import subprocess
import sys
from pathlib import Path

import pytest

# Path to the script relative to this test file
SCRIPT_PATH = Path(__file__).resolve().parents[1] / "code" / "init_project_structure.py"

# Expected directories relative to the repository root
EXPECTED_DIRS = [
    "src",
    "data/raw",
    "data/processed",
    "scripts",
    "tests",
    "notebooks",
    "data/validation",
    "code",
]

def repo_root() -> Path:
    """Return the repository root (parent of the tests directory)."""
    return Path(__file__).resolve().parents[1]

@pytest.mark.parametrize("dir_rel", EXPECTED_DIRS)
def test_directory_created(dir_rel: str):
    """Run the init script and verify each directory exists."""
    # Run the initialization script
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Check that the directory now exists
    target = repo_root() / dir_rel
    assert target.is_dir(), f"Expected directory {target} to exist"